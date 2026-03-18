from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

notifs_bp = Blueprint("notifs", __name__)

def get_col():
    from app import notifs_col
    return notifs_col

def serialize(n):
    n["_id"] = str(n["_id"])
    if "userId" in n and isinstance(n["userId"], ObjectId):
        n["userId"] = str(n["userId"])
    if "createdAt" in n:
        n["createdAt"] = n["createdAt"].isoformat()
    return n

@notifs_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    notifs_col = get_col()
    user_id = get_jwt_identity()
    notifs = list(notifs_col.find(
        {"userId": ObjectId(user_id)}
    ).sort("createdAt", -1).limit(20))
    unread = notifs_col.count_documents({"userId": ObjectId(user_id), "read": False})
    return jsonify({
        "notifications": [serialize(n) for n in notifs],
        "unread": unread
    })

@notifs_bp.route("/<notif_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notif_id):
    notifs_col = get_col()
    notifs_col.update_one({"_id": ObjectId(notif_id)}, {"$set": {"read": True}})
    return jsonify({"message": "Marked as read"})

@notifs_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    notifs_col = get_col()
    user_id = get_jwt_identity()
    notifs_col.update_many({"userId": ObjectId(user_id)}, {"$set": {"read": True}})
    return jsonify({"message": "All marked as read"})
