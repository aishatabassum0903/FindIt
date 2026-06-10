from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

admin_bp = Blueprint("admin", __name__)

def get_cols():
    from app import users_col, items_col, matches_col, claims_col, notifs_col
    return users_col, items_col, matches_col, claims_col, notifs_col

def is_admin(user_id):
    users_col, _, _, _, _ = get_cols()
    user = users_col.find_one({"_id": ObjectId(user_id)})
    return user and user.get("role") == "admin"

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def get_all_users():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    users_col, _, _, _, _ = get_cols()
    users = list(users_col.find({}, {"passwordHash": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
        if "createdAt" in u:
            u["createdAt"] = u["createdAt"].isoformat()
    return jsonify({"users": users, "total": len(users)})

@admin_bp.route("/items", methods=["GET"])
@jwt_required()
def get_all_items():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    _, items_col, _, _, _ = get_cols()
    items = list(items_col.find().sort("createdAt", -1))
    for i in items:
        i["_id"] = str(i["_id"])
        if "postedBy" in i:
            i["postedBy"] = str(i["postedBy"])
        if "createdAt" in i:
            i["createdAt"] = i["createdAt"].isoformat()
    return jsonify({"items": items, "total": len(items)})

@admin_bp.route("/items/<item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    _, items_col, _, _, _ = get_cols()
    items_col.delete_one({"_id": ObjectId(item_id)})
    return jsonify({"message": "Item deleted"})

@admin_bp.route("/users/<uid>", methods=["DELETE"])
@jwt_required()
def delete_user(uid):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    users_col, _, _, _, _ = get_cols()
    users_col.delete_one({"_id": ObjectId(uid)})
    return jsonify({"message": "User deleted"})

@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({"error": "Admin access required"}), 403
    users_col, items_col, matches_col, claims_col, _ = get_cols()
    total_users    = users_col.count_documents({})
    total_items    = items_col.count_documents({})
    total_lost     = items_col.count_documents({"type": "lost"})
    total_found    = items_col.count_documents({"type": "found"})
    total_resolved = items_col.count_documents({"status": "resolved"})
    total_matches  = matches_col.count_documents({})
    total_claims   = claims_col.count_documents({})
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
    categories = list(items_col.aggregate(pipeline))
    loc_pipeline = [{"$group": {"_id": "$location", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}, {"$limit": 5}]
    locations = list(items_col.aggregate(loc_pipeline))
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    daily_pipeline = [
        {"$match": {"createdAt": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_items = list(items_col.aggregate(daily_pipeline))
    return jsonify({
        "overview": {
            "totalUsers":    total_users,
            "totalItems":    total_items,
            "totalLost":     total_lost,
            "totalFound":    total_found,
            "totalResolved": total_resolved,
            "totalMatches":  total_matches,
            "totalClaims":   total_claims,
            "successRate":   round((total_resolved / total_items * 100) if total_items > 0 else 0, 1)
        },
        "categories": [{"name": c["_id"], "count": c["count"]} for c in categories if c["_id"]],
        "locations":  [{"name": l["_id"], "count": l["count"]} for l in locations if l["_id"]],
        "dailyItems": [{"date": d["_id"], "count": d["count"]} for d in daily_items]
    })