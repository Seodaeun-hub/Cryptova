#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import argparse
import random
import requests
import pandas as pd

from datetime import datetime, UTC, timedelta
from dateutil import parser as dparser
from tqdm import tqdm


BYBIT_BASE = os.getenv("BYBIT_BASE", "https://api.bybit.com")
DEFAULT_OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "chart_raw_latest_bybit.csv",
)


def iso_utc_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat()


def fetch_chunk(base, category, symbol, interval, start_ms, end_ms, limit=1000):
    url = f"{base}/v5/market/kline"

    params = {
        "category": category,
        "symbol": symbol,
        "interval": str(interval),
        "start": start_ms,
        "end": end_ms,
        "limit": limit,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.Timeout as e:
        print(f"[ERROR] Bybit kline request timeout: {e}", flush=True)
        return [], -1

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Bybit kline request failed: {e}", flush=True)
        return [], -1

    except Exception as e:
        print(f"[ERROR] Unexpected kline fetch error: {e}", flush=True)
        return [], -1

    ret_code = data.get("retCode", -2)

    if ret_code != 0:
        print(f"[ERROR] Bybit retCode={ret_code}, message={data.get('retMsg')}", flush=True)
        return [], ret_code

    data_list = data["result"].get("list", [])

    print(f"[DEBUG] fetched kline rows={len(data_list)}", flush=True)

    return data_list, 0


def fetch_funding_rate(base, symbol):
    url = f"{base}/v5/market/funding/history"

    params = {
        "category": "linear",
        "symbol": symbol,
        "limit": 200,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data.get("retCode") != 0:
        return pd.DataFrame()

    rows = []

    for item in data["result"]["list"]:
        rows.append({
            "funding_hour": iso_utc_from_ms(int(item["fundingRateTimestamp"])),
            "funding_rate": float(item["fundingRate"]),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["funding_hour"] = pd.to_datetime(df["funding_hour"], utc=True)
    return df


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--category", default="linear")
    ap.add_argument("--base", default=BYBIT_BASE)

    ap.add_argument(
        "--out",
        default=DEFAULT_OUTPUT_PATH,
    )

    ap.add_argument("--sleep-base", type=float, default=0.5)
    ap.add_argument("--max-backoff", type=float, default=20.0)
    ap.add_argument("--max-retries", type=int, default=3)

    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    now = datetime.now(UTC)
    start_dt = now - timedelta(hours=300)

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)

    cursor = start_ms
    rows = []

    total_minutes = (end_ms - start_ms) // (1000 * 60)
    total_candles = total_minutes // args.interval
    total_chunks = max((total_candles + 999) // 1000, 1)

    print("[Bybit Chart Fetch]")
    print(f"symbol   : {args.symbol}")
    print(f"category : {args.category}")
    print(f"interval : {args.interval}m")
    print(f"period   : {start_dt.isoformat()} → {now.isoformat()}")
    print(f"output   : {args.out}")

    pbar = tqdm(total=total_chunks, desc="Fetching chunks", ncols=100)
    backoff = 1.0

    retry_count = 0

    while cursor < end_ms:
        chunk_end = min(cursor + 1000 * args.interval * 60 * 1000, end_ms)

        print(
            f"[REQUEST] kline start={iso_utc_from_ms(cursor)} "
            f"end={iso_utc_from_ms(chunk_end)} "
            f"retry={retry_count}",
            flush=True,
        )

        data_list, ret_code = fetch_chunk(
            base=args.base,
            category=args.category,
            symbol=args.symbol,
            interval=args.interval,
            start_ms=cursor,
            end_ms=chunk_end,
        )

        if ret_code != 0 or not data_list:
            retry_count += 1

            if retry_count > args.max_retries:
                raise RuntimeError(
                    f"Bybit chart fetch failed after {args.max_retries} retries. "
                    f"ret_code={ret_code}, cursor={iso_utc_from_ms(cursor)}"
                )

            print(
                f"[RETRY] ret_code={ret_code}, empty={not data_list}, "
                f"sleep={backoff:.1f}s",
                flush=True,
            )

            time.sleep(backoff)
            backoff = min(backoff * 2.0, args.max_backoff)
            continue

        retry_count = 0
        backoff = 1.0
        data_list.sort(key=lambda x: int(x[0]))

        for item in data_list:
            ts, open_, high, low, close, volume, turnover = item[:7]

            rows.append({
                "ts": iso_utc_from_ms(int(ts)),
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
                "turnover": float(turnover),
                "symbol": args.symbol,
                "interval": str(args.interval),
                "category": args.category,
            })

        cursor = int(data_list[-1][0]) + args.interval * 60 * 1000
        pbar.set_postfix_str(f"last={rows[-1]['ts']}")
        pbar.update(1)

        time.sleep(args.sleep_base + random.random() * 0.2)

    pbar.close()

    if not rows:
        print("수집된 데이터가 없습니다.")
        return

    df = pd.DataFrame(rows)

    funding_df = fetch_funding_rate(args.base, args.symbol)

    if not funding_df.empty:
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        funding_df = funding_df.sort_values("funding_hour")

        df = pd.merge_asof(
            df.sort_values("ts"),
            funding_df,
            left_on="ts",
            right_on="funding_hour",
            direction="backward",
        )

        df["funding_rate"] = df["funding_rate"].ffill().fillna(0.0)
    else:
        df["funding_rate"] = 0.0

    df = df.drop_duplicates(subset=["ts"])
    df = df.sort_values("ts").reset_index(drop=True)

    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    diff = df["ts"].diff().dropna()
    irregular_count = int((diff != pd.Timedelta(hours=1)).sum())

    df.to_csv(args.out, index=False)

    print("\nBybit chart data saved")
    print(f"path  : {args.out}")
    print(f"rows  : {len(df)}")
    print(f"range : {df['ts'].iloc[0]} → {df['ts'].iloc[-1]}")
    print(f"irregular intervals: {irregular_count}")
    print("columns:", list(df.columns))


if __name__ == "__main__":
    main()
