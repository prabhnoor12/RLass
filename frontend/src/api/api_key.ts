// API utility for api_key endpoints matching backend/api/api_key.py

export async function issueApiKey(userId: string) {
  const response = await fetch(`/api/api_key/issue/${userId}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to issue API key');
  return response.json();
}

export async function revokeApiKey(key: string) {
  const response = await fetch(`/api/api_key/revoke/${key}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to revoke API key');
  return response.json();
}

export async function listUserApiKeys(userId: string) {
  const response = await fetch(`/api/api_key/user/${userId}`);
  if (!response.ok) throw new Error('Failed to list user API keys');
  return response.json();
}

export async function getApiKeyDetails(key: string) {
  const response = await fetch(`/api/api_key/details/${key}`);
  if (!response.ok) throw new Error('Failed to get API key details');
  return response.json();
}

export async function validateApiKey(key: string, userId?: string) {
  const url = userId ? `/api/api_key/validate/${key}?user_id=${userId}` : `/api/api_key/validate/${key}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to validate API key');
  return response.json();
}

export async function reactivateApiKey(key: string) {
  const response = await fetch(`/api/api_key/reactivate/${key}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to reactivate API key');
  return response.json();
}

export async function countApiKeys(userId?: string, activeOnly: boolean = false) {
  let url = `/api/api_key/count?active_only=${activeOnly}`;
  if (userId) url += `&user_id=${userId}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to count API keys');
  return response.json();
}
