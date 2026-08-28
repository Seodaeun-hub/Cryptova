#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fetch_latest_news.py

역할:
- 실시간 inference용 최신 MarketAux BTC 뉴스 수집
- 최근 96시간 뉴스만 가져옴
- historical chunk/progress 사용 안 함
- 결과는 매번 latest 파일로 overwrite 저장

api_key.txt 형식:
marketaux_api_key=여기에_키_값

출력:
data/news/raw/news_raw_latest_marketaux.csv
"""

import os
import time
import random
from pathlib import Path

import requests
import pandas as pd


# ============================================================
# 경로 설정
# 현재 파일 위치:
# cryptova-ai/data/news/raw/fetch_latest_news.py
# parents[3] = cryptova-ai
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]

API_KEY_PATH = PROJECT_ROOT / "api_key.txt"
RAW_OUT = PROJECT_ROOT / "data/news/raw/news_raw_latest_marketaux.csv"


SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "fetch-latest-marketaux-bitcoin-news/1.0 (+research use)"
})


def load_marketaux_api_key(path: Path = API_KEY_PATH) -> str:
    environment_key = os.getenv("MARKETAUX_API_KEY", "").strip()
    if environment_key:
        return environment_key

    if not path.exists():
        raise FileNotFoundError(
            f"API key 파일을 찾을 수 없습니다: {path}\n"
            "MARKETAUX_API_KEY 환경변수를 설정하거나 프로젝트 최상위 폴더에 "
            "api_key.txt를 만들고 marketaux_api_key=키값 형태로 저장하세요."
        )

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("marketaux_api_key="):
                key = line.split("=", 1)[1].strip()

                if not key:
                    raise ValueError("marketaux_api_key= 뒤에 API 키 값이 비어 있습니다.")

                return key

    raise ValueError(
        "api_key.txt 안에서 marketaux_api_key= 형식을 찾지 못했습니다.\n"
        "예: marketaux_api_key=여기에_키_값"
    )


def iso(dt: pd.Timestamp) -> str:
    d = pd.to_datetime(dt, utc=True)
    d = d.tz_convert(None)
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def clean_and_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
        df = df.dropna(subset=["published_at"])
        df = df.sort_values("published_at")

    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"], keep="first")
    elif {"title", "published_at"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["title", "published_at"], keep="first")
    else:
        df = df.drop_duplicates(keep="first")

    return df.reset_index(drop=True)


def save_csv_safely(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    df = clean_and_deduplicate(df)
    df.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"💾 저장 완료: {path}")
    print(f"   저장된 뉴스 개수: {len(df)}")

    if not df.empty and "published_at" in df.columns:
        print(f"   저장 범위: {df['published_at'].min()} ~ {df['published_at'].max()}")


def get_json(url: str, params: dict, tries: int = 3):
    last_status = None
    last_text = None

    for k in range(tries):
        try:
            response = SESSION.get(url, params=params, timeout=30)
            last_status = response.status_code
            last_text = response.text[:500]

            if response.status_code == 429:
                wait_sec = 2 * (k + 1) + random.random()
                print(f"[MarketAux] 429 rate limit 발생. {wait_sec:.1f}초 후 재시도...")
                time.sleep(wait_sec)
                continue

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"[MarketAux] HTTP 에러 발생 ({k + 1}/{tries}): {e}")

            if last_status is not None:
                print(f"[MarketAux] status={last_status}, body={last_text}")

            wait_sec = 2 * (k + 1) + random.random()
            time.sleep(wait_sec)

    if last_status == 429:
        print("[MarketAux] rate limit으로 인해 최신 뉴스 수집 실패")
        return "RATE_LIMIT"

    print("[MarketAux] 모든 재시도 실패")

    if last_status is not None:
        print(f"status={last_status}")
        print(f"body={last_text}")

    return {}


def fetch_latest_marketaux_news(
    token: str,
    lookback_hours: int = 96,
    query: str = "(bitcoin OR BTC)",
    language: str = "en",
    limit: int = 20,
    max_pages: int = 5,
    sleep: float = 0.5,
) -> pd.DataFrame:
    base_url = "https://api.marketaux.com/v1/news/all"

    end = pd.Timestamp.utcnow()
    if end.tzinfo is None:
        end = end.tz_localize("UTC")
    else:
        end = end.tz_convert("UTC")

    start = end - pd.Timedelta(hours=lookback_hours)

    print("🚀 최신 MarketAux BTC 뉴스 수집 시작")
    print(f"수집 범위: {start} ~ {end}")
    print(f"lookback_hours: {lookback_hours}")
    print(f"검색어: {query}")

    rows = []

    for page in range(1, max_pages + 1):
        params = {
            "api_token": token,
            "search": query,
            "language": language,
            "published_after": iso(start),
            "published_before": iso(end),
            "group_similar": "true",
            "limit": limit,
            "page": page,
        }

        js = get_json(base_url, params)

        if js == "RATE_LIMIT":
            break

        data = js.get("data", js.get("news", [])) if isinstance(js, dict) else []
        data = data or []

        if not data:
            print(f"page {page}: 데이터 없음")
            break

        print(f"page {page}: {len(data)}개 수집")

        for item in data:
            rows.append({
                "source": "marketaux",
                "title": item.get("title"),
                "summary": item.get("description") or item.get("snippet"),
                "url": item.get("url"),
                "published_at": item.get("published_at"),
                "origin": item.get("source"),
                "entities": item.get("entities"),
                "symbols": item.get("symbols"),
            })

        if len(data) < limit:
            break

        time.sleep(sleep)

    df = pd.DataFrame(rows)
    df = clean_and_deduplicate(df)

    return df


def main():
    token = load_marketaux_api_key(API_KEY_PATH)

    df = fetch_latest_marketaux_news(
        token=token,
        lookback_hours=96,
        query="(bitcoin OR BTC)",
        language="en",
        limit=20,
        max_pages=5,
        sleep=0.5,
    )

    save_csv_safely(df, RAW_OUT)

    print("\n✅ 최신 뉴스 수집 완료")
    print(f"최종 저장 파일: {RAW_OUT}")
    print(f"최종 뉴스 개수: {len(df)}")

    if not df.empty:
        print("\n미리보기:")
        preview_cols = [col for col in ["published_at", "title", "url"] if col in df.columns]
        print(df[preview_cols].tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
