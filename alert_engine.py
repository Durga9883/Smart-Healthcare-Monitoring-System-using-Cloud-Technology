"""
services/alert_engine.py – Threshold-based Alert Detection
Analyses one set of vitals and returns a list of alert dicts.
Called by the simulator and by the /api/health POST endpoint.
"""

from models.health_record import insert_alert


# ── Thresholds ─────────────────────────────────────────────────────────────────
THRESHOLDS = {
    "temperature": {
        "critical": 103.0,   # °F
        "warning":  100.0,
        "message_critical": "CRITICAL: Dangerously High Fever Detected!",
        "message_warning":  "WARNING: High Fever Detected",
        "type":              "High Fever",
    },
    "oxygen_level": {
        "critical": 85.0,    # %
        "warning":  90.0,
        "message_critical": "CRITICAL: Life-Threatening Oxygen Deficiency!",
        "message_warning":  "WARNING: Low Oxygen Level Detected",
        "type":              "Low Oxygen",
        "direction": "low",  # alert when BELOW threshold
    },
    "heart_rate": {
        "critical": 140,     # bpm
        "warning":  120,
        "message_critical": "CRITICAL: Emergency — Extreme Tachycardia!",
        "message_warning":  "WARNING: Rapid Heart Rate Detected",
        "type":              "Rapid Heart Rate",
    },
    "blood_pressure": {
        "critical_sys": 160,
        "warning_sys":  140,
        "message_critical": "CRITICAL: Hypertensive Crisis Detected!",
        "message_warning":  "WARNING: High Blood Pressure",
        "type":              "High Blood Pressure",
    },
}


def evaluate(patient_id: int, temp: float, hr: int,
             spo2: float, bp_sys: int | None) -> tuple[str, list]:
    """
    Evaluate one set of vitals against all thresholds.

    Returns:
        status  – 'normal' | 'warning' | 'critical'
        alerts  – list of dicts describing each triggered alert
    """
    triggered = []
    worst_status = "normal"

    # ── Temperature ──────────────────────────────────────────────────────────
    t_cfg = THRESHOLDS["temperature"]
    if temp >= t_cfg["critical"]:
        triggered.append({
            "type": t_cfg["type"],
            "message": t_cfg["message_critical"],
            "severity": "critical",
        })
        worst_status = "critical"
    elif temp >= t_cfg["warning"]:
        triggered.append({
            "type": t_cfg["type"],
            "message": t_cfg["message_warning"],
            "severity": "warning",
        })
        if worst_status != "critical":
            worst_status = "warning"

    # ── Oxygen Level (alert when LOW) ────────────────────────────────────────
    o_cfg = THRESHOLDS["oxygen_level"]
    if spo2 <= o_cfg["critical"]:
        triggered.append({
            "type": o_cfg["type"],
            "message": o_cfg["message_critical"],
            "severity": "critical",
        })
        worst_status = "critical"
    elif spo2 <= o_cfg["warning"]:
        triggered.append({
            "type": o_cfg["type"],
            "message": o_cfg["message_warning"],
            "severity": "warning",
        })
        if worst_status != "critical":
            worst_status = "warning"

    # ── Heart Rate ───────────────────────────────────────────────────────────
    h_cfg = THRESHOLDS["heart_rate"]
    if hr >= h_cfg["critical"]:
        triggered.append({
            "type": h_cfg["type"],
            "message": h_cfg["message_critical"],
            "severity": "critical",
        })
        worst_status = "critical"
    elif hr >= h_cfg["warning"]:
        triggered.append({
            "type": h_cfg["type"],
            "message": h_cfg["message_warning"],
            "severity": "warning",
        })
        if worst_status != "critical":
            worst_status = "warning"

    # ── Blood Pressure ───────────────────────────────────────────────────────
    bp_cfg = THRESHOLDS["blood_pressure"]
    if bp_sys is not None:
        if bp_sys >= bp_cfg["critical_sys"]:
            triggered.append({
                "type": bp_cfg["type"],
                "message": bp_cfg["message_critical"],
                "severity": "critical",
            })
            worst_status = "critical"
        elif bp_sys >= bp_cfg["warning_sys"]:
            triggered.append({
                "type": bp_cfg["type"],
                "message": bp_cfg["message_warning"],
                "severity": "warning",
            })
            if worst_status != "critical":
                worst_status = "warning"

    # ── Persist each triggered alert to DB ───────────────────────────────────
    for alert in triggered:
        try:
            insert_alert(
                patient_id=patient_id,
                alert_type=alert["type"],
                message=alert["message"],
                severity=alert["severity"],
            )
        except Exception as e:
            print(f"[AlertEngine] Could not save alert: {e}")

    return worst_status, triggered
