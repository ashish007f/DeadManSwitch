import type { 
  StatusResponse, 
  CheckInResponse, 
  SettingsResponse, 
  InstructionsResponse,
  User,
} from './types';
import { API_BASE, STORAGE_KEYS } from './constants';

// Token storage helpers
const getAccessToken = () => localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
const getRefreshToken = () => localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
const setTokens = (access: string, refresh: string) => {
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access);
  localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh);
};
const clearTokens = () => {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
};

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  
  const headers = new Headers(options?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });
  
  // Handle Token Expiration
  if (res.status === 403) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      // Try to refresh
      try {
        const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (refreshRes.ok) {
          const { access_token } = await refreshRes.json();
          localStorage.setItem('access_token', access_token);
          
          // Retry original request
          headers.set('Authorization', `Bearer ${access_token}`);
          res = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers,
          });
        } else {
          clearTokens();
          window.location.reload(); // Force login
        }
      } catch (err) {
        clearTokens();
        window.location.reload();
      }
    }
  }
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed with status ${res.status}`);
  }
  
  return res.json();
}

export const api = {
  // Auth
  verifyFirebase: async (idToken: string) => {
    const user = await request<User>('/auth/verify-firebase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken }),
    });
    if (user.access_token && user.refresh_token) {
      setTokens(user.access_token, user.refresh_token);
    }
    return user;
  },
  
  logout: async () => {
    try {
      await request<{ ok: boolean }>('/auth/logout', { method: 'POST' });
    } finally {
      clearTokens();
    }
    return { ok: true };
  },
  
  updateDisplayName: (displayName: string) =>
    request<User>('/auth/update-display-name', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: displayName }),
    }),
  
  updateFcmToken: (fcmToken: string) =>
    request<{ phone: string; fcm_token: string }>('/auth/update-fcm-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fcm_token: fcmToken }),
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
