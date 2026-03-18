from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import Config
import certifi

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY

CORS(app, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager(app)

# MongoDB connection with SSL fix
client = MongoClient(
    Config.MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = client["lost_and_found"]

# Collections
users_col   = db["users"]
items_col   = db["items"]
matches_col = db["matches"]
claims_col  = db["claims"]
notifs_col  = db["notifications"]

# Create indexes for fast search
try:
    items_col.create_index([("title", "text"), ("description", "text")])
except:
    pass

# Import and register routes
from routes.auth    import auth_bp
from routes.items   import items_bp
from routes.matches import matches_bp
from routes.claims  import claims_bp
from routes.notifs  import notifs_bp
from routes.upload  import upload_bp

app.register_blueprint(auth_bp,    url_prefix="/api/auth")
app.register_blueprint(items_bp,   url_prefix="/api/items")
app.register_blueprint(matches_bp, url_prefix="/api/matches")
app.register_blueprint(claims_bp,  url_prefix="/api/claims")
app.register_blueprint(notifs_bp,  url_prefix="/api/notifications")
app.register_blueprint(upload_bp,  url_prefix="/api/upload")

@app.route("/api/test")
def test():
    return {"message": "✅ Backend is working!", "status": "ok"}

if __name__ == "__main__":
    print("🚀 Server running at http://localhost:5000")
    app.run(debug=True, port=5000)