// API utility for authorization endpoints matching backend/api/authorization.py

export async function createRole(role: any) {
  const response = await fetch('/api/authorization/role/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(role),
  });
  if (!response.ok) throw new Error('Failed to create role');
  return response.json();
}

export async function getRoleByName(name: string) {
  const response = await fetch(`/api/authorization/role/get?name=${encodeURIComponent(name)}`);
  if (!response.ok) throw new Error('Failed to get role');
  return response.json();
}

export async function listRoles() {
  const response = await fetch('/api/authorization/role/list');
  if (!response.ok) throw new Error('Failed to list roles');
  return response.json();
}

export async function assignRoleToUser(userRole: any) {
  const response = await fetch('/api/authorization/user-role/assign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userRole),
  });
  if (!response.ok) throw new Error('Failed to assign role to user');
  return response.json();
}

export async function getRolesForUser(userId: number) {
  const response = await fetch(`/api/authorization/user-role/list/${userId}`);
  if (!response.ok) throw new Error('Failed to get roles for user');
  return response.json();
}

export async function userHasRole(userId: number, roleName: string) {
  const response = await fetch(`/api/authorization/user-role/has-role?user_id=${userId}&role_name=${encodeURIComponent(roleName)}`);
  if (!response.ok) throw new Error('Failed to check user role');
  return response.json();
}

export async function removeRoleFromUser(userId: number, roleId: number) {
  const response = await fetch(`/api/authorization/user-role/remove?user_id=${userId}&role_id=${roleId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to remove role from user');
  return response.json();
}
