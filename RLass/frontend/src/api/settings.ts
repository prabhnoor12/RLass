// API utility for settings endpoints matching backend/api/settings.py

export async function createSettings(settings: any) {
  const response = await fetch('/api/settings/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!response.ok) throw new Error('Failed to create settings');
  return response.json();
}

export async function getSettingsForUser(userId: number) {
  const response = await fetch(`/api/settings/user/${userId}`);
  if (!response.ok) throw new Error('Failed to get settings for user');
  return response.json();
}

export async function updateSettingsValue(userId: number, key: string, value: string) {
  const url = `/api/settings/update?user_id=${userId}&key=${encodeURIComponent(key)}&value=${encodeURIComponent(value)}`;
  const response = await fetch(url, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to update settings value');
  return response.json();
}

export async function deleteSettings(userId: number, key: string) {
  const url = `/api/settings/delete?user_id=${userId}&key=${encodeURIComponent(key)}`;
  const response = await fetch(url, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete settings');
  return response.json();
}

export async function getSettingValue(userId: number, key: string) {
  const response = await fetch(`/api/settings/get?user_id=${userId}&key=${encodeURIComponent(key)}`);
  if (!response.ok) throw new Error('Failed to get setting value');
  return response.json();
}
