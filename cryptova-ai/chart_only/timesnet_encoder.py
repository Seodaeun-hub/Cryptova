#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clean TimesNet Encoder + Chart-only Classifier

Input:
- X_chart: [B, 72, 12]

Task:
- SHORT / HOLD / LONG classification

Label mapping:
- 0 = SHORT
- 1 = HOLD
- 2 = LONG
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ======================================================
# FFT-based period detection
# ======================================================
def FFT_for_Period(x, k=3):
    """
    Args:
        x: [B, T, C]
        k: number of dominant periods

    Returns:
        periods: list[int]
        period_weight: [B, k]
    """
    if x.dim() != 3:
        raise ValueError(f"x는 [B, T, C] 형태여야 합니다. 현재 shape: {x.shape}")

    B, T, C = x.shape

    # [B, freq, C]
    xf = torch.fft.rfft(x, dim=1)

    # [freq]
    freq_amp = xf.abs().mean(0).mean(-1)
    freq_amp = freq_amp.clone()

    # DC component 제거
    freq_amp[0] = 0

    freq_len = freq_amp.numel()
    k = min(k, freq_len)

    if k <= 0:
        raise ValueError("top_k가 유효하지 않습니다.")

    _, top_idx = torch.topk(freq_amp, k)
    top_idx_cpu = top_idx.detach().cpu().tolist()

    periods = []

    for idx in top_idx_cpu:
        idx = max(1, int(idx))
        period = max(1, T // idx)
        periods.append(period)

    # [B, freq]
    amp_per_freq = xf.abs().mean(-1)

    # [B, k]
    period_weight = amp_per_freq[:, top_idx]

    return periods, period_weight


# ======================================================
# Inception Block V1
# ======================================================
class Inception_Block_V1(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, num_kernels: int = 6):
        super().__init__()

        self.kernels = nn.ModuleList([
            nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=2 * i + 1,
                padding=i,
            )
            for i in range(num_kernels)
        ])

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

    def forward(self, x):
        """
        Args:
            x: [B, C, H, W]

        Returns:
            out: [B, out_channels, H, W]
        """
        outputs = [kernel(x) for kernel in self.kernels]
        out = torch.stack(outputs, dim=-1).mean(dim=-1)

        return out


