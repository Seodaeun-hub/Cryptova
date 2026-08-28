import os

import requests


AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8001")


def request_latest_ai_signal():
    response = requests.post(
        f"{AI_SERVER_URL}/predict/latest",
        timeout=180,
    )

    response.raise_for_status()
    return response.json()
