import { API_BASE_URL } from "./config";

function getAuthToken() {
  return localStorage.getItem("access_token");
}

export async function getExchangeBalance() {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/exchange/balance`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch exchange balance.");
  }

  return data;
}
