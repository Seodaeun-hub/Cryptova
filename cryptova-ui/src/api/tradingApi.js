import { API_BASE_URL } from "./config";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(url, options = {}) {
  const token = getToken();

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || `Trading API 요청 실패: ${response.status}`
    );
  }

  return response.json();
}

export async function getTradingMarkers({
  symbol = "BTCUSDT",
  limit = 100,
} = {}) {
  return request(`/trading/markers?symbol=${symbol}&limit=${limit}`);
}

export async function getOpenPositionPnl({ symbol = "BTCUSDT" } = {}) {
  return request(`/positions/open/pnl?symbol=${symbol}`);
}

export async function getTradingRuns({ limit = 20 } = {}) {
  return request(`/trading/runs?limit=${limit}`);
}

export async function startAutoTrading() {
  return request("/trading/start", {
    method: "POST",
  });
}

export async function stopAutoTrading() {
  return request("/trading/stop", {
    method: "POST",
  });
}

export async function getAutoTradingStatus() {
  return request("/trading/status");
}

export async function runTradingOnce() {
  const token = localStorage.getItem("access_token");

  const response = await fetch(`${API_BASE_URL}/trading/run-once`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      symbol: "BTCUSDT",
      dry_run: true,
    }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    console.error("runTradingOnce error:", data);
    throw new Error(data?.detail || "Failed to run trading once.");
  }

  return data;
}
export async function getPaperPortfolioSummary(symbol = "BTCUSDT") {
  const token = localStorage.getItem("access_token");

  const response = await fetch(
    `${API_BASE_URL}/positions/paper-portfolio?symbol=${symbol}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || "Failed to load paper portfolio summary."
    );
  }

  return response.json();
}
