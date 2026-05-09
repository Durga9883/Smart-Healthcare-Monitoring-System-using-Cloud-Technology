"""
models/__init__.py
Exports a helper to obtain a PyMySQL database connection from config.
All models import get_db() instead of managing connections themselves.
"""

import pymysql
import pymysql.cursors
from config import Config


def get_db():
    """
    Return a new PyMySQL connection using the project config.
    Each request/service call should open its own connection and
    close it when done (use try/finally or a context manager).
    """
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,   # rows as dicts
        autocommit=False,
    )
    return connection
