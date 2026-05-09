/**
 * dashboard.js – Main Dashboard Logic
 * Polls /api/dashboard/stats and /api/dashboard/all-vitals every 15 s.
 * Renders Chart.js doughnut + bar charts and the live vitals table.
 */

let statusChart = null;
let alertChart  = null;
let pollInterval = null;

/* ── Initialise ─────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  loadStats();
  loadAllVitals();
  loadAlertFeed();

  // Auto-refresh every 15 seconds
  pollInterval = setInterval(() => {
    loadStats();
    loadAllVitals();
    loadAlertFeed();
  }, 15000);
});

/* ── Stats ──────────────────────────────────────────────────── */

async function loadStats() {
  const res = await apiFetch("/api/dashboard/stats");
  if (!res) return;
  const d = await res.json();

  setText("stat-total",    d.total_patients ?? "—");
  setText("stat-critical", d.critical       ?? "—");
  setText("stat-warning",  d.warning        ?? "—");
  setText("stat-normal",   d.normal         ?? "—");
  setText("stat-alerts",   d.active_alerts  ?? "—");
  setText("sidebar-alert-count", d.active_alerts ?? 0);
  setText("last-updated", "Updated " + new Date().toLocaleTimeString());

  updateStatusChart(d);
}

/* ── All Vitals Table ───────────────────────────────────────── */

async function loadAllVitals() {
  const res = await apiFetch("/api/dashboard/all-vitals");
  if (!res) return;
  const rows = await res.json();
  renderVitalsTable(rows);
  updateAlertChart(rows);
}

function renderVitalsTable(rows) {
  const tbody = document.getElementById("vitals-tbody");
  if (!tbody) return;

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:32px;color:var(--txt-muted)">No patient records found. <a href="/patients">Add a patient</a>.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const tempClass  = r.temperature  > 100  ? "danger" : r.temperature  > 99.5 ? "warn" : "ok";
    const hrClass    = r.heart_rate   > 120  ? "danger" : r.heart_rate   > 100  ? "warn" : "ok";
    const spo2Class  = r.oxygen_level < 90   ? "danger" : r.oxygen_level < 95   ? "warn" : "ok";
    const bp = r.blood_pressure_sys ? `${r.blood_pressure_sys}/${r.blood_pressure_dia}` : "—";
    const bpClass = (r.blood_pressure_sys || 0) >= 140 ? "danger" : "ok";
    const time = r.recorded_at ? new Date(r.recorded_at).toLocaleTimeString() : "—";

    return `<tr>
      <td><code style="color:var(--clr-accent)">${r.pid || "—"}</code></td>
      <td><strong>${r.name || "—"}</strong></td>
      <td><span class="vital-value ${tempClass}">${r.temperature ?? "—"}°F</span></td>
      <td><span class="vital-value ${hrClass}">${r.heart_rate ?? "—"} bpm</span></td>
      <td><span class="vital-value ${spo2Class}">${r.oxygen_level ?? "—"}%</span></td>
      <td><span class="vital-value ${bpClass}">${bp}</span></td>
      <td>${badgeBadge(r.status)}</td>
      <td style="color:var(--txt-muted);font-size:12px;">${time}</td>
      <td><a href="/patients/${r.patient_id}" class="btn btn-outline btn-sm">View</a></td>
    </tr>`;
  }).join("");
}

/* ── Alert Feed ─────────────────────────────────────────────── */

async function loadAlertFeed() {
  const res = await apiFetch("/api/alerts?limit=5");
  if (!res) return;
  const alerts = await res.json();
  const feed = document.getElementById("alert-feed");
  if (!feed) return;

  if (!alerts.length) {
    feed.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><p>No active alerts</p></div>`;
    return;
  }

  feed.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.severity}">
      <div class="alert-icon">${a.severity === "critical" ? "🚨" : "⚠️"}</div>
      <div class="alert-content">
        <div class="alert-title">${a.message}</div>
        <div class="alert-meta">${a.patient_name} (${a.pid}) · ${new Date(a.created_at).toLocaleString()}</div>
      </div>
      <button class="btn btn-success btn-sm" style="margin-left:auto;flex-shrink:0;"
              onclick="resolveAlert(${a.id}, this)">✓ Resolve</button>
    </div>`).join("");
}

