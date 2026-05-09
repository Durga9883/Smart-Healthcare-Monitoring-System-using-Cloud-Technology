/**
 * auth.js – Shared Authentication Helpers
 * Included on every page. Handles JWT storage, user info display,
 * login/logout, and guards unauthorised access.
 */

const API = "";   // same-origin; change to full URL for cross-origin

/* ── Token helpers ──────────────────────────────────────────── */

function getToken() {
  return localStorage.getItem("hms_token");
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("hms_user") || "{}");
  } catch {
    return {};
  }
}

function setSession(token, user) {
  localStorage.setItem("hms_token", token);
  localStorage.setItem("hms_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("hms_token");
  localStorage.removeItem("hms_user");
}

/* ── Auth-guarded fetch wrapper ─────────────────────────────── */

async function apiFetch(url, options = {}) {
  const token = getToken();
  if (!token && !url.includes("/api/auth/login")) {
    window.location.href = "/";
    return null;
  }
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(API + url, { ...options, headers });
  if (res.status === 401) {
    clearSession();
    window.location.href = "/";
    return null;
  }
  return res;
}

/* ── Login page logic ───────────────────────────────────────── */

let selectedRole = "admin";

function selectRole(btn) {
  document.querySelectorAll(".role-tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  selectedRole = btn.dataset.role;
}

function togglePwd() {
  const inp = document.getElementById("password");
  inp.type = inp.type === "password" ? "text" : "password";
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const errEl    = document.getElementById("error-msg");
  const btn      = document.getElementById("login-btn");

  errEl.classList.remove("show");
  if (!username || !password) {
    errEl.textContent = "Please enter username and password.";
    errEl.classList.add("show");
    return;
  }

  btn.textContent = "Signing in…";
  btn.disabled = true;

  try {
    const res  = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();

    if (!res.ok) {
      errEl.textContent = data.error || "Login failed.";
      errEl.classList.add("show");
      return;
    }

    setSession(data.token, data.user);
    window.location.href = "/dashboard";
  } catch (err) {
    errEl.textContent = "Cannot connect to server. Is Flask running?";
    errEl.classList.add("show");
  } finally {
    btn.textContent = "Sign In →";
    btn.disabled = false;
  }
}

/* ── Logout ─────────────────────────────────────────────────── */

async function logout() {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } catch {}
  clearSession();
  window.location.href = "/";
}

/* ── Populate sidebar user info ─────────────────────────────── */

function populateSidebarUser() {
  const user = getUser();
  const nameEl   = document.getElementById("user-name");
  const roleEl   = document.getElementById("user-role");
  const avatarEl = document.getElementById("user-avatar");
  if (nameEl)   nameEl.textContent   = user.full_name || user.username || "—";
  if (roleEl)   roleEl.textContent   = user.role || "—";
  if (avatarEl) avatarEl.textContent = (user.full_name || user.username || "A")[0].toUpperCase();
}

/* ── Toast notifications ────────────────────────────────────── */

function showToast(msg, type = "info", duration = 3500) {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

/* ── Guard: redirect if not logged in ───────────────────────── */

(function guardPage() {
  const isLoginPage = window.location.pathname === "/";
  if (!isLoginPage && !getToken()) {
    window.location.href = "/";
  }
  if (isLoginPage && getToken()) {
    window.location.href = "/dashboard";
  }
  populateSidebarUser();
})();
