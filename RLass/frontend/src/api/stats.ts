// API utility for stats endpoints matching backend/api/stats.py

export async function listStats(userId?: number) {
  let url = '/api/stats/list';
  if (userId !== undefined) url += `?user_id=${userId}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to list stats');
  return response.json();
}

export async function getStats(userId: number, endpoint: string, period: string) {
  const url = `/api/stats/get?user_id=${userId}&endpoint=${encodeURIComponent(endpoint)}&period=${encodeURIComponent(period)}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to get stats');
  return response.json();
}

export async function incrementUserUsage(userId: number, endpoint: string, period: string) {
  const url = `/api/stats/increment?user_id=${userId}&endpoint=${encodeURIComponent(endpoint)}&period=${encodeURIComponent(period)}`;
  const response = await fetch(url, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to increment user usage');
  return response.json();
}