async function resolveAlert(alertId, btn) {
  btn.disabled = true;
  const res = await apiFetch(`/api/alerts/${alertId}/resolve`, { method: "PUT" });
  if (res && res.ok) {
    showToast("Alert resolved.", "success");
    loadAlertFeed();
    loadStats();
  } else {
    showToast("Failed to resolve alert.", "error");
    btn.disabled = false;
  }
}

/* ── Simulate vitals ────────────────────────────────────────── */

async function triggerSimulate(e) {
  e.preventDefault();
  const res = await apiFetch("/api/health/simulate", { method: "POST" });
  if (res && res.ok) {
    showToast("Simulation cycle triggered!", "info");
    setTimeout(() => { loadStats(); loadAllVitals(); loadAlertFeed(); }, 2000);
  }
}

/* ── Charts ─────────────────────────────────────────────────── */

function initCharts() {
  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: "#8ba3c7", font: { family: "Inter" } } } },
  };

  // Status doughnut
  const ctx1 = document.getElementById("statusChart");
  if (ctx1) {
    statusChart = new Chart(ctx1, {
      type: "doughnut",
      data: {
        labels: ["Normal", "Warning", "Critical"],
        datasets: [{
          data: [0, 0, 0],
          backgroundColor: ["rgba(16,185,129,0.8)", "rgba(245,158,11,0.8)", "rgba(239,68,68,0.8)"],
          borderColor: "#0d1626",
          borderWidth: 3,
        }],
      },
      options: { ...chartDefaults, cutout: "65%" },
    });
  }

  // Alert types bar
  const ctx2 = document.getElementById("alertChart");
  if (ctx2) {
    alertChart = new Chart(ctx2, {
      type: "bar",
      data: {
        labels: ["High Fever", "Low Oxygen", "Rapid HR", "High BP"],
        datasets: [{
          label: "Active Alerts",
          data: [0, 0, 0, 0],
          backgroundColor: [
            "rgba(239,68,68,0.7)",
            "rgba(6,182,212,0.7)",
            "rgba(245,158,11,0.7)",
            "rgba(37,99,235,0.7)",
          ],
          borderRadius: 6,
        }],
      },
      options: {
        ...chartDefaults,
        scales: {
          x: { ticks: { color: "#8ba3c7" }, grid: { color: "rgba(30,50,85,0.4)" } },
          y: { ticks: { color: "#8ba3c7", stepSize: 1 }, grid: { color: "rgba(30,50,85,0.4)" } },
        },
      },
    });
  }
}

function updateStatusChart(d) {
  if (!statusChart) return;
  statusChart.data.datasets[0].data = [d.normal || 0, d.warning || 0, d.critical || 0];
  statusChart.update();
}

function updateAlertChart(rows) {
  if (!alertChart) return;
  // Count anomalies from vitals rows
  let fever = 0, spo2 = 0, hr = 0, bp = 0;
  rows.forEach(r => {
    if (r.temperature  > 100) fever++;
    if (r.oxygen_level < 90)  spo2++;
    if (r.heart_rate   > 120) hr++;
    if ((r.blood_pressure_sys || 0) >= 140) bp++;
  });
  alertChart.data.datasets[0].data = [fever, spo2, hr, bp];
  alertChart.update();
}

/* ── Helpers ────────────────────────────────────────────────── */

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function badgeBadge(status) {
  const map = { normal: "badge-normal", warning: "badge-warning", critical: "badge-critical" };
  const icon = { normal: "●", warning: "▲", critical: "⬥" };
  return `<span class="badge ${map[status] || "badge-normal"}">${icon[status] || "●"} ${status || "—"}</span>`;
}
