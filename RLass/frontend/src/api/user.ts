// API utility for user endpoints matching backend/api/user.py

export async function createUser(user: any) {
  const response = await fetch('/api/user/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(user),
  });
  if (!response.ok) throw new Error('Failed to create user');
  return response.json();
}

export async function getUser(userId: string) {
  const response = await fetch(`/api/user/get/${userId}`);
  if (!response.ok) throw new Error('Failed to get user');
  return response.json();
}

export async function updateUser(userId: string, email?: string, password?: string, isActive?: boolean) {
  const params = new URLSearchParams();
  if (email) params.append('email', email);
  if (password) params.append('password', password);
  if (isActive !== undefined) params.append('is_active', String(isActive));
  const url = `/api/user/update/${userId}` + (params.toString() ? `?${params.toString()}` : '');
  const response = await fetch(url, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to update user');
  return response.json();
}
