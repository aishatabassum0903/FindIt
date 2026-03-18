from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import bcrypt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

auth_bp = Blueprint("auth", __name__)

def get_db():
    from app import users_col
    return users_col

@auth_bp.route("/register", methods=["POST"])
def register():
    users_col = get_db()
    data = request.get_json()

    required = ["name", "studentId", "email", "password", "department"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if users_col.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    if users_col.find_one({"studentId": data["studentId"]}):
        return jsonify({"error": "Student ID already registered"}), 409

    hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

    user = {
        "name":       data["name"],
        "studentId":  data["studentId"],
        "email":      data["email"],
        "passwordHash": hashed.decode("utf-8"),
        "department": data["department"],
        "phone":      data.get("phone", ""),
        "role":       "student",
        "avatar":     "",
        "createdAt":  __import__("datetime").datetime.utcnow()
    }

    result = users_col.insert_one(user)
    token = create_access_token(
        identity=str(result.inserted_id),
        expires_delta=timedelta(hours=24)
    )

    return jsonify({
        "message": "Registered successfully",
        "token": token,
        "user": {
            "id":         str(result.inserted_id),
            "name":       user["name"],
            "email":      user["email"],
            "studentId":  user["studentId"],
            "department": user["department"],
            "role":       user["role"]
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    users_col = get_db()
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    user = users_col.find_one({"email": data["email"]})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(data["password"].encode("utf-8"), user["passwordHash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=timedelta(hours=24)
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id":         str(user["_id"]),
            "name":       user["name"],
            "email":      user["email"],
            "studentId":  user["studentId"],
            "department": user["department"],
            "role":       user["role"]
        }
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    from bson import ObjectId
    users_col = get_db()
    user_id = get_jwt_identity()
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id":         str(user["_id"]),
        "name":       user["name"],
        "email":      user["email"],
        "studentId":  user["studentId"],
        "department": user["department"],
        "phone":      user.get("phone",""),
        "role":       user["role"]
    })