# ======================================================
# TimesBlock
# ======================================================
class TimesBlock(nn.Module):
    def __init__(
        self,
        hidden_size: int,
        top_k: int = 3,
        conv_hidden_size: int = 128,
        num_kernels: int = 6,
        dropout: float = 0.25,
    ):
        super().__init__()

        self.top_k = top_k
        self.dropout = nn.Dropout(dropout)

        self.conv = nn.Sequential(
            Inception_Block_V1(
                in_channels=hidden_size,
                out_channels=conv_hidden_size,
                num_kernels=num_kernels,
            ),
            nn.GELU(),
            nn.Dropout(dropout),
            Inception_Block_V1(
                in_channels=conv_hidden_size,
                out_channels=hidden_size,
                num_kernels=num_kernels,
            ),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        """
        Args:
            x: [B, T, H]

        Returns:
            out: [B, T, H]

        주의:
        - 이 block은 residual을 내부에서 더하지 않음.
        - Encoder에서 x = x + block(norm(x)) 형태로 residual 처리.
        """
        if x.dim() != 3:
            raise ValueError(f"x는 [B, T, H] 형태여야 합니다. 현재 shape: {x.shape}")

        B, T, H = x.size()

        periods, period_weight = FFT_for_Period(x, self.top_k)

        if len(periods) == 0:
            raise ValueError("감지된 period가 없습니다.")

        outputs = []

        for period in periods:
            if period <= 0:
                raise ValueError(f"period는 1 이상이어야 합니다. 현재 period={period}")

            if T % period != 0:
                padded_len = ((T // period) + 1) * period

                pad = torch.zeros(
                    (B, padded_len - T, H),
                    device=x.device,
                    dtype=x.dtype,
                )

                out = torch.cat([x, pad], dim=1)
            else:
                padded_len = T
                out = x

            # [B, padded_len, H]
            # -> [B, padded_len // period, period, H]
            # -> [B, H, padded_len // period, period]
            out = out.reshape(B, padded_len // period, period, H)
            out = out.permute(0, 3, 1, 2).contiguous()

            out = self.conv(out)

            # [B, H, padded_len // period, period]
            # -> [B, padded_len, H]
            out = out.permute(0, 2, 3, 1).contiguous()
            out = out.reshape(B, padded_len, H)

            outputs.append(out[:, :T, :])

        # [B, T, H, k]
        outputs = torch.stack(outputs, dim=-1)

        if period_weight.shape[1] != outputs.shape[-1]:
            raise ValueError(
                f"period_weight와 outputs의 k 차원이 다릅니다: "
                f"{period_weight.shape[1]} != {outputs.shape[-1]}"
            )

        # [B, k] -> [B, 1, 1, k]
        period_weight = F.softmax(period_weight, dim=1)
        period_weight = period_weight.unsqueeze(1).unsqueeze(1)

        out = torch.sum(outputs * period_weight, dim=-1)

        return self.dropout(out)


# ======================================================
# Data Embedding
# ======================================================
class DataEmbedding(nn.Module):
    def __init__(
        self,
        input_size: int,
        input_dim: int,
        exog_input_size: int,
        hidden_size: int,
        dropout: float = 0.25,
    ):
        super().__init__()

        self.input_size = input_size
        self.input_dim = input_dim
        self.exog_input_size = exog_input_size
        self.hidden_size = hidden_size

        self.value_embedding = nn.Linear(input_dim, hidden_size)

        if exog_input_size > 0:
            self.exog_embedding = nn.Linear(exog_input_size, hidden_size)
        else:
            self.exog_embedding = None

        self.pos_embedding = nn.Parameter(
            torch.zeros(1, input_size, hidden_size)
        )

        self.dropout = nn.Dropout(dropout)

        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.pos_embedding, mean=0.0, std=0.02)

    def forward(self, x, exog=None):
        """
        Args:
            x: [B, T, F]
            exog: [B, T, E] or None

        Returns:
            out: [B, T, H]
        """
        if x.dim() != 3:
            raise ValueError(f"x는 [B, T, F] 형태여야 합니다. 현재 shape: {x.shape}")

        B, T, F_dim = x.shape

        if T != self.input_size:
            raise ValueError(f"입력 길이 불일치: expected {self.input_size}, got {T}")

        if F_dim != self.input_dim:
            raise ValueError(f"feature dim 불일치: expected {self.input_dim}, got {F_dim}")

        x = self.value_embedding(x)

        if exog is not None:
            if self.exog_embedding is None:
                raise ValueError("exog가 입력되었지만 exog_embedding이 없습니다.")

            if exog.dim() != 3:
                raise ValueError(
                    f"exog는 [B, T, E] 형태여야 합니다. 현재 shape: {exog.shape}"
                )

            if exog.shape[0] != B or exog.shape[1] != T:
                raise ValueError(
                    f"exog의 B/T 차원이 chart 입력과 다릅니다. "
                    f"chart={x.shape}, exog={exog.shape}"
                )

            if exog.shape[2] != self.exog_input_size:
                raise ValueError(
                    f"exog feature dim 불일치: "
                    f"expected {self.exog_input_size}, got {exog.shape[2]}"
                )

            x = x + self.exog_embedding(exog)

        x = x + self.pos_embedding[:, :T, :]

        return self.dropout(x)


# ======================================================
# TimesNet Encoder
# ======================================================
class TimesNetEncoder(nn.Module):
    def __init__(
        self,
        input_size: int,
        input_dim: int,
        h: int = 24,
        exog_size: int = 0,
        hidden_size: int = 64,
        dropout: float = 0.25,
        conv_hidden_size: int = 128,
        top_k: int = 3,
        num_kernels: int = 6,
        encoder_layers: int = 2,
        expand_to_future: bool = False,
        pre_norm: bool = True,
    ):
        super().__init__()

        self.input_size = input_size
        self.input_dim = input_dim
        self.h = h
        self.hidden_size = hidden_size
        self.expand_to_future = expand_to_future
        self.pre_norm = pre_norm

        self.embed = DataEmbedding(
            input_size=input_size,
            input_dim=input_dim,
            exog_input_size=exog_size,
            hidden_size=hidden_size,
            dropout=dropout,
        )

        if expand_to_future:
            self.predict_linear = nn.Linear(input_size, input_size + h)
        else:
            self.predict_linear = nn.Identity()

        self.layers = nn.ModuleList([
            TimesBlock(
                hidden_size=hidden_size,
                top_k=top_k,
                conv_hidden_size=conv_hidden_size,
                num_kernels=num_kernels,
                dropout=dropout,
            )
            for _ in range(encoder_layers)
        ])

        self.norms = nn.ModuleList([
            nn.LayerNorm(hidden_size)
            for _ in range(encoder_layers)
        ])

        self.final_norm = nn.LayerNorm(hidden_size)

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

    def forward(self, chart_window, exog_window=None):
        """
        Args:
            chart_window: [B, T, F]
            exog_window: [B, T, E] or None

        Returns:
            seq_emb: [B, T, H]
        """
        if chart_window.dim() != 3:
            raise ValueError(
                f"chart_window는 [B, T, F] 형태여야 합니다. "
                f"현재 shape: {chart_window.shape}"
            )

        B, T, F_dim = chart_window.shape

        if T != self.input_size:
            raise ValueError(f"입력 길이 불일치: expected {self.input_size}, got {T}")

        if F_dim != self.input_dim:
            raise ValueError(f"feature dim 불일치: expected {self.input_dim}, got {F_dim}")

        x = self.embed(chart_window, exog_window)

        # optional length expansion
        x = self.predict_linear(x.permute(0, 2, 1)).permute(0, 2, 1)

        for layer, norm in zip(self.layers, self.norms):
            if self.pre_norm:
                x = x + layer(norm(x))
            else:
                x = norm(x + layer(x))

        x = self.final_norm(x)

        return x[:, :self.input_size, :]


# ======================================================
# Chart-only TimesNet Classifier
# ======================================================
class ChartOnlyTimesNetClassifier(nn.Module):
    def __init__(
        self,
        input_size: int = 72,
        input_dim: int = 12,
        num_classes: int = 3,
        h: int = 24,
        hidden_size: int = 64,
        dropout: float = 0.25,
        conv_hidden_size: int = 128,
        top_k: int = 3,
        num_kernels: int = 6,
        encoder_layers: int = 2,
        expand_to_future: bool = False,
        pre_norm: bool = True,
    ):
        super().__init__()

        self.input_size = input_size
        self.input_dim = input_dim
        self.num_classes = num_classes

        self.encoder = TimesNetEncoder(
            input_size=input_size,
            input_dim=input_dim,
            h=h,
            hidden_size=hidden_size,
            dropout=dropout,
            conv_hidden_size=conv_hidden_size,
            top_k=top_k,
            num_kernels=num_kernels,
            encoder_layers=encoder_layers,
            expand_to_future=expand_to_future,
            pre_norm=pre_norm,
        )

        classifier_input_dim = hidden_size * 2

        self.classifier = nn.Sequential(
            nn.LayerNorm(classifier_input_dim),
            nn.Linear(classifier_input_dim, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),
        )

    def encode(self, chart_window):
        """
        Args:
            chart_window: [B, T, F]

        Returns:
            chart_embedding: [B, 2H]
        """
        seq_emb = self.encoder(chart_window)  # [B, T, H]

        mean_pool = seq_emb.mean(dim=1)
        last_pool = seq_emb[:, -1, :]

        chart_embedding = torch.cat([mean_pool, last_pool], dim=-1)

        return chart_embedding

    def forward(self, chart_window):
        """
        Args:
            chart_window: [B, 72, 12]

        Returns:
            logits: [B, 3]

        class order:
            0 = SHORT
            1 = HOLD
            2 = LONG
        """
        chart_embedding = self.encode(chart_window)
        logits = self.classifier(chart_embedding)

        return logits


# ======================================================
# quick shape test
# ======================================================
if __name__ == "__main__":
    model = ChartOnlyTimesNetClassifier(
        input_size=72,
        input_dim=12,
        num_classes=3,
    )

    dummy_x = torch.randn(4, 72, 12)
    logits = model(dummy_x)

    print("dummy input:", dummy_x.shape)
    print("logits:", logits.shape)

    assert logits.shape == (4, 3)

    print("✅ ChartOnlyTimesNetClassifier shape test passed")