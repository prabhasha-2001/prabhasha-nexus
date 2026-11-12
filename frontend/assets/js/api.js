(function () {
  const config = window.PRABHASHA_CONFIG || {};
  const API_BASE = (config.apiBase || "/api/v1").replace(/\/$/, "");
  const TOKEN_KEY = "nexus_token";
  const REFRESH_KEY = "nexus_refresh";
  const USER_KEY = "nexus_user";

  class ApiError extends Error {
    constructor(message, status, code, details) {
      super(message);
      this.status = status;
      this.code = code;
      this.details = details;
    }
  }

  function token() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setSession(data) {
    if (!data) return;
    if (data.access_token) localStorage.setItem(TOKEN_KEY, data.access_token);
    if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token);
    if (data.user) localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function currentUser() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || "null");
    } catch (_error) {
      return null;
    }
  }

  async function request(path, options = {}) {
    const { method = "GET", body, auth = false, formData = false, raw = false, signal } = options;
    const headers = {};
    if (!formData && body !== undefined) headers["Content-Type"] = "application/json";
    if (auth) {
      const stored = token();
      if (stored) headers.Authorization = `Bearer ${stored}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      signal,
      body: formData ? body : body !== undefined ? JSON.stringify(body) : undefined
    });

    if (raw) {
      if (!response.ok) throw new ApiError("Request failed", response.status);
      return response;
    }

    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }

    if (!response.ok || (payload && payload.success === false)) {
      const error = (payload && payload.error) || {};
      if (response.status === 401 && auth && !path.includes("/auth/login")) {
        clearSession();
        window.dispatchEvent(new CustomEvent("nexus:unauthorized"));
      }
      throw new ApiError(
        error.message || `Request failed (${response.status})`,
        response.status,
        error.code || "request_failed",
        error.details
      );
    }

    return { data: payload ? payload.data : null, meta: payload ? payload.meta : null, status: response.status };
  }

  async function refreshSession() {
    const refresh = localStorage.getItem(REFRESH_KEY);
    if (!refresh) throw new ApiError("No refresh token", 401, "unauthorized");
    const result = await request("/auth/refresh", {
      method: "POST",
      auth: false,
      body: undefined
    }).catch(async () => {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { Authorization: `Bearer ${refresh}` }
      });
      const payload = await response.json();
      if (!response.ok) throw new ApiError("Session expired", 401, "unauthorized");
      return { data: payload.data };
    });
    setSession(result.data);
    return result.data;
  }

  async function download(path, filename) {
    const response = await request(path, { auth: true, raw: true });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "download";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  window.nexusApi = {
    ApiError,
    API_BASE,
    TOKEN_KEY,
    REFRESH_KEY,
    request,
    get: (path, options) => request(path, { ...options, method: "GET" }),
    post: (path, body, options) => request(path, { ...options, method: "POST", body }),
    put: (path, body, options) => request(path, { ...options, method: "PUT", body }),
    del: (path, options) => request(path, { ...options, method: "DELETE" }),
    setSession,
    clearSession,
    token,
    currentUser,
    refreshSession,
    download,
    login: (email, password) =>
      request("/auth/login", { method: "POST", body: { email, password } }).then((result) => {
        setSession(result.data);
        return result.data;
      }),
    logout: () => {
      const refresh = localStorage.getItem(REFRESH_KEY);
      return fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: refresh ? { Authorization: `Bearer ${refresh}` } : {}
      })
        .catch(() => null)
        .finally(clearSession);
    }
  };
})();
