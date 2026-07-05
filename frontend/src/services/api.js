/**
 * KOVIRX Platform — Frontend API Client.
 * Handles JWT authorization header injection, request routing,
 * login states, and WebSocket connection URL resolver.
 */

// Dynamically determine the backend base API URL
const getBaseUrl = () => {
  const backendUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL;
  if (backendUrl) {
    const cleanUrl = backendUrl.replace(/\/$/, '');
    if (cleanUrl.endsWith('/api/v1')) {
      return cleanUrl;
    }
    return `${cleanUrl}/api/v1`;
  }
  // Fallback to local Vite dev server proxy path
  return '/api/v1';
};

const BASE_URL = getBaseUrl();

console.log("VITE_API_URL:", import.meta.env.VITE_API_URL);
console.log("BASE_URL:", BASE_URL);

export const getToken = () => {
  return localStorage.getItem('kovirx_access_token');
};

export const getRefreshToken = () => {
  return localStorage.getItem('kovirx_refresh_token');
};

export const setTokens = (accessToken, refreshToken) => {
  localStorage.setItem('kovirx_access_token', accessToken);
  localStorage.setItem('kovirx_refresh_token', refreshToken);
};

export const logout = () => {
  localStorage.removeItem('kovirx_access_token');
  localStorage.removeItem('kovirx_refresh_token');
  window.dispatchEvent(new Event('auth_change'));
};

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
      // Access token might be expired. Try to refresh.
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        logout();
        throw new Error('Authentication expired. Please log in again.');
      }

      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshRes.ok) {
          throw new Error('Refresh failed');
        }

        const refreshData = await refreshRes.json();
        setTokens(refreshData.access_token, refreshData.refresh_token);
        
        // Retry the original request
        headers['Authorization'] = `Bearer ${refreshData.access_token}`;
        const retryRes = await fetch(url, {
          ...options,
          headers,
        });

        if (!retryRes.ok) {
          const errorData = await retryRes.json().catch(() => ({}));
          throw new Error(errorData.detail || `Request failed with status ${retryRes.status}`);
        }
        return await retryRes.json();
      } catch (err) {
        logout();
        throw new Error('Session expired. Please log in again.');
      }
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
    setTokens(data.access_token, data.refresh_token);
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

  let backendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL;
  if (!backendUrl) {
    // If VITE_BACKEND_URL/VITE_API_URL is not set, we are running in local dev mode.
    // The Vite proxy doesn't proxy websockets by default unless configured.
    // Connect directly to the local backend port 8000:
    backendUrl = 'http://localhost:8000';
  }

  // Replace http/https protocol with ws/wss protocol
  const wsProto = backendUrl.startsWith('https') ? 'wss' : 'ws';
  const cleanUrl = backendUrl.replace(/^(https?:\/\/)/, '');
  
  return `${wsProto}://${cleanUrl}/ws/live?token=${encodeURIComponent(token)}`;
}

/**
 * Register a new device.
 */
