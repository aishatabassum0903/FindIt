from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

claims_bp = Blueprint("claims", __name__)

def get_cols():
    from app import claims_col, items_col, notifs_col
    return claims_col, items_col, notifs_col

def serialize(doc):
    doc["_id"] = str(doc["_id"])
    for k in ["itemId","claimedBy"]:
        if k in doc and isinstance(doc[k], ObjectId):
            doc[k] = str(doc[k])
    if "createdAt" in doc:
        doc["createdAt"] = doc["createdAt"].isoformat()
    return doc

@claims_bp.route("", methods=["POST"])
@jwt_required()
def submit_claim():
    claims_col, items_col, notifs_col = get_cols()
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("itemId"):
        return jsonify({"error": "itemId required"}), 400

    try:
        item = items_col.find_one({"_id": ObjectId(data["itemId"])})
    except:
        return jsonify({"error": "Invalid itemId"}), 400

    if not item:
        return jsonify({"error": "Item not found"}), 404

    if str(item["postedBy"]) == user_id:
        return jsonify({"error": "Cannot claim your own item"}), 400

    existing = claims_col.find_one({
        "itemId":    ObjectId(data["itemId"]),
        "claimedBy": ObjectId(user_id)
    })
    if existing:
        return jsonify({"error": "Already submitted a claim"}), 409

    # Check hotspot keyword matches
    claimant_desc = data.get("description","").lower()
    hotspot_matches = 0
    for h in item.get("hotspots",[]):
        if h.get("label","").lower() in claimant_desc:
            hotspot_matches += 1

    claim = {
        "itemId":          ObjectId(data["itemId"]),
        "claimedBy":       ObjectId(user_id),
        "description":     data.get("description",""),
        "imageUrl":        data.get("imageUrl",""),
        "hotspotMatchCount": hotspot_matches,
        "status":          "pending",
        "createdAt":       datetime.datetime.utcnow()
    }
    result = claims_col.insert_one(claim)

    # Notify item owner
    notif = {
        "userId":    item["postedBy"],
        "message":   f"Someone submitted a claim on your item: '{item['title']}'",
        "itemId":    str(item["_id"]),
        "read":      False,
        "createdAt": datetime.datetime.utcnow()
    }
    notifs_col.insert_one(notif)

    claim["_id"] = str(result.inserted_id)
    return jsonify({"message": "Claim submitted", "hotspotMatches": hotspot_matches, "claim": serialize(claim)}), 201


@claims_bp.route("/<item_id>", methods=["GET"])
@jwt_required()
def get_claims(item_id):
    claims_col, items_col, _ = get_cols()
    user_id = get_jwt_identity()

    try:
        item = items_col.find_one({"_id": ObjectId(item_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not item:
        return jsonify({"error": "Item not found"}), 404

    if str(item["postedBy"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    claims = list(claims_col.find({"itemId": ObjectId(item_id)}).sort("createdAt", -1))
    return jsonify({"claims": [serialize(c) for c in claims]})


@claims_bp.route("/<claim_id>/status", methods=["PUT"])
@jwt_required()
def update_claim_status(claim_id):
    claims_col, items_col, notifs_col = get_cols()
    user_id = get_jwt_identity()
    data = request.get_json()
    status = data.get("status")

    if status not in ["approved","rejected"]:
        return jsonify({"error": "Status must be approved or rejected"}), 400

    try:
        claim = claims_col.find_one({"_id": ObjectId(claim_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not claim:
        return jsonify({"error": "Claim not found"}), 404

    item = items_col.find_one({"_id": claim["itemId"]})
    if not item or str(item["postedBy"]) != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    claims_col.update_one({"_id": ObjectId(claim_id)}, {"$set": {"status": status}})

    if status == "approved":
        items_col.update_one({"_id": claim["itemId"]}, {"$set": {"status": "resolved"}})

    notif = {
        "userId":    claim["claimedBy"],
        "message":   f"Your claim was {status} for item: '{item['title']}'",
        "itemId":    str(item["_id"]),
        "read":      False,
        "createdAt": datetime.datetime.utcnow()
    }
    notifs_col.insert_one(notif)

    return jsonify({"message": f"Claim {status}"})
