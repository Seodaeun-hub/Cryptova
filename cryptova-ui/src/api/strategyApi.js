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

    let message = `Strategy API 요청 실패: ${response.status}`;

    if (typeof errorData?.detail === "string") {
      message = errorData.detail;
    } else if (Array.isArray(errorData?.detail)) {
      message = errorData.detail
        .map((item) => {
          const loc = item.loc ? item.loc.join(".") : "field";
          return `${loc}: ${item.msg}`;
        })
        .join("\n");
    } else if (errorData?.detail) {
      message = JSON.stringify(errorData.detail, null, 2);
    }

    throw new Error(message);
  }

  return response.json();
}

export async function getStrategySettings() {
  return request("/strategy/settings");
}

export async function saveStrategySettings(data) {
  return request("/strategy/settings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
