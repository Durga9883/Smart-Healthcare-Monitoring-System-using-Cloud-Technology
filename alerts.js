/**
 * alerts.js – Alerts Page Logic
 * Loads all active alerts with filter tabs and resolve capability.
 */

let allAlerts  = [];
let activeFilter = "all";

/* ── Init ───────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  loadAlerts();
  loadAlertCount();
  setInterval(loadAlerts, 20000);
});

/* ── Load & render ──────────────────────────────────────────── */

async function loadAlerts() {
  const res = await apiFetch("/api/alerts?limit=100");
  if (!res) return;
  allAlerts = await res.json();

  const critical = allAlerts.filter(a => a.severity === "critical").length;
  const warning  = allAlerts.filter(a => a.severity === "warning").length;

  setText("count-critical", critical);
  setText("count-warning",  warning);
  setText("sidebar-alert-count", allAlerts.length);

  // Resolved today — placeholder (full implementation needs separate endpoint)
  setText("count-resolved", "—");

  renderAlerts();
}

function renderAlerts() {
  const container = document.getElementById("alerts-container");
  if (!container) return;

  let filtered = allAlerts;
  if (activeFilter !== "all") {
    filtered = allAlerts.filter(a => a.severity === activeFilter);
  }

  if (!filtered.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><p>No ${activeFilter === "all" ? "active" : activeFilter} alerts.</p></div>`;
    return;
  }

  container.innerHTML = filtered.map(a => `
    <div class="alert-item ${a.severity}" id="alert-${a.id}" style="margin-bottom:12px;">
      <div class="alert-icon" style="font-size:24px;">${a.severity === "critical" ? "🚨" : "⚠️"}</div>
      <div class="alert-content" style="flex:1;">
        <div class="alert-title" style="font-size:15px;">${a.message}</div>
        <div class="alert-meta" style="margin-top:4px;">
          <strong>${a.patient_name}</strong> (${a.pid})
          · ${a.alert_type}
          · ${new Date(a.created_at).toLocaleString()}
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px;flex-shrink:0;align-items:flex-end;">
        <span class="badge ${a.severity === "critical" ? "badge-critical" : "badge-warning"}">${a.severity}</span>
        <button class="btn btn-success btn-sm" onclick="resolveAlert(${a.id}, this)">✓ Resolve</button>
        <a href="/patients/${a.patient_id}" class="btn btn-outline btn-sm">View Patient</a>
      </div>
    </div>`).join("");
}

/* ── Filter ─────────────────────────────────────────────────── */

function setFilter(filter, btn) {
  activeFilter = filter;
  document.querySelectorAll("[id^='filter-']").forEach(b => {
    b.className = "btn btn-outline btn-sm";
  });
  btn.className = "btn btn-primary btn-sm";
  renderAlerts();
}

/* ── Resolve ────────────────────────────────────────────────── */

async function resolveAlert(alertId, btn) {
  btn.disabled = true;
  btn.textContent = "Resolving…";
  const res = await apiFetch(`/api/alerts/${alertId}/resolve`, { method: "PUT" });

  if (res && res.ok) {
    showToast("Alert resolved successfully.", "success");
    // Animate out
    const el = document.getElementById(`alert-${alertId}`);
    if (el) { el.style.opacity = "0"; el.style.transition = "opacity 0.4s"; setTimeout(() => el.remove(), 400); }
    allAlerts = allAlerts.filter(a => a.id !== alertId);
    // Update counts
    const critical = allAlerts.filter(a => a.severity === "critical").length;
    const warning  = allAlerts.filter(a => a.severity === "warning").length;
    setText("count-critical", critical);
    setText("count-warning",  warning);
    setText("sidebar-alert-count", allAlerts.length);
  } else {
    showToast("Failed to resolve alert.", "error");
    btn.disabled = false;
    btn.textContent = "✓ Resolve";
  }
}

/* ── Alert count badge ──────────────────────────────────────── */

async function loadAlertCount() {
  const res = await apiFetch("/api/dashboard/stats");
  if (!res) return;
  const d = await res.json();
  setText("sidebar-alert-count", d.active_alerts || 0);
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
