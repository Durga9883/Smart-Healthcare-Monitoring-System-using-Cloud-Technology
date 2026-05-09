"""
app.py – Smart Healthcare Monitoring System
Flask application factory + entry-point.

Run locally:
    python app.py

Production (Gunicorn on AWS EC2):
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

from config import Config
from routes.auth      import auth_bp
from routes.patients  import patients_bp
from routes.health    import health_bp
from routes.dashboard import dashboard_bp


def create_app() -> Flask:
    """Application factory – creates and configures the Flask app."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Load config ──────────────────────────────────────────────────────────
    app.config["SECRET_KEY"]     = Config.SECRET_KEY
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

    # ── Extensions ───────────────────────────────────────────────────────────
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # ── Register Blueprints ──────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)

    # ── Serve HTML pages (SPA-style) ─────────────────────────────────────────
    @app.route("/")
    def index():
        return send_from_directory("templates", "login.html")

    @app.route("/dashboard")
    def dashboard():
        return send_from_directory("templates", "dashboard.html")

    @app.route("/patients")
    def patients_page():
        return send_from_directory("templates", "patients.html")

    @app.route("/patients/<int:patient_id>")
    def patient_detail_page(patient_id):
        return send_from_directory("templates", "patient_detail.html")

    @app.route("/alerts")
    def alerts_page():
        return send_from_directory("templates", "alerts.html")

    # ── Global error handlers ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error."}), 500

    return app


# ── Entry-point ───────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    # Start the background vitals simulator before serving requests
    from services.simulator import start_simulator
    start_simulator()

    print("=" * 60)
    print("  Smart Healthcare Monitoring System")
    print("  Running at http://127.0.0.1:5000")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=Config.FLASK_DEBUG if hasattr(Config, "FLASK_DEBUG") else True)
