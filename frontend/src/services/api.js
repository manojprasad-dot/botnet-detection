/**
 * KOVIRX Platform — Frontend API Client.
 * Handles JWT authorization header injection, request routing,
 * login states, and WebSocket connection URL resolver.
 */

// Dynamically determine the backend base API URL
const getBaseUrl = () => {
  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  if (backendUrl) {
    // Remove trailing slash if present
    return `${backendUrl.replace(/\/$/, '')}/api/v1`;
  }
  // Fallback to local Vite dev server proxy path
  return '/api/v1';
};

const BASE_URL = getBaseUrl();

/**
 * Retrieve stored JWT token from local storage.
 */
export const getToken = () => {
  return localStorage.getItem('kovirx_access_token');
};

/**
 * Save JWT token to local storage.
 */
export const setToken = (token) => {
  localStorage.setItem('kovirx_access_token', token);
};

/**
 * Clear JWT token and log user out.
 */
export const logout = () => {
  localStorage.removeItem('kovirx_access_token');
  window.dispatchEvent(new Event('auth_change'));
};

/**
 * Helper to check if user has token.
 */
export const isAuthenticated = () => {
  return !!getToken();
};

/**
 * General authenticated fetch client.
 * Injects JWT token and handles auth errors (401).
 */
export async function fetchWithAuth(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const cleanEndpoint = endpoint.replace(/^\//, '');
  const url = `${BASE_URL}/${cleanEndpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token is invalid/expired
      logout();
      throw new Error('Authentication expired. Please log in again.');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error.message);
    throw error;
  }
}

/**
 * Auth APIs
 */
export async function login(email, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed. Check your credentials.');
  }

  const data = await response.json();
  if (data.access_token) {
    setToken(data.access_token);
    window.dispatchEvent(new Event('auth_change'));
    return data;
  }
  throw new Error('No access token returned from server.');
}

export async function getCurrentUser() {
  return fetchWithAuth('/auth/me');
}

/**
 * Dashboard APIs
 */
export async function getDashboardSummary() {
  return fetchWithAuth('/dashboard/summary');
}

/**
 * Alerts APIs
 */
export async function getAlerts() {
  const data = await fetchWithAuth('/alerts');
  return data.alerts || [];
}

export async function updateAlertStatus(alertId, status) {
  return fetchWithAuth(`/alerts/${alertId}`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  });
}

/**
 * Devices APIs
 */
export async function getDevices() {
  const data = await fetchWithAuth('/devices');
  return data.devices || [];
}

/**
 * Threat Intelligence APIs
 */
export async function getThreatFamilies() {
  const data = await fetchWithAuth('/threats/families');
  return data.families || [];
}

/**
 * Dynamic WebSocket Live Stream URL Builder.
 */
export function getWebSocketUrl() {
  const token = getToken();
  if (!token) return null;

  let backendUrl = import.meta.env.VITE_BACKEND_URL;
  if (!backendUrl) {
    // If VITE_BACKEND_URL is not set, we are running in local dev mode.
    // The Vite proxy doesn't proxy websockets by default unless configured.
    // Connect directly to the local backend port 8000:
    backendUrl = 'http://localhost:8000';
  }

  // Replace http/https protocol with ws/wss protocol
  const wsProto = backendUrl.startsWith('https') ? 'wss' : 'ws';
  const cleanUrl = backendUrl.replace(/^(https?:\/\/)/, '');
  
  return `${wsProto}://${cleanUrl}/ws/live?token=${encodeURIComponent(token)}`;
}
