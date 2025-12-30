// API utility for auth endpoints matching backend/api/auth.py

export async function issueAuthToken(tokenIn: any) {
	const response = await fetch('/api/auth/issue', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(tokenIn),
	});
	if (!response.ok) throw new Error('Failed to issue auth token');
	return response.json();
}

export async function validateAuthToken(token: string, checkExpiry: boolean = true) {
	const url = `/api/auth/validate/${token}?check_expiry=${checkExpiry}`;
	const response = await fetch(url);
	if (!response.ok) throw new Error('Invalid or expired auth token');
	return response.json();
}

export async function revokeAuthToken(token: string) {
	const response = await fetch(`/api/auth/revoke/${token}`, {
		method: 'POST',
	});
	if (!response.ok) throw new Error('Failed to revoke auth token');
	return response.json();
}

export async function cleanupExpiredTokens() {
	const response = await fetch('/api/auth/cleanup-expired', {
		method: 'DELETE',
	});
	if (!response.ok) throw new Error('Failed to cleanup expired tokens');
	return response.json();
}
