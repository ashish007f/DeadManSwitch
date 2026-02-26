import type { 
  StatusResponse, 
  CheckInResponse, 
  SettingsResponse, 
  InstructionsResponse,
  User,
} from './types';

const API_BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed with status ${res.status}`);
  }
  
  return res.json();
}

export const api = {
  // Auth
  verifyFirebase: (idToken: string) =>
    request<User>('/auth/verify-firebase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken }),
    }),
  
  logout: () =>
    request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  
  updateDisplayName: (displayName: string) =>
    request<User>('/auth/update-display-name', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: displayName }),
    }),
  
  me: () => request<User>('/me'),

  // Check-in
  getStatus: () => request<StatusResponse>('/status'),
  
  checkin: (hoursAgo?: number) =>
    request<CheckInResponse>('/checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(hoursAgo !== undefined ? { hours_ago: hoursAgo } : {}),
    }),

  // Settings
  getSettings: () => request<SettingsResponse>('/settings'),
  
  updateSettings: (settings: Partial<SettingsResponse>) =>
    request<SettingsResponse>('/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }),
  
  // Instructions
  getInstructions: () => request<InstructionsResponse>('/instructions'),
  
  saveInstructions: (content: string) =>
    request<InstructionsResponse>('/instructions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    }),
};
