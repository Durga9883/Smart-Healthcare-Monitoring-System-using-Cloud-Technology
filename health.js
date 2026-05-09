/**
 * health.js – Patient Detail Page Logic
 * Loads patient profile, latest vitals, trend chart, history table, alerts.
 * Auto-refreshes every 20 seconds.
 */

let trendChart = null;
const patientId = parseInt(window.location.pathname.split("/").pop());

/* ── Init ───────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  if (isNaN(patientId)) return;
  loadPatient();
  loadLatestVitals();
  loadHistory();
  loadPatientAlerts();

  setInterval(() => {
    loadLatestVitals();
    loadHistory();
    loadPatientAlerts();
  }, 20000);
});

/* ── Patient profile ────────────────────────────────────────── */

async function loadPatient() {
  const res = await apiFetch(`/api/patients/${patientId}`);
  if (!res || !res.ok) return;
  const p = await res.json();

  setText("page-title", p.name);
  setText("p-name", p.name);
  setText("p-id",  `ID: ${p.patient_id}`);
  setText("p-age-gender", `${p.age} yrs · ${p.gender}`);
  setText("p-blood", `Blood: ${p.blood_group || "—"}`);
  setText("p-contact", `📞 ${p.contact || "—"}`);
  setText("p-history", p.medical_history || "No known history");

  // Set avatar emoji by gender
  const avatarEl = document.getElementById("patient-avatar");
  if (avatarEl) avatarEl.textContent = p.gender === "Female" ? "👩" : "👨";
}

/* ── Latest vitals ──────────────────────────────────────────── */

async function loadLatestVitals() {
  const res = await apiFetch(`/api/health/${patientId}`);
  if (!res) return;

  if (!res.ok) {
    // No readings yet
    ["v-temp","v-hr","v-spo2","v-bp"].forEach(id => setText(id, "—"));
    return;
  }

  const v = await res.json();

  // Temperature
  const tempEl = document.getElementById("v-temp");
  if (tempEl) {
    tempEl.textContent = v.temperature + "°";
    tempEl.style.color = v.temperature > 100 ? "var(--clr-danger)" :
                         v.temperature > 99.5 ? "var(--clr-warning)" : "var(--clr-success)";
  }

  // Heart rate
  const hrEl = document.getElementById("v-hr");
  if (hrEl) {
    hrEl.textContent = v.heart_rate;
    hrEl.style.color = v.heart_rate > 120 ? "var(--clr-danger)" :
                       v.heart_rate > 100 ? "var(--clr-warning)" : "var(--clr-success)";
  }

  // SpO2
  const spo2El = document.getElementById("v-spo2");
  if (spo2El) {
    spo2El.textContent = v.oxygen_level + "%";
    spo2El.style.color = v.oxygen_level < 90 ? "var(--clr-danger)" :
                         v.oxygen_level < 95 ? "var(--clr-warning)" : "var(--clr-success)";
  }

  // Blood pressure
  const bpEl = document.getElementById("v-bp");
  if (bpEl) {
    bpEl.textContent = v.blood_pressure_sys ? `${v.blood_pressure_sys}/${v.blood_pressure_dia}` : "—";
    bpEl.style.color = (v.blood_pressure_sys || 0) >= 140 ? "var(--clr-danger)" : "var(--clr-success)";
  }

  // Status badge
  const badgeEl = document.getElementById("p-status-badge");
  if (badgeEl) {
    const map = { normal: "badge-normal", warning: "badge-warning", critical: "badge-critical" };
    badgeEl.innerHTML = `<span class="badge ${map[v.status] || 'badge-normal'}" style="font-size:13px;padding:5px 14px;">${v.status || "—"}</span>`;
  }

  setText("last-updated", "Updated " + new Date().toLocaleTimeString());
}

/* ── History table + trend chart ────────────────────────────── */

async function loadHistory() {
  const res = await apiFetch(`/api/health/${patientId}/history?limit=20`);
  if (!res || !res.ok) return;
  const records = await res.json();

  renderHistoryTable(records);
  renderTrendChart(records);
}

