// API utility for maintenance endpoints matching backend/api/maintenance.py

export async function createMaintenanceTask(task: any) {
  const response = await fetch('/api/maintenance/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  });
  if (!response.ok) throw new Error('Failed to create maintenance task');
  return response.json();
}

export async function getMaintenanceTaskByName(name: string) {
  const response = await fetch(`/api/maintenance/get?name=${encodeURIComponent(name)}`);
  if (!response.ok) throw new Error('Failed to get maintenance task');
  return response.json();
}

export async function listMaintenanceTasks(isActive?: boolean) {
  let url = '/api/maintenance/list';
  if (isActive !== undefined) url += `?is_active=${isActive}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to list maintenance tasks');
  return response.json();
}

export async function updateMaintenanceTaskStatus(taskId: number, status: string) {
  const response = await fetch(`/api/maintenance/update-status/${taskId}?status=${encodeURIComponent(status)}`, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to update maintenance task status');
  return response.json();
}

export async function runMaintenanceTask(taskId: number) {
  const response = await fetch(`/api/maintenance/run/${taskId}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to run maintenance task');
  return response.json();
}

export async function deactivateMaintenanceTask(taskId: number) {
  const response = await fetch(`/api/maintenance/deactivate/${taskId}`, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to deactivate maintenance task');
  return response.json();
}
