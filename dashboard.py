"""
routes/dashboard.py – Dashboard Summary Endpoint
GET /api/dashboard/stats      → aggregate counts + latest vitals for all patients
GET /api/dashboard/all-vitals → latest reading per patient (for status cards)
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import models.health_record as hr_model

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    """
    Return summary metrics:
      - total_patients
      - critical / warning / normal counts
      - active_alerts count
    """
    data = hr_model.get_dashboard_stats()
    return jsonify(data), 200


@dashboard_bp.route("/all-vitals", methods=["GET"])
@jwt_required()
def all_vitals():
    """
    Return the latest vitals row for every patient.
    Used to render the patient status cards on the dashboard.
    """
    rows = hr_model.get_all_latest()
    for r in rows:
        r["recorded_at"] = str(r.get("recorded_at", ""))
    return jsonify(rows), 200
