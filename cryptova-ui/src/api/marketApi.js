import { API_BASE_URL } from "./config";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(url) {
  const token = getToken();

  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    throw new Error(
      errorData?.detail || `Market API 요청 실패: ${response.status}`
    );
  }

  return response.json();
}

export async function getCandles({
  symbol = "BTCUSDT",
  interval = "60",
  category = "linear",
  startDate = "2020-03-01",
  endDate = null,
  pageLimit = 1000,
} = {}) {
  const params = new URLSearchParams();

  params.set("symbol", symbol);
  params.set("interval", interval);
  params.set("category", category);
  params.set("start_date", startDate);
  params.set("page_limit", String(pageLimit));

  if (endDate) {
    params.set("end_date", endDate);
  }

  return request(`/market/candles?${params.toString()}`);
}
