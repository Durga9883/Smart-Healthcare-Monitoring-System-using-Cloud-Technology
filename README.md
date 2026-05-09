# Smart Healthcare Monitoring System

A **cloud-ready, full-stack** patient monitoring platform built with Python Flask, MySQL, and a dark-theme Hospital UI.

---

## 🚀 Quick Start (Local)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL database
```bash
mysql -u root -p < schema.sql
```

### 3. Configure environment
Edit `.env` with your MySQL credentials:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=healthcare_db
```

### 4. Seed the database (10 patients + sample data)
```bash
python seed_data.py
```

### 5. Run the application
```bash
python app.py
```

Open: **http://localhost:5000**

### Default Login Credentials
| Role   | Username   | Password    |
|--------|-----------|-------------|
| Admin  | `admin`    | `admin123`  |
| Doctor | `dr_smith` | `doctor123` |
| Doctor | `dr_patel` | `doctor123` |

---

## 📁 Folder Structure

```
Cloud-Based Healthcare Monitoring System/
├── app.py              ← Flask entry point
├── config.py           ← All settings (reads .env)
├── schema.sql          ← MySQL DDL
├── seed_data.py        ← Sample data seeder
├── requirements.txt
├── .env                ← DB credentials (never commit!)
├── models/             ← Database access layer
│   ├── user.py
│   ├── patient.py
│   └── health_record.py
├── routes/             ← REST API blueprints
│   ├── auth.py
│   ├── patients.py
│   ├── health.py
│   └── dashboard.py
├── services/           ← Business logic
│   ├── alert_engine.py ← Threshold detection
│   └── simulator.py    ← Background vitals simulator
├── templates/          ← HTML pages
│   ├── login.html
│   ├── dashboard.html
│   ├── patients.html
│   ├── patient_detail.html
│   └── alerts.html
└── static/
    ├── css/
    │   ├── main.css    ← Full design system
    │   └── auth.css    ← Login page styles
    └── js/
        ├── auth.js     ← JWT + shared helpers
        ├── dashboard.js
        ├── patients.js
        ├── health.js
        └── alerts.js
```

---

## 🏥 Alert Thresholds

| Vital | Warning | Critical |
|-------|---------|----------|
| Temperature | > 100°F | > 103°F |
| Oxygen Level | < 90% | < 85% |
| Heart Rate | > 120 bpm | > 140 bpm |
| Blood Pressure | > 140 mmHg | > 160 mmHg |

---

## ☁️ AWS Free Tier Deployment

### Services Used (All Free Tier)
| Service | Usage | Free Tier |
|---------|-------|-----------|
| EC2 t2.micro | Flask + Gunicorn | 750 hrs/month |
| RDS db.t3.micro | MySQL 8 | 750 hrs/month |
| S3 | Reports/backups | 5 GB |
| Elastic IP | Static IP | 1 free if attached |

### Step-by-Step

**1. Launch EC2 (Ubuntu 22.04 LTS, t2.micro)**
```bash
# On your EC2 instance:
sudo apt update && sudo apt install python3-pip python3-venv nginx git -y
```

**2. Clone and set up project**
```bash
git clone <your-repo> /home/ubuntu/healthcare
cd /home/ubuntu/healthcare
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

**3. Create RDS MySQL (db.t3.micro, Free Tier)**
- Engine: MySQL 8.0
- Template: Free Tier
- Set DB name: `healthcare_db`
- Update `.env` with RDS endpoint

**4. Run schema and seed**
```bash
mysql -h <RDS-endpoint> -u admin -p < schema.sql
python seed_data.py
```

**5. Run with Gunicorn**
```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

**6. Configure Nginx reverse proxy**
```nginx
server {
    listen 80;
    server_name your-ec2-public-ip;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
```bash
sudo systemctl restart nginx
```

**7. EC2 Security Group — open ports**
- Port 22  (SSH)
- Port 80  (HTTP)
- Port 5000 (optional, for direct access)

---

## 📋 API Routes Summary

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/auth/login` | Login → JWT token |
| GET  | `/api/auth/me` | Current user info |
| GET  | `/api/patients` | List all patients |
| POST | `/api/patients` | Add patient |
| GET  | `/api/patients/<id>` | Get patient |
| PUT  | `/api/patients/<id>` | Update patient |
| DELETE | `/api/patients/<id>` | Delete patient |
| GET  | `/api/health/<id>` | Latest vitals |
| GET  | `/api/health/<id>/history` | Vitals history |
| POST | `/api/health/simulate` | Trigger simulation |
| GET  | `/api/alerts` | Active alerts |
| PUT  | `/api/alerts/<id>/resolve` | Resolve alert |
| GET  | `/api/dashboard/stats` | Summary statistics |
| GET  | `/api/dashboard/all-vitals` | Latest vitals per patient |
