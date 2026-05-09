"""
routes/auth.py – Authentication Endpoints
POST /api/auth/login   → validate credentials, return JWT
POST /api/auth/logout  → client-side token drop (stateless)
GET  /api/auth/me      → return current user info
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
import models.user as user_model

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT token.
    Body JSON: { "username": "...", "password": "..." }
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    # Find the user in DB
    user = user_model.find_by_username(username)
    if not user:
        return jsonify({"error": "Invalid credentials."}), 401

    # Verify password hash
    if not user_model.check_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials."}), 401

    # Create JWT with user id as identity; embed role in additional claims
    token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"]}
    )

    return jsonify({
        "token": token,
        "user": {
            "id":        user["id"],
            "username":  user["username"],
            "role":      user["role"],
            "full_name": user["full_name"],
            "email":     user["email"],
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Stateless logout – the client simply discards the token.
    In production, use a token blocklist for true invalidation.
    """
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the currently authenticated user's profile."""
    user_id = int(get_jwt_identity())
    user = user_model.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user), 200
