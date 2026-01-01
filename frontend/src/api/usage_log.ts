// API utility for usage_log endpoints matching backend/api/usage_log.py

export async function logUsageEvent(apiKey: string, endpoint: string | null, identifier: string, status: string) {
  const url = '/api/usage_log/log';
  const params = new URLSearchParams({ api_key: apiKey, identifier, status });
  if (endpoint) params.append('endpoint', endpoint);
  const response = await fetch(`${url}?${params.toString()}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to log usage event');
  return response.json();
}

export async function getUsageEvents(query: { api_key?: string; endpoint?: string; identifier?: string; from_time?: string; to_time?: string }) {
  const params = new URLSearchParams();
  if (query.api_key) params.append('api_key', query.api_key);
  if (query.endpoint) params.append('endpoint', query.endpoint);
  if (query.identifier) params.append('identifier', query.identifier);
  if (query.from_time) params.append('from_time', query.from_time);
  if (query.to_time) params.append('to_time', query.to_time);
  const response = await fetch(`/api/usage_log/events?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to get usage events');
  return response.json();
}

export async function deleteUsageEvents(api_key?: string, identifier?: string, before?: string) {
  const params = new URLSearchParams();
  if (api_key) params.append('api_key', api_key);
  if (identifier) params.append('identifier', identifier);
  if (before) params.append('before', before);
  const response = await fetch(`/api/usage_log/events?${params.toString()}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete usage events');
  return response.json();
}

export async function countUsageEvents(api_key?: string, endpoint?: string, identifier?: string) {
  const params = new URLSearchParams();
  if (api_key) params.append('api_key', api_key);
  if (endpoint) params.append('endpoint', endpoint);
  if (identifier) params.append('identifier', identifier);
  const response = await fetch(`/api/usage_log/count?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to count usage events');
  return response.json();
}

export async function summarizeUsage(groupBy: string = 'endpoint', api_key?: string, identifier?: string) {
  const params = new URLSearchParams({ group_by: groupBy });
  if (api_key) params.append('api_key', api_key);
  if (identifier) params.append('identifier', identifier);
  const response = await fetch(`/api/usage_log/summary?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to summarize usage');
  return response.json();
}
