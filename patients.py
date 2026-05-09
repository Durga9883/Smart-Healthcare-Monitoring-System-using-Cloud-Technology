"""
routes/patients.py – Patient Management Endpoints
GET    /api/patients            → list all patients
POST   /api/patients            → create patient
GET    /api/patients/<id>       → get one patient
PUT    /api/patients/<id>       → update patient
DELETE /api/patients/<id>       → delete patient
GET    /api/patients/search     → search by name/id
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import models.patient as patient_model

patients_bp = Blueprint("patients", __name__, url_prefix="/api/patients")


def _require_admin_or_doctor():
    """Helper – deny access if caller is a plain patient."""
    claims = get_jwt()
    role = claims.get("role", "patient")
    if role not in ("admin", "doctor"):
        return jsonify({"error": "Forbidden – insufficient role."}), 403
    return None


@patients_bp.route("", methods=["GET"])
@jwt_required()
def list_patients():
    """Return all patients (admin/doctor) or only own record (patient)."""
    claims  = get_jwt()
    role    = claims.get("role", "patient")
    query   = request.args.get("search", "").strip()

    if query:
        patients = patient_model.search_patients(query)
    elif role == "admin":
        patients = patient_model.get_all_patients()
    elif role == "doctor":
        from flask_jwt_extended import get_jwt_identity
        doc_id   = int(get_jwt_identity())
        patients = patient_model.get_all_patients(doctor_id=doc_id)
    else:
        # patient role – not used in this flow, handled by patient_detail
        patients = []

    # Convert datetime objects to strings for JSON serialisation
    for p in patients:
        if p.get("created_at"):
            p["created_at"] = str(p["created_at"])
    return jsonify(patients), 200


@patients_bp.route("", methods=["POST"])
@jwt_required()
def create_patient():
    """Add a new patient record (admin/doctor only)."""
    err = _require_admin_or_doctor()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ["name", "age", "gender"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required."}), 400

    new_id = patient_model.create_patient(data)
    return jsonify({"message": "Patient created.", "id": new_id}), 201


@patients_bp.route("/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_patient(patient_id):
    """Return full details for a single patient."""
    p = patient_model.get_patient_by_id(patient_id)
    if not p:
        return jsonify({"error": "Patient not found."}), 404
    if p.get("created_at"):
        p["created_at"] = str(p["created_at"])
    return jsonify(p), 200


@patients_bp.route("/<int:patient_id>", methods=["PUT"])
@jwt_required()
def update_patient(patient_id):
    """Update a patient record (admin/doctor only)."""
    err = _require_admin_or_doctor()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    ok = patient_model.update_patient(patient_id, data)
    if not ok:
        return jsonify({"error": "Patient not found or no changes."}), 404
    return jsonify({"message": "Patient updated."}), 200


@patients_bp.route("/<int:patient_id>", methods=["DELETE"])
@jwt_required()
def delete_patient(patient_id):
    """Delete a patient and their records (admin only)."""
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin role required."}), 403

    ok = patient_model.delete_patient(patient_id)
    if not ok:
        return jsonify({"error": "Patient not found."}), 404
    return jsonify({"message": "Patient deleted."}), 200


@patients_bp.route("/search", methods=["GET"])
@jwt_required()
def search_patients():
    """Quick-search patients by name or patient_id."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([]), 200
    results = patient_model.search_patients(q)
    for p in results:
        if p.get("created_at"):
            p["created_at"] = str(p["created_at"])
    return jsonify(results), 200