export async function registerDevice(data) {
  return fetchWithAuth('/devices/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing device.
 */
export async function updateDevice(deviceId, data) {
  return fetchWithAuth(`/devices/${deviceId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a device.
 */
export async function deleteDevice(deviceId) {
  return fetchWithAuth(`/devices/${deviceId}`, {
    method: 'DELETE',
  });
}

/**
 * Assign alert to a user.
 */
export async function assignAlert(alertId, assignedTo) {
  return fetchWithAuth(`/alerts/${alertId}/assign`, {
    method: 'POST',
    body: JSON.stringify({ assigned_to: assignedTo }),
  });
}

/**
 * Trigger background report generation.
 */
export async function generateReport(reportType, format) {
  return fetchWithAuth('/reports/generate', {
    method: 'POST',
    body: JSON.stringify({ report_type: reportType, format }),
  });
}

/**
 * Get all reports.
 */
export async function getReports() {
  return fetchWithAuth('/reports');
}

/**
 * Download a generated report as a binary blob.
 */
export async function downloadReport(reportId) {
  const token = getToken();
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${BASE_URL}/reports/${reportId}/download`, {
    headers,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to download report');
  }
  return await response.blob();
}

/**
 * Get system logs.
 */
export async function getSystemLogs(level = null, module = null, skip = 0, limit = 50) {
  let query = `?skip=${skip}&limit=${limit}`;
  if (level) query += `&level=${level}`;
  if (module) query += `&module=${module}`;
  return fetchWithAuth(`/logs/system${query}`);
}

/**
 * Get audit logs.
 */
// ── Telemetry APIs ──────────────────────────────────────────────

/**
 * Ingest telemetry payloads directly.
 */
export async function ingestTelemetry(payload) {
  return fetchWithAuth('/telemetry/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}


export async function getAuditLogs(userId = null, action = null, skip = 0, limit = 50) {
  let query = `?skip=${skip}&limit=${limit}`;
  if (userId) query += `&user_id=${userId}`;
  if (action) query += `&action=${action}`;
  return fetchWithAuth(`/logs/audit${query}`);
}


// ── Risk Engine APIs ────────────────────────────────────────────

/**
 * Calculate multi-source risk score for a telemetry event.
 */
export async function calculateRisk(payload) {
  return fetchWithAuth('/risk/calculate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Get device risk history for trend chart.
 */
export async function getDeviceRiskHistory(deviceId, days = 7) {
  return fetchWithAuth(`/risk/device/${deviceId}/history?days=${days}`);
}


// ── Behavior Analysis APIs ──────────────────────────────────────

/**
 * Get network-wide behavior analysis overview.
 */
export async function getBehaviorOverview(hours = 24) {
  return fetchWithAuth(`/behavior/overview?hours=${hours}`);
}

/**
 * Get behavior analysis for a specific device.
 */
export async function getDeviceBehavior(deviceId, hours = 24) {
  return fetchWithAuth(`/behavior/device/${deviceId}?hours=${hours}`);
}


// ── Agent Management APIs ───────────────────────────────────────

/**
 * Send a command to endpoint agent(s).
 */
export async function sendAgentCommand(command, target = null, deviceId = null, payload = {}) {
  return fetchWithAuth('/agent/command', {
    method: 'POST',
    body: JSON.stringify({
      device_id: deviceId,
      command,
      target,
      payload,
    }),
  });
}

/**
 * Get latest agent version info.
 */
export async function getAgentVersion() {
  return fetchWithAuth('/agent/version');
}

/**
 * List active agent WebSocket connections.
 */
export async function getAgentConnections() {
  return fetchWithAuth('/agent/connections');
}


// ── Heartbeat API ───────────────────────────────────────────────

/**
 * Get device heartbeat status (used by the dashboard health widget).
 */
export async function getDeviceHeartbeats(deviceId) {
  // This endpoint would be added for querying heartbeat history
  return fetchWithAuth(`/devices/${deviceId}`);
}

// ── Enterprise Authentication APIs ─────────────────────────────────

export async function forgotPassword(email) {
  return fetchWithAuth('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token, newPassword) {
  return fetchWithAuth('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function changePassword(currentPassword, newPassword) {
  return fetchWithAuth('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export async function updateProfile(data) {
  return fetchWithAuth('/auth/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function getSessions() {
  return fetchWithAuth('/auth/sessions');
}

export async function revokeSession(sessionId) {
  return fetchWithAuth(`/auth/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function revokeAllSessions() {
  return fetchWithAuth('/auth/sessions', {
    method: 'DELETE',
  });
}

export async function adminGetUsers() {
  return fetchWithAuth('/auth/admin/users');
}

export async function adminCreateUser(data) {
  return fetchWithAuth('/auth/admin/users', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function adminEditUser(userId, data) {
  return fetchWithAuth(`/auth/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function adminUnlockUser(userId) {
  return fetchWithAuth(`/auth/admin/users/${userId}/unlock`, {
    method: 'POST',
  });
}

export async function adminGetAuditLogs() {
  return fetchWithAuth('/auth/admin/audit-logs');
}


