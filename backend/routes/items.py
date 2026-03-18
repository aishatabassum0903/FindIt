from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

items_bp = Blueprint("items", __name__)

def get_cols():
    from app import items_col, users_col, notifs_col
    return items_col, users_col, notifs_col

def serialize_item(item):
    item["_id"] = str(item["_id"])
    if "postedBy" in item and isinstance(item["postedBy"], ObjectId):
        item["postedBy"] = str(item["postedBy"])
    if "createdAt" in item:
        item["createdAt"] = item["createdAt"].isoformat()
    return item

@items_bp.route("", methods=["GET"])
def get_items():
    items_col, _, _ = get_cols()
    item_type = request.args.get("type")          # lost / found
    category  = request.args.get("category")
    status    = request.args.get("status", "open")
    location  = request.args.get("location")
    page      = int(request.args.get("page", 1))
    limit     = int(request.args.get("limit", 12))
    skip      = (page - 1) * limit

    query = {}
    if item_type: query["type"]     = item_type
    if category:  query["category"] = category
    if status:    query["status"]   = status
    if location:  query["location"] = {"$regex": location, "$options": "i"}

    total = items_col.count_documents(query)
    items = list(items_col.find(query).sort("createdAt", -1).skip(skip).limit(limit))
    return jsonify({
        "items": [serialize_item(i) for i in items],
        "total": total,
        "page":  page,
        "pages": (total + limit - 1) // limit
    })

@items_bp.route("/search", methods=["GET"])
def search_items():
    items_col, _, _ = get_cols()
    q = request.args.get("q", "")
    if not q:
        return jsonify({"items": []})
    items = list(items_col.find(
        {"$text": {"$search": q}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(20))
    return jsonify({"items": [serialize_item(i) for i in items]})

@items_bp.route("/<item_id>", methods=["GET"])
def get_item(item_id):
    items_col, users_col, _ = get_cols()
    try:
        item = items_col.find_one({"_id": ObjectId(item_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Attach poster name
    if "postedBy" in item:
        user = users_col.find_one({"_id": item["postedBy"]}, {"name": 1, "department": 1})
        if user:
            item["posterName"] = user["name"]
            item["posterDept"] = user.get("department", "")

    return jsonify(serialize_item(item))

@items_bp.route("", methods=["POST"])
@jwt_required()
def create_item():
    items_col, _, notifs_col = get_cols()
    user_id = get_jwt_identity()
    data = request.get_json()

    required = ["type", "title", "category", "location", "date"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"{f} is required"}), 400

    item = {
        "type":        data["type"],
        "title":       data["title"],
        "description": data.get("description", ""),
        "category":    data["category"],
        "location":    data["location"],
        "date":        data["date"],
        "imageUrl":    data.get("imageUrl", ""),
        "hotspots":    data.get("hotspots", []),
        "color":       data.get("color", ""),
        "brand":       data.get("brand", ""),
        "size":        data.get("size", ""),
        "status":      "open",
        "postedBy":    ObjectId(user_id),
        "createdAt":   datetime.datetime.utcnow()
    }

    result = items_col.insert_one(item)
    item["_id"] = str(result.inserted_id)

    # Run matching in background (simple sync for now)
    try:
        from routes.matches import run_matching
        run_matching(str(result.inserted_id))
    except Exception as e:
        print("Matching error:", e)

    return jsonify({"message": "Item posted successfully", "item": serialize_item(item)}), 201

@items_bp.route("/<item_id>", methods=["PUT"])
@jwt_required()
def update_item(item_id):
    items_col, _, _ = get_cols()
    user_id = get_jwt_identity()
    try:
        item = items_col.find_one({"_id": ObjectId(item_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not item:
        return jsonify({"error": "Not found"}), 404
    if str(item["postedBy"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    allowed = ["title","description","category","location","date",
               "imageUrl","hotspots","color","brand","size","status"]
    update = {k: data[k] for k in allowed if k in data}
    items_col.update_one({"_id": ObjectId(item_id)}, {"$set": update})
    return jsonify({"message": "Item updated"})

@items_bp.route("/<item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    items_col, users_col, _ = get_cols()
    user_id = get_jwt_identity()
    try:
        item = items_col.find_one({"_id": ObjectId(item_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not item:
        return jsonify({"error": "Not found"}), 404

    # Allow owner or admin
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if str(item["postedBy"]) != user_id and user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    items_col.delete_one({"_id": ObjectId(item_id)})
    return jsonify({"message": "Item deleted"})

@items_bp.route("/stats/overview", methods=["GET"])
def get_stats():
    items_col, _, _ = get_cols()
    total_lost  = items_col.count_documents({"type": "lost"})
    total_found = items_col.count_documents({"type": "found"})
    resolved    = items_col.count_documents({"status": "resolved"})
    return jsonify({
        "totalLost":  total_lost,
        "totalFound": total_found,
        "resolved":   resolved
    })
