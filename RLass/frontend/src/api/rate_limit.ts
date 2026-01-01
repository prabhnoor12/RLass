// API utility for rate_limit endpoints matching backend/api/rate_limit.py

export async function checkRateLimit(request: any) {
  const response = await fetch('/api/rate_limit/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error('Failed to check rate limit');
  return response.json();
}

export async function getUsageSummary(apiKey: string, endpoint?: string) {
  let url = `/api/rate_limit/usage/summary/${apiKey}`;
  if (endpoint) url += `?endpoint=${encodeURIComponent(endpoint)}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to get usage summary');
  return response.json();
}

export async function getRateLimitConfigs(apiKey: string) {
  const response = await fetch(`/api/rate_limit/rate-limit/config/${apiKey}`);
  if (!response.ok) throw new Error('Failed to get rate limit configs');
  return response.json();
}

export async function updateRateLimitConfig(apiKey: string, endpoint: string, limit: number, periodSeconds: number) {
  const url = `/api/rate_limit/rate-limit/config/${apiKey}?endpoint=${encodeURIComponent(endpoint)}&limit=${limit}&period_seconds=${periodSeconds}`;
  const response = await fetch(url, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to update rate limit config');
  return response.json();
}
