from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import base64, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("", methods=["POST"])
@jwt_required()
def upload_image():
    """
    Accepts base64 image or file upload.
    Uses Cloudinary if configured, otherwise returns placeholder.
    """
    try:
        from config import Config
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET
        )

        if "file" in request.files:
            file = request.files["file"]
            allowed = {"image/jpeg","image/png","image/gif","image/webp"}
            if file.content_type not in allowed:
                return jsonify({"error": "Only image files allowed"}), 400

            result = cloudinary.uploader.upload(
                file,
                folder="lost_and_found",
                transformation=[{"width":800,"height":600,"crop":"limit"}]
            )
            return jsonify({"url": result["secure_url"]})

        data = request.get_json()
        if data and data.get("base64"):
            result = cloudinary.uploader.upload(
                data["base64"],
                folder="lost_and_found"
            )
            return jsonify({"url": result["secure_url"]})

        return jsonify({"error": "No file provided"}), 400

    except Exception as e:
        # If Cloudinary not configured, return a placeholder
        print(f"Upload error (Cloudinary not configured?): {e}")
        return jsonify({
            "url": "https://placehold.co/400x300?text=Item+Image",
            "warning": "Cloudinary not configured. Using placeholder."
        })
