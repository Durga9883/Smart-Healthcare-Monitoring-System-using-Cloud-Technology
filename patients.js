/**
 * patients.js – Patient Management Page Logic
 * Handles: load list, search, add modal, edit modal, delete confirmation.
 */

let allPatients   = [];
let editingId     = null;
let deletingId    = null;
let searchTimeout = null;

/* ── Init ───────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  loadPatients();
  loadAlertCount();
  // Hide add button for patient role
  const user = getUser();
  if (user.role === "patient") {
    const btn = document.getElementById("btn-add-patient");
    if (btn) btn.style.display = "none";
  }
});

/* ── Load patients ──────────────────────────────────────────── */

async function loadPatients() {
  const res = await apiFetch("/api/patients");
  if (!res) return;
  allPatients = await res.json();
  renderTable(allPatients);
  const countEl = document.getElementById("patient-count");
  if (countEl) countEl.textContent = `(${allPatients.length})`;
}

/* ── Render table ───────────────────────────────────────────── */

function renderTable(patients) {
  const tbody = document.getElementById("patients-tbody");
  if (!tbody) return;

  if (!patients.length) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--txt-muted)">
      No patients found. <button class="btn btn-primary btn-sm" onclick="openAddModal()">Add First Patient</button>
    </td></tr>`;
    return;
  }

  const user = getUser();
  tbody.innerHTML = patients.map(p => `
    <tr>
      <td><code style="color:var(--clr-accent)">${p.patient_id || "—"}</code></td>
      <td>
        <div style="font-weight:600;">${p.name}</div>
      </td>
      <td>${p.age}</td>
      <td>${p.gender}</td>
      <td>${p.blood_group || "—"}</td>
      <td>${p.contact || "—"}</td>
      <td style="max-width:180px;font-size:12px;color:var(--txt-secondary);">
        ${p.medical_history ? p.medical_history.substring(0, 60) + (p.medical_history.length > 60 ? "…" : "") : "None"}
      </td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <a href="/patients/${p.id}" class="btn btn-outline btn-sm">📋 View</a>
          ${user.role !== "patient" ? `<button class="btn btn-outline btn-sm" onclick="openEditModal(${JSON.stringify(p).replace(/"/g,'&quot;')})">✏️ Edit</button>` : ""}
          ${user.role === "admin"   ? `<button class="btn btn-danger btn-sm" onclick="openDeleteModal(${p.id}, '${p.name.replace(/'/g,"\\'")}')">🗑️</button>` : ""}
        </div>
      </td>
    </tr>`).join("");
}

/* ── Search ─────────────────────────────────────────────────── */

function debounceSearch(val) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => searchPatients(val), 300);
}

function searchPatients(q) {
  if (!q.trim()) {
    renderTable(allPatients);
    return;
  }
  const lower = q.toLowerCase();
  const filtered = allPatients.filter(p =>
    p.name.toLowerCase().includes(lower) ||
    (p.patient_id || "").toLowerCase().includes(lower)
  );
  renderTable(filtered);
}

function filterPatients() {
  const status = document.getElementById("filter-status").value;
  // Status filter requires health data — for simplicity, reload from API with status param
  renderTable(allPatients); // basic client-side (expand with health join if needed)
}

/* ── Add / Edit Modal ───────────────────────────────────────── */

function openAddModal() {
  editingId = null;
  document.getElementById("modal-title").textContent = "Add New Patient";
  document.getElementById("save-btn").textContent    = "Save Patient";
  document.getElementById("patient-form").reset();
  document.getElementById("patient-id-field").value = "";
  document.getElementById("patient-modal").classList.add("open");
}

function openEditModal(p) {
  editingId = p.id;
  document.getElementById("modal-title").textContent = "Edit Patient";
  document.getElementById("save-btn").textContent    = "Update Patient";
  document.getElementById("patient-id-field").value = p.id;
  document.getElementById("p-name").value    = p.name || "";
  document.getElementById("p-age").value     = p.age  || "";
  document.getElementById("p-gender").value  = p.gender || "";
  document.getElementById("p-blood").value   = p.blood_group || "";
  document.getElementById("p-contact").value = p.contact || "";
  document.getElementById("p-history").value = p.medical_history || "";
  document.getElementById("patient-modal").classList.add("open");
}

function closeModal() {
  document.getElementById("patient-modal").classList.remove("open");
}

/* ── Save Patient ───────────────────────────────────────────── */

async function savePatient(e) {
  e.preventDefault();
  const btn = document.getElementById("save-btn");
  btn.disabled = true;
  btn.textContent = "Saving…";

  const payload = {
    name:            document.getElementById("p-name").value.trim(),
    age:             parseInt(document.getElementById("p-age").value),
    gender:          document.getElementById("p-gender").value,
    blood_group:     document.getElementById("p-blood").value,
    contact:         document.getElementById("p-contact").value.trim(),
    medical_history: document.getElementById("p-history").value.trim(),
  };

  let res;
  if (editingId) {
    res = await apiFetch(`/api/patients/${editingId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  } else {
    res = await apiFetch("/api/patients", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  btn.disabled = false;
  btn.textContent = editingId ? "Update Patient" : "Save Patient";

  if (res && res.ok) {
    showToast(editingId ? "Patient updated!" : "Patient added!", "success");
    closeModal();
    loadPatients();
  } else {
    const d = res ? await res.json() : {};
    showToast(d.error || "Failed to save patient.", "error");
  }
}

/* ── Delete ─────────────────────────────────────────────────── */

function openDeleteModal(id, name) {
  deletingId = id;
  document.getElementById("delete-patient-name").textContent = name;
  document.getElementById("delete-modal").classList.add("open");
}

function closeDeleteModal() {
  document.getElementById("delete-modal").classList.remove("open");
  deletingId = null;
}

async function confirmDelete() {
  if (!deletingId) return;
  const btn = document.getElementById("confirm-delete-btn");
  btn.disabled = true;
  btn.textContent = "Deleting…";

  const res = await apiFetch(`/api/patients/${deletingId}`, { method: "DELETE" });

  btn.disabled = false;
  btn.textContent = "Delete";

  if (res && res.ok) {
    showToast("Patient deleted.", "success");
    closeDeleteModal();
    loadPatients();
  } else {
    showToast("Failed to delete.", "error");
  }
}

/* ── Alert count for sidebar badge ─────────────────────────── */

async function loadAlertCount() {
  const res = await apiFetch("/api/dashboard/stats");
  if (!res) return;
  const d = await res.json();
  const el = document.getElementById("sidebar-alert-count");
  if (el) el.textContent = d.active_alerts || 0;
}

/* ── Close modal on outside click ──────────────────────────── */

document.addEventListener("click", e => {
  const modal = document.getElementById("patient-modal");
  if (modal && e.target === modal) closeModal();
  const dModal = document.getElementById("delete-modal");
  if (dModal && e.target === dModal) closeDeleteModal();
});
