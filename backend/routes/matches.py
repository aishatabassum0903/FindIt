from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import datetime, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

matches_bp = Blueprint("matches", __name__)

def get_cols():
    from app import items_col, matches_col, notifs_col
    return items_col, matches_col, notifs_col

def run_matching(new_item_id):
    """Run TF-IDF matching when a new item is posted."""
    items_col, matches_col, notifs_col = get_cols()

    try:
        new_item = items_col.find_one({"_id": ObjectId(new_item_id)})
    except:
        return
    if not new_item:
        return

    # Find opposite type items
    opposite_type = "found" if new_item["type"] == "lost" else "lost"
    candidates = list(items_col.find({"type": opposite_type, "status": "open"}))

    if not candidates:
        return

    new_text = f"{new_item.get('title','')} {new_item.get('description','')}"
    candidate_texts = [f"{c.get('title','')} {c.get('description','')}" for c in candidates]

    all_texts = [new_text] + candidate_texts

    try:
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
    except:
        return

    for idx, candidate in enumerate(candidates):
        text_sim = float(similarities[idx])

        # Category match bonus
        cat_bonus = 0.20 if new_item.get("category") == candidate.get("category") else 0

        # Location match bonus
        loc_bonus = 0.0
        new_loc  = new_item.get("location","").lower()
        cand_loc = candidate.get("location","").lower()
        if new_loc and cand_loc and (new_loc in cand_loc or cand_loc in new_loc):
            loc_bonus = 0.15

        # Date proximity bonus
        date_bonus = 0.0
        try:
            d1 = datetime.datetime.fromisoformat(new_item.get("date",""))
            d2 = datetime.datetime.fromisoformat(candidate.get("date",""))
            if abs((d1 - d2).days) <= 3:
                date_bonus = 0.10
        except:
            pass

        # Hotspot keyword overlap bonus
        hotspot_bonus = 0.0
        new_labels  = " ".join([h.get("label","") for h in new_item.get("hotspots",[])])
        cand_labels = " ".join([h.get("label","") for h in candidate.get("hotspots",[])])
        if new_labels and cand_labels:
            new_words  = set(new_labels.lower().split())
            cand_words = set(cand_labels.lower().split())
            overlap = len(new_words & cand_words)
            hotspot_bonus = min(overlap * 0.05, 0.15)

        score = (text_sim * 0.45) + cat_bonus + loc_bonus + date_bonus + hotspot_bonus
        score = min(score, 1.0)

        if score < 0.30:
            continue

        # Determine lost/found IDs correctly
        if new_item["type"] == "lost":
            lost_id  = new_item["_id"]
            found_id = candidate["_id"]
        else:
            lost_id  = candidate["_id"]
            found_id = new_item["_id"]

        # Avoid duplicate matches
        existing = matches_col.find_one({
            "lostItemId":  lost_id,
            "foundItemId": found_id
        })
        if existing:
            continue

        match = {
            "lostItemId":  lost_id,
            "foundItemId": found_id,
            "score":       round(score, 3),
            "status":      "pending",
            "createdAt":   datetime.datetime.utcnow()
        }
        match_result = matches_col.insert_one(match)

        # Notify both users if score is high enough
        if score >= 0.55:
            for item_obj, other_obj in [(new_item, candidate), (candidate, new_item)]:
                notif = {
                    "userId":    item_obj["postedBy"],
                    "message":   f"A potential match found for your {item_obj['type']} item: '{item_obj['title']}'",
                    "itemId":    str(item_obj["_id"]),
                    "matchId":   str(match_result.inserted_id),
                    "matchScore": round(score, 3),
                    "read":      False,
                    "createdAt": datetime.datetime.utcnow()
                }
                notifs_col.insert_one(notif)

    print(f"✅ Matching complete for item {new_item_id}")


@matches_bp.route("/<item_id>", methods=["GET"])
@jwt_required()
def get_matches(item_id):
    items_col, matches_col, _ = get_cols()
    try:
        oid = ObjectId(item_id)
    except:
        return jsonify({"error": "Invalid ID"}), 400

    matches = list(matches_col.find({
        "$or": [{"lostItemId": oid}, {"foundItemId": oid}]
    }).sort("score", -1).limit(10))

    result = []
    for m in matches:
        other_id = m["foundItemId"] if str(m["lostItemId"]) == item_id else m["lostItemId"]
        other_item = items_col.find_one({"_id": other_id})
        if other_item:
            result.append({
                "matchId":   str(m["_id"]),
                "score":     m["score"],
                "status":    m["status"],
                "item": {
                    "_id":      str(other_item["_id"]),
                    "title":    other_item["title"],
                    "type":     other_item["type"],
                    "imageUrl": other_item.get("imageUrl",""),
                    "category": other_item.get("category",""),
                    "location": other_item.get("location",""),
                    "date":     other_item.get("date","")
                }
            })

    return jsonify({"matches": result})


@matches_bp.route("/run/<item_id>", methods=["POST"])
@jwt_required()
def manual_match(item_id):
    run_matching(item_id)
    return jsonify({"message": "Matching complete"})
