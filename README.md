# 🔍 FindIt — College Lost & Found Portal

A complete web application for managing lost and found items on a college campus.

## Tech Stack
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Backend**: Python (Flask)
- **Database**: MongoDB
- **Image Storage**: Cloudinary (optional)

---

## 🚀 Setup Instructions

### Step 1 — Install Python dependencies
```bash
cd backend
python -m venv venv

# Activate (Windows):
venv\Scripts\activate

# Activate (Mac/Linux):
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2 — Configure environment
Edit the `.env` file in the root folder:
```
MONGO_URI=mongodb://localhost:27017/lost_and_found
JWT_SECRET_KEY=your-secret-key-here
CLOUDINARY_CLOUD_NAME=your_cloud_name    ← optional
CLOUDINARY_API_KEY=your_api_key          ← optional
CLOUDINARY_API_SECRET=your_api_secret   ← optional
```

### Step 3 — Start MongoDB
Make sure MongoDB is running locally, or use MongoDB Atlas (update MONGO_URI).

### Step 4 — Run the Flask backend
```bash
cd backend
python app.py
# Server runs at http://localhost:5000
```

### Step 5 — Open the frontend
Right-click `frontend/index.html` → **Open with Live Server**
- OR open it directly in a browser
- Frontend runs at http://localhost:5500 (Live Server) or file://

---

## 📁 Project Structure
```
college-lost-and-found/
├── backend/
│   ├── app.py               ← Main Flask app
│   ├── config.py            ← Configuration
│   ├── requirements.txt     ← Python packages
│   └── routes/
│       ├── auth.py          ← Register/Login
│       ├── items.py         ← CRUD for items
│       ├── matches.py       ← AI matching algorithm
│       ├── claims.py        ← Item claims
│       ├── notifs.py        ← Notifications
│       └── upload.py        ← Image upload
│
├── frontend/
│   ├── index.html           ← Landing page
│   ├── css/style.css        ← Main stylesheet
│   ├── js/
│   │   ├── api.js           ← All API calls
│   │   └── imagemapper.js   ← Image hotspot mapping
│   └── pages/
│       ├── login.html
│       ├── register.html
│       ├── report.html      ← Report lost/found item
│       ├── browse.html      ← Browse all items
│       ├── item.html        ← Item detail page
│       └── dashboard.html   ← User dashboard
│
└── .env                     ← Secret keys
```

---

## 🔑 Features
- ✅ User authentication (register/login with JWT)
- ✅ Report lost & found items
- ✅ **Image Mapping** — Click on images to pin & label distinctive features
- ✅ **AI Matching** — TF-IDF + Cosine Similarity auto-matches items
- ✅ Browse & search with filters
- ✅ Submit claims on items
- ✅ Real-time notifications
- ✅ User dashboard
- ✅ Fully responsive design

---

## 🧪 Test the API
Open Thunder Client in VS Code and test:
```
GET  http://localhost:5000/api/test
POST http://localhost:5000/api/auth/register
POST http://localhost:5000/api/auth/login
GET  http://localhost:5000/api/items
```
