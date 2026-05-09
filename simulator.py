"""
services/simulator.py – Patient Vitals Simulator
Generates realistic-looking (but simulated) health data for every patient
in the database. Runs in a background thread every N seconds.

Usage:
    from services.simulator import start_simulator
    start_simulator()   # call once at app startup
"""

import random
import threading
import time
import datetime

from models.patient import get_all_patients
from models.health_record import insert_record
from services.alert_engine import evaluate
from config import Config


# ── Realistic baseline ranges per reading ─────────────────────────────────────
# 90 % of readings are "normal"; 10 % drift into warning/critical territory.

def _random_vitals(patient_age: int) -> dict:
    """
    Generate one plausible vital-signs reading for a patient.
    Older patients have slightly wider variance.
    """
    age_factor = 1.0 + (patient_age - 40) * 0.005  # small age bias

    # Decide if this reading is an 'anomaly' (10 % chance)
    anomaly = random.random() < 0.10

    if anomaly:
        # Push at least one parameter into warning/critical range
        choice = random.choice(["temp", "hr", "spo2", "bp"])
        temp    = round(random.uniform(98.6, 99.5), 1)
        hr      = random.randint(60, 100)
        spo2    = round(random.uniform(93.0, 99.0), 1)
        bp_sys  = random.randint(110, 130)
        bp_dia  = random.randint(70, 85)

        if choice == "temp":
            temp = round(random.uniform(100.5, 105.0), 1)
        elif choice == "hr":
            hr = random.randint(121, 155)
        elif choice == "spo2":
            spo2 = round(random.uniform(80.0, 89.9), 1)
        elif choice == "bp":
            bp_sys = random.randint(141, 180)
            bp_dia = random.randint(90, 115)
    else:
        temp   = round(random.uniform(97.0, 99.5) * age_factor, 1)
        temp   = min(temp, 99.9)          # cap normal range
        hr     = int(random.gauss(72, 8) * age_factor)
        hr     = max(50, min(hr, 119))
        spo2   = round(random.uniform(95.0, 99.9), 1)
        bp_sys = random.randint(105, 135)
        bp_dia = random.randint(65, 85)

    return {
        "temperature": temp,
        "heart_rate":  hr,
        "oxygen_level": spo2,
        "blood_pressure_sys": bp_sys,
        "blood_pressure_dia": bp_dia,
    }


# ── Background simulation loop ────────────────────────────────────────────────

def _simulation_loop():
    interval = Config.SIMULATE_INTERVAL_SECONDS
    print(f"[Simulator] Started – generating vitals every {interval}s")

    while True:
        try:
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
            print(f"[Simulator] {datetime.datetime.now():%H:%M:%S} – "
                  f"Updated {len(patients)} patients")
        except Exception as exc:
            print(f"[Simulator] ERROR: {exc}")

        time.sleep(interval)


def start_simulator():
    """Launch the vitals simulator in a daemon thread."""
    t = threading.Thread(target=_simulation_loop, daemon=True, name="VitalsSimulator")
    t.start()
    return t
