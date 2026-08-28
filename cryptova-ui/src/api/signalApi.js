import { API_BASE_URL } from "./config";

function getAuthToken() {
  return localStorage.getItem("access_token");
}

export async function createMockSignal() {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/signals/mock`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to create mock signal.");
  }

  return data;
}

export async function getSignals() {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/signals`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load signals.");
  }

  return data;
}

export async function getSignalDetail(signalId) {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/signals/${signalId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load signal detail.");
  }

  return data;
}
export async function generateSignal() {
  const token = getAuthToken();

  if (!token) {
    throw new Error("Login is required.");
  }

  const response = await fetch(`${API_BASE_URL}/signals/generate`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to generate signal.");
  }

  return data;
}
