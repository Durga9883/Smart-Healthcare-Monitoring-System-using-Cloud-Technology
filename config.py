"""
config.py – Application & Database Configuration
Reads settings from .env (python-dotenv) so credentials never
live in source code. Change values in .env before running.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file in the project root
load_dotenv()


class Config:
    # ── Flask ────────────────────────────────────────────────────────────────
    SECRET_KEY      = os.getenv("SECRET_KEY",     "change-me-in-production")
    JWT_SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = False   # tokens don't auto-expire in dev

    # ── MySQL / PyMySQL ──────────────────────────────────────────────────────
    DB_HOST     = os.getenv("DB_HOST",     "localhost")
    DB_PORT     = int(os.getenv("DB_PORT", 3306))
    DB_USER     = os.getenv("DB_USER",     "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME     = os.getenv("DB_NAME",     "healthcare_db")

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS = ["*"]   # restrict to your domain in production

    # ── Simulator ────────────────────────────────────────────────────────────
    # How often (seconds) the background simulator generates new vitals
    SIMULATE_INTERVAL_SECONDS = 30
