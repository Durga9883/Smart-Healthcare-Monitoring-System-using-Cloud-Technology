"""
models/patient.py – Patient profile CRUD
Manages the 'patients' table: add, update, delete, and search patients.
"""

from models import get_db


def get_all_patients(doctor_id: int | None = None) -> list:
    """
    Return all patients.
    If doctor_id is given, filter to only that doctor's patients.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if doctor_id:
                cur.execute(
                    "SELECT * FROM patients WHERE assigned_doctor_id = %s "
                    "ORDER BY created_at DESC",
                    (doctor_id,)
                )
            else:
                cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()


def get_patient_by_id(patient_id: int) -> dict | None:
    """Fetch a single patient row by primary key."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM patients WHERE id = %s LIMIT 1",
                (patient_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def create_patient(data: dict) -> int:
    """
    Insert a new patient record.
    data keys: name, age, gender, contact, blood_group,
               medical_history, assigned_doctor_id
    Returns the new patient's integer PK.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Generate a human-readable patient ID like PT-007
            cur.execute("SELECT COUNT(*) as cnt FROM patients")
            cnt = cur.fetchone()["cnt"]
            pid = f"PT-{cnt + 1:03d}"

            cur.execute(
                """INSERT INTO patients
                   (patient_id, name, age, gender, contact, blood_group,
                    medical_history, assigned_doctor_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    pid,
                    data["name"],
                    data["age"],
                    data["gender"],
                    data.get("contact", ""),
                    data.get("blood_group", ""),
                    data.get("medical_history", ""),
                    data.get("assigned_doctor_id"),
                )
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_patient(patient_id: int, data: dict) -> bool:
    """Update mutable fields of a patient record. Returns True on success."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE patients
                   SET name=%s, age=%s, gender=%s, contact=%s,
                       blood_group=%s, medical_history=%s, assigned_doctor_id=%s
                   WHERE id=%s""",
                (
                    data["name"],
                    data["age"],
                    data["gender"],
                    data.get("contact", ""),
                    data.get("blood_group", ""),
                    data.get("medical_history", ""),
                    data.get("assigned_doctor_id"),
                    patient_id,
                )
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_patient(patient_id: int) -> bool:
    """Delete a patient and cascade-remove their health records and alerts."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def search_patients(query: str) -> list:
    """Full-text search on name or patient_id."""
    like = f"%{query}%"
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM patients
                   WHERE name LIKE %s OR patient_id LIKE %s
                   ORDER BY name""",
                (like, like)
            )
            return cur.fetchall()
    finally:
        conn.close()
