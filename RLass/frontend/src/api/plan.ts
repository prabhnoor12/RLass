// API utility for plan endpoints matching backend/api/plan.py

export async function createPlan(plan: any) {
  const response = await fetch('/api/plan/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan),
  });
  if (!response.ok) throw new Error('Failed to create plan');
  return response.json();
}

export async function getPlanByName(name: string) {
  const response = await fetch(`/api/plan/get?name=${encodeURIComponent(name)}`);
  if (!response.ok) throw new Error('Failed to get plan');
  return response.json();
}

export async function listPlans() {
  const response = await fetch('/api/plan/list');
  if (!response.ok) throw new Error('Failed to list plans');
  return response.json();
}

export async function activatePlan(planId: number) {
  const response = await fetch(`/api/plan/activate/${planId}`, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to activate plan');
  return response.json();
}

export async function deactivatePlan(planId: number) {
  const response = await fetch(`/api/plan/deactivate/${planId}`, {
    method: 'PUT',
  });
  if (!response.ok) throw new Error('Failed to deactivate plan');
  return response.json();
}
