"""
seed_data.py – Database Seeder
Creates default admin/doctor users and 10 realistic patient records
with initial health readings. Run ONCE after setting up the database.

Usage:
    python seed_data.py
"""

import sys
import pymysql
from config import Config
from models.user import hash_password
from services.alert_engine import evaluate
import random
import datetime


# ── Sample Dataset ────────────────────────────────────────────────────────────

USERS = [
    # (username, password, role, email, full_name)
    ("admin",    "admin123",   "admin",   "admin@healthcare.com",     "System Administrator"),
    ("dr_smith", "doctor123",  "doctor",  "smith@healthcare.com",     "Dr. Robert Smith"),
    ("dr_patel", "doctor123",  "doctor",  "patel@healthcare.com",     "Dr. Priya Patel"),
]

PATIENTS = [
    # (name, age, gender, contact, blood_group, medical_history)
    ("Ananya Sharma",    62, "Female", "9876543210", "A+",  "Type 2 Diabetes, Hypertension"),
    ("Rajesh Kumar",     55, "Male",   "9876543211", "B+",  "Chronic Kidney Disease"),
    ("Meena Iyer",       70, "Female", "9876543212", "O-",  "Arthritis, Hypertension"),
    ("Vikram Singh",     45, "Male",   "9876543213", "AB+", "None"),
    ("Sunita Verma",     68, "Female", "9876543214", "A-",  "Diabetes, Heart Disease"),
    ("Arjun Nair",       38, "Male",   "9876543215", "B-",  "Asthma"),
    ("Lakshmi Pillai",   74, "Female", "9876543216", "O+",  "Osteoporosis, COPD"),
    ("Mohammed Khan",    50, "Male",   "9876543217", "A+",  "Hypertension"),
    ("Pooja Desai",      29, "Female", "9876543218", "B+",  "None"),
    ("Ravi Chandran",    58, "Male",   "9876543219", "AB-", "Type 1 Diabetes"),
]

# Initial vitals (one per patient) – a mix of normal, warning, critical
INITIAL_VITALS = [
    # (temp_F, heart_rate, spo2, bp_sys, bp_dia)
    (101.5, 88,  95.2, 142, 90),   # Ananya – fever + hypertension warning
    (98.6,  118, 91.0, 130, 82),   # Rajesh – borderline heart rate
    (103.2, 92,  84.5, 155, 98),   # Meena – CRITICAL (fever + O2 + BP)
    (98.2,  72,  97.8, 118, 76),   # Vikram – normal
    (102.0, 125, 88.0, 160, 100),  # Sunita – CRITICAL multiple
    (99.1,  96,  94.5, 125, 80),   # Arjun – normal
    (100.8, 88,  87.5, 148, 92),   # Lakshmi – warning O2 + BP
    (98.9,  82,  96.0, 138, 86),   # Mohammed – normal
    (98.4,  68,  98.5, 112, 72),   # Pooja – normal
    (101.0, 78,  93.0, 135, 84),   # Ravi – mild fever warning
]


def seed():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

    try:
        with conn.cursor() as cur:
            # ── Seed Users ───────────────────────────────────────────────────
            print("Seeding users …")
            for username, password, role, email, full_name in USERS:
                cur.execute("SELECT id FROM users WHERE username=%s", (username,))
                if cur.fetchone():
                    print(f"  [SKIP] User '{username}' already exists.")
                    continue
                cur.execute(
                    """INSERT INTO users (username, password_hash, role, email, full_name)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (username, hash_password(password), role, email, full_name)
                )
                print(f"  [OK]   Created user '{username}' ({role})")

            conn.commit()

            # Get doctor IDs for assignment
            cur.execute("SELECT id FROM users WHERE role='doctor' LIMIT 2")
            doctors = [r["id"] for r in cur.fetchall()]
            if not doctors:
                doctors = [None, None]

            # ── Seed Patients ────────────────────────────────────────────────
            print("\nSeeding patients …")
            patient_ids = []
            for idx, (name, age, gender, contact, blood_group, history) in enumerate(PATIENTS):
                cur.execute("SELECT id FROM patients WHERE name=%s", (name,))
                existing = cur.fetchone()
                if existing:
                    print(f"  [SKIP] Patient '{name}' already exists.")
                    patient_ids.append(existing["id"])
                    continue

                pid     = f"PT-{idx+1:03d}"
                doc_id  = doctors[idx % len(doctors)] if doctors else None
                cur.execute(
                    """INSERT INTO patients
                       (patient_id, name, age, gender, contact, blood_group,
                        medical_history, assigned_doctor_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (pid, name, age, gender, contact, blood_group, history, doc_id)
                )
                new_id = cur.lastrowid
                patient_ids.append(new_id)
                print(f"  [OK]   Created patient {pid} – {name}")

            conn.commit()

            # ── Seed Health Records (initial + 10 historical readings each) ──
            print("\nSeeding health records …")
            for idx, pid in enumerate(patient_ids):
                if pid is None:
                    continue

                temp, hr, spo2, bp_sys, bp_dia = INITIAL_VITALS[idx]

                # Determine status via alert engine (also writes alerts to DB)
                status, _ = evaluate(
                    patient_id=pid,
                    temp=temp, hr=hr, spo2=spo2, bp_sys=bp_sys
                )

                cur.execute(
                    """INSERT INTO health_records
                       (patient_id, temperature, heart_rate, oxygen_level,
                        blood_pressure_sys, blood_pressure_dia, status)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (pid, temp, hr, spo2, bp_sys, bp_dia, status)
                )

                # Generate 9 historical readings spread over the last 24 h
                for h in range(1, 10):
                    hist_temp  = round(temp   + random.uniform(-1.5, 1.5), 1)
                    hist_hr    = hr   + random.randint(-15, 15)
                    hist_spo2  = round(spo2   + random.uniform(-3.0, 3.0), 1)
                    hist_bp_s  = bp_sys + random.randint(-15, 15)
                    hist_bp_d  = bp_dia + random.randint(-10, 10)
                    hist_time  = datetime.datetime.now() - datetime.timedelta(hours=h*2)
                    hist_status, _ = evaluate(
                        patient_id=pid,
                        temp=hist_temp, hr=hist_hr,
                        spo2=hist_spo2, bp_sys=hist_bp_s
                    )
                    cur.execute(
                        """INSERT INTO health_records
                           (patient_id, temperature, heart_rate, oxygen_level,
                            blood_pressure_sys, blood_pressure_dia, status, recorded_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (pid, hist_temp, hist_hr, hist_spo2,
                         hist_bp_s, hist_bp_d, hist_status, hist_time)
                    )

                conn.commit()
                print(f"  [OK]   10 records seeded for patient id={pid}")

        print("\n[OK] Database seeded successfully!")
        print("\nDefault Login Credentials:")
        print("  Admin  : admin / admin123")
        print("  Doctor : dr_smith / doctor123")
        print("  Doctor : dr_patel / doctor123")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAIL] Seeding failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
