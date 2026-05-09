"""
models/health_record.py – Health vitals CRUD + alert queries
Stores and retrieves readings from health_records and alerts tables.
"""

from models import get_db


# ── Health Records ─────────────────────────────────────────────────────────────

def insert_record(patient_id: int, temp: float, hr: int,
                  spo2: float, bp_sys: int | None, bp_dia: int | None,
                  status: str) -> int:
    """Insert one vitals reading. Returns new record id."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO health_records
                   (patient_id, temperature, heart_rate, oxygen_level,
                    blood_pressure_sys, blood_pressure_dia, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (patient_id, temp, hr, spo2, bp_sys, bp_dia, status)
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_latest_record(patient_id: int) -> dict | None:
    """Return the most-recent vitals row for a patient."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM health_records
                   WHERE patient_id = %s
                   ORDER BY recorded_at DESC LIMIT 1""",
                (patient_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_history(patient_id: int, limit: int = 20) -> list:
    """Return the last `limit` vitals rows for a patient (newest first)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM health_records
                   WHERE patient_id = %s
                   ORDER BY recorded_at DESC LIMIT %s""",
                (patient_id, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_all_latest() -> list:
    """
    Return the single most-recent health record for every patient.
    Used by the dashboard to display all patient status cards.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT hr.*, p.name, p.patient_id AS pid, p.age, p.gender
                   FROM health_records hr
                   INNER JOIN patients p ON hr.patient_id = p.id
                   INNER JOIN (
                       SELECT patient_id, MAX(recorded_at) AS latest
                       FROM health_records
                       GROUP BY patient_id
                   ) sub ON hr.patient_id = sub.patient_id
                          AND hr.recorded_at = sub.latest
                   ORDER BY hr.status DESC, p.name"""
            )
            return cur.fetchall()
    finally:
        conn.close()


# ── Alerts ─────────────────────────────────────────────────────────────────────

def insert_alert(patient_id: int, alert_type: str,
                 message: str, severity: str) -> int:
    """Insert an alert row. Returns new alert id."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO alerts
                   (patient_id, alert_type, message, severity)
                   VALUES (%s, %s, %s, %s)""",
                (patient_id, alert_type, message, severity)
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_active_alerts(limit: int = 50) -> list:
    """Return unresolved alerts, newest first, joined with patient name."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT a.*, p.name AS patient_name, p.patient_id AS pid
                   FROM alerts a
                   JOIN patients p ON a.patient_id = p.id
                   WHERE a.is_resolved = FALSE
                   ORDER BY a.created_at DESC LIMIT %s""",
                (limit,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_alerts_for_patient(patient_id: int) -> list:
    """All alerts (resolved and not) for a specific patient."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM alerts
                   WHERE patient_id = %s
                   ORDER BY created_at DESC""",
                (patient_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def resolve_alert(alert_id: int) -> bool:
    """Mark an alert as resolved. Returns True if a row was updated."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE alerts SET is_resolved = TRUE WHERE id = %s",
                (alert_id,)
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_dashboard_stats() -> dict:
    """
    Single-query aggregate for the dashboard summary card row:
    total patients, critical count, active alerts count, normal count.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM patients")
            total = cur.fetchone()["total"]

            # latest status per patient
            cur.execute(
                """SELECT status, COUNT(*) AS cnt
                   FROM (
                       SELECT DISTINCT patient_id,
                              FIRST_VALUE(status) OVER (
                                  PARTITION BY patient_id
                                  ORDER BY recorded_at DESC
                              ) AS status
                       FROM health_records
                   ) t
                   GROUP BY status"""
            )
            status_map = {r["status"]: r["cnt"] for r in cur.fetchall()}

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM alerts WHERE is_resolved = FALSE"
            )
            active_alerts = cur.fetchone()["cnt"]

        return {
            "total_patients": total,
            "critical": status_map.get("critical", 0),
            "warning":  status_map.get("warning",  0),
            "normal":   status_map.get("normal",   0),
            "active_alerts": active_alerts,
        }
    finally:
        conn.close()
