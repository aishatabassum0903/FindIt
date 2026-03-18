// api.js — Central API handler for all fetch() calls
const BASE_URL = "http://127.0.0.1:5000/api";
function getToken() {
  return localStorage.getItem("token");
}

function getHeaders(includeAuth = true) {
  const headers = { "Content-Type": "application/json" };
  if (includeAuth && getToken()) {
    headers["Authorization"] = `Bearer ${getToken()}`;
  }
  return headers;
}

async function request(endpoint, method = "GET", body = null, auth = true) {
  const options = { method, headers: getHeaders(auth) };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}${endpoint}`, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// AUTH
const Auth = {
  register: (data) => request("/auth/register", "POST", data, false),
  login:    (data) => request("/auth/login",    "POST", data, false),
  me:       ()     => request("/auth/me"),
};

// ITEMS
const Items = {
  getAll:   (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/items${q ? "?" + q : ""}`);
  },
  search:   (q)      => request(`/items/search?q=${encodeURIComponent(q)}`),
  getById:  (id)     => request(`/items/${id}`),
  create:   (data)   => request("/items", "POST", data),
  update:   (id, d)  => request(`/items/${id}`, "PUT", d),
  delete:   (id)     => request(`/items/${id}`, "DELETE"),
  stats:    ()       => request("/items/stats/overview"),
};

// MATCHES
const Matches = {
  getForItem: (itemId) => request(`/matches/${itemId}`),
  run:        (itemId) => request(`/matches/run/${itemId}`, "POST"),
};

// CLAIMS
const Claims = {
  submit:       (data)       => request("/claims", "POST", data),
  getForItem:   (itemId)     => request(`/claims/${itemId}`),
  updateStatus: (id, status) => request(`/claims/${id}/status`, "PUT", { status }),
};

// NOTIFICATIONS
const Notifications = {
  getAll:    ()   => request("/notifications"),
  markRead:  (id) => request(`/notifications/${id}/read`, "PUT"),
  markAllRead: () => request("/notifications/read-all",   "PUT"),
};

// UPLOAD
const Upload = {
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/upload`, {
      method:  "POST",
      headers: { Authorization: `Bearer ${getToken()}` },
      body:    formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");
    return data;
  },
};

// Toast notifications
function showToast(message, type = "success") {
  const existing = document.getElementById("toast-container");
  if (!existing) {
    const container = document.createElement("div");
    container.id = "toast-container";
    container.style.cssText = `
      position:fixed; top:20px; right:20px; z-index:9999;
      display:flex; flex-direction:column; gap:10px;
    `;
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  const colors = {
    success: "#10B981",
    error:   "#EF4444",
    info:    "#2563EB",
    warning: "#F59E0B"
  };
  toast.style.cssText = `
    background: ${colors[type] || colors.info};
    color: white;
    padding: 12px 20px;
    border-radius: 10px;
    font-family: 'Poppins', sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideIn 0.3s ease;
    max-width: 320px;
    display: flex;
    align-items: center;
    gap: 8px;
  `;

  const icons = { success:"✓", error:"✕", info:"ℹ", warning:"⚠" };
  toast.innerHTML = `<span>${icons[type]||""}</span><span>${message}</span>`;

  document.getElementById("toast-container").appendChild(toast);
  setTimeout(() => { toast.style.opacity = "0"; toast.style.transition = "opacity 0.3s"; }, 3000);
  setTimeout(() => toast.remove(), 3300);
}

// Auth guard
function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "/pages/login.html";
    return false;
  }
  return true;
}

function getCurrentUser() {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/index.html";
}
