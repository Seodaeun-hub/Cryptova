import { API_BASE_URL } from "./config";

function getAuthToken() {
  return localStorage.getItem("access_token");
}

export async function runBacktest(settings) {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/backtest/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(settings),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to run backtest.");
  }

  return data;
}

export async function getBacktestResults() {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/backtest/results`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load backtest results.");
  }

  return data;
}

export async function getBacktestResultDetail(resultId) {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/backtest/results/${resultId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load backtest result detail.");
  }

  return data;
}
