"""
routes/health.py – Health Vitals & Alert Endpoints
GET  /api/health/<patient_id>           → latest vitals
GET  /api/health/<patient_id>/history   → last N records
POST /api/health/simulate               → trigger one simulation cycle
GET  /api/alerts                        → all active alerts
GET  /api/alerts/<patient_id>           → alerts for one patient
PUT  /api/alerts/<alert_id>/resolve     → resolve an alert
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import models.health_record as hr_model

health_bp = Blueprint("health", __name__)


# ── Vitals ─────────────────────────────────────────────────────────────────────

@health_bp.route("/api/health/<int:patient_id>", methods=["GET"])
@jwt_required()
def latest_vitals(patient_id):
    """Return the most-recent vitals record for a patient."""
    record = hr_model.get_latest_record(patient_id)
    if not record:
        return jsonify({"error": "No health records found for this patient."}), 404
    record["recorded_at"] = str(record.get("recorded_at", ""))
    return jsonify(record), 200


@health_bp.route("/api/health/<int:patient_id>/history", methods=["GET"])
@jwt_required()
def vitals_history(patient_id):
    """Return the last `limit` vitals records for a patient (default 20)."""
    limit = int(request.args.get("limit", 20))
    records = hr_model.get_history(patient_id, limit=limit)
    for r in records:
        r["recorded_at"] = str(r.get("recorded_at", ""))
    return jsonify(records), 200


@health_bp.route("/api/health/simulate", methods=["POST"])
@jwt_required()
def trigger_simulate():
    """
    Manually trigger one round of vitals simulation for all patients.
    Useful during demos or testing without waiting for the background timer.
    """
    from services.simulator import _simulation_loop
    import threading
    t = threading.Thread(target=_simulation_loop_once, daemon=True)
    t.start()
    return jsonify({"message": "Simulation cycle triggered."}), 202


def _simulation_loop_once():
    """Run one iteration of the simulator (not the infinite loop)."""
    import random
    from models.patient import get_all_patients
    from models.health_record import insert_record
    from services.simulator import _random_vitals
    from services.alert_engine import evaluate

    patients = get_all_patients()
    for p in patients:
        vitals = _random_vitals(p["age"])
        status, _ = evaluate(
            patient_id=p["id"],
            temp=vitals["temperature"],
            hr=vitals["heart_rate"],
            spo2=vitals["oxygen_level"],
            bp_sys=vitals["blood_pressure_sys"],
        )
        insert_record(
            patient_id=p["id"],
            temp=vitals["temperature"],
            hr=vitals["heart_rate"],
            spo2=vitals["oxygen_level"],
            bp_sys=vitals["blood_pressure_sys"],
            bp_dia=vitals["blood_pressure_dia"],
            status=status,
        )


# ── Alerts ─────────────────────────────────────────────────────────────────────

@health_bp.route("/api/alerts", methods=["GET"])
@jwt_required()
def active_alerts():
    """Return all unresolved alerts with patient name, newest first."""
    limit = int(request.args.get("limit", 50))
    alerts = hr_model.get_active_alerts(limit=limit)
    for a in alerts:
        a["created_at"] = str(a.get("created_at", ""))
    return jsonify(alerts), 200


@health_bp.route("/api/alerts/<int:patient_id>", methods=["GET"])
@jwt_required()
def patient_alerts(patient_id):
    """Return all alerts (resolved + unresolved) for one patient."""
    alerts = hr_model.get_alerts_for_patient(patient_id)
    for a in alerts:
        a["created_at"] = str(a.get("created_at", ""))
    return jsonify(alerts), 200


@health_bp.route("/api/alerts/<int:alert_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_alert(alert_id):
    """Mark a specific alert as resolved."""
    ok = hr_model.resolve_alert(alert_id)
    if not ok:
        return jsonify({"error": "Alert not found or already resolved."}), 404
    return jsonify({"message": "Alert resolved."}), 200