function renderHistoryTable(records) {
  const tbody = document.getElementById("history-tbody");
  if (!tbody) return;

  if (!records.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:20px;color:var(--txt-muted)">No history yet</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
    const time = new Date(r.recorded_at).toLocaleString("en-IN", { hour12: true, hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" });
    const map = { normal: "badge-normal", warning: "badge-warning", critical: "badge-critical" };
    return `<tr>
      <td style="font-size:12px;color:var(--txt-muted)">${time}</td>
      <td class="vital-value ${r.temperature > 100 ? "danger" : r.temperature > 99.5 ? "warn" : "ok"}">${r.temperature}°F</td>
      <td class="vital-value ${r.heart_rate > 120 ? "danger" : r.heart_rate > 100 ? "warn" : "ok"}">${r.heart_rate} bpm</td>
      <td class="vital-value ${r.oxygen_level < 90 ? "danger" : r.oxygen_level < 95 ? "warn" : "ok"}">${r.oxygen_level}%</td>
      <td><span class="badge ${map[r.status] || 'badge-normal'}">${r.status}</span></td>
    </tr>`;
  }).join("");
}

function renderTrendChart(records) {
  // Reverse so oldest is on left
  const rev = [...records].reverse();
  const labels = rev.map(r => {
    const d = new Date(r.recorded_at);
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  });

  const ctx = document.getElementById("trendChart");
  if (!ctx) return;

  const chartData = {
    labels,
    datasets: [
      {
        label: "Temp (°F)",
        data: rev.map(r => r.temperature),
        borderColor: "#ef4444",
        backgroundColor: "rgba(239,68,68,0.1)",
        tension: 0.4, fill: true, yAxisID: "y",
      },
      {
        label: "Heart Rate (bpm)",
        data: rev.map(r => r.heart_rate),
        borderColor: "#f59e0b",
        backgroundColor: "rgba(245,158,11,0.08)",
        tension: 0.4, fill: false, yAxisID: "y1",
      },
      {
        label: "SpO₂ (%)",
        data: rev.map(r => r.oxygen_level),
        borderColor: "#06b6d4",
        backgroundColor: "rgba(6,182,212,0.08)",
        tension: 0.4, fill: false, yAxisID: "y",
      },
    ],
  };

  if (trendChart) {
    trendChart.data = chartData;
    trendChart.update();
    return;
  }

  trendChart = new Chart(ctx, {
    type: "line",
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#8ba3c7", font: { family: "Inter", size: 12 } } },
      },
      scales: {
        x:  { ticks: { color: "#8ba3c7", maxTicksLimit: 8 }, grid: { color: "rgba(30,50,85,0.4)" } },
        y:  { ticks: { color: "#8ba3c7" }, grid: { color: "rgba(30,50,85,0.4)" }, position: "left" },
        y1: { ticks: { color: "#8ba3c7" }, grid: { drawOnChartArea: false }, position: "right" },
      },
    },
  });
}

/* ── Patient Alerts ─────────────────────────────────────────── */

async function loadPatientAlerts() {
  const res = await apiFetch(`/api/alerts/${patientId}`);
  if (!res || !res.ok) return;
  const alerts = await res.json();
  const container = document.getElementById("patient-alerts");
  if (!container) return;

  const active = alerts.filter(a => !a.is_resolved);

  if (!active.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><p>No active alerts</p></div>`;
    return;
  }

  container.innerHTML = active.map(a => `
    <div class="alert-item ${a.severity}" style="margin-bottom:8px;">
      <div class="alert-icon">${a.severity === "critical" ? "🚨" : "⚠️"}</div>
      <div class="alert-content">
        <div class="alert-title">${a.message}</div>
        <div class="alert-meta">${new Date(a.created_at).toLocaleString()}</div>
      </div>
      <button class="btn btn-success btn-sm" style="margin-left:auto;flex-shrink:0;"
              onclick="resolveAlert(${a.id},this)">✓</button>
    </div>`).join("");
}

async function resolveAlert(alertId, btn) {
  btn.disabled = true;
  const res = await apiFetch(`/api/alerts/${alertId}/resolve`, { method: "PUT" });
  if (res && res.ok) {
    showToast("Alert resolved.", "success");
    loadPatientAlerts();
  } else {
    showToast("Failed.", "error");
    btn.disabled = false;
  }
}

/* ── Helpers ────────────────────────────────────────────────── */

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
