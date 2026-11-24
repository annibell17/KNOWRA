export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string) ?? "http://127.0.0.1:8000";

export async function apiFetch(
  endpoint: string,
  init?: RequestInit
): Promise<Response> {
  const url = `${API_BASE_URL}${endpoint}`;
  return fetch(url, init);
}
