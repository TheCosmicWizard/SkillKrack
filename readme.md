Got it ✅
Here’s a **clear README.md** for your project so others (and you) can set it up easily.

---

# 📘 Interview Prep AI — Prototype

A simple full-stack project to help users practice for interviews.
It analyzes **facial confidence** (camera) and **speech knowledge** (audio), then gives feedback and stores results.

---

## 📂 Project Structure

```
backend/       → Flask backend (API + SQLite)
database/      → SQLite database file (results.db created automatically)
frontend/      → Static HTML, CSS, JS (UI for camera + audio)
model/         → (optional) ML models (DeepFace, Whisper, NLP) — not implemented yet
```

---

## 🚀 Features

- 🎥 **Facial Expression Capture** → maps emotions to confidence score
- 🎤 **Speech Recording** → converts speech to text & evaluates knowledge score
- 📊 **Scoring System** → final score = average(confidence, knowledge)
- 💾 **Backend (Flask + SQLite)** → saves user test results with feedback
- 📜 **History API** → fetch all previous results

---

## ⚙️ Installation & Setup

### 1️⃣ Clone repo

```bash
git clone https://github.com/yourname/interview-prep-ai.git
cd interview-prep-ai
```

### 2️⃣ Backend Setup

Go to backend folder and install requirements:

```bash
cd backend
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install flask
```

Run server:

```bash
python app.py
```

- Server runs on: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**
- It will auto-create `database/results.db`

### 3️⃣ Frontend Setup

No build tools needed.
Just open `frontend/index.html` in your browser.

To connect with backend:

- When saving scores, frontend will call:

  - `POST http://127.0.0.1:5000/save-result`
  - `GET http://127.0.0.1:5000/get-results`

---

## 🗂️ API Endpoints

### `POST /save-result`

Save a user’s test result.
**Request (JSON)**:

```json
{
  "username": "John",
  "confidence_score": 80,
  "knowledge_score": 70,
  "feedback": ["Good eye contact", "Improve clarity"]
}
```

**Response:**

```json
{ "message": "Result saved successfully", "final_score": 75 }
```

---

### `GET /get-results`

Fetch all saved results.
**Response:**

```json
[
  {
    "username": "John",
    "confidence_score": 80,
    "knowledge_score": 70,
    "final_score": 75,
    "feedback": "Good eye contact, Improve clarity",
    "created_at": "2025-09-15T14:00:00"
  }
]
```

---

## 🖥️ Screenshots (Prototype)

- **Frontend App (index.html)**
  🎥 Camera preview + record button
  🎤 Audio recorder with playback
  📊 Feedback summary

- **Backend**
  SQLite database saves results like this:

  | id  | username | confidence_score | knowledge_score | final_score | feedback | created_at |
  | --- | -------- | ---------------- | --------------- | ----------- | -------- | ---------- |

---

## 🔮 Next Steps (Improvements)

- Integrate **DeepFace / MediaPipe** for real emotion → confidence analysis
- Use **Whisper API** for speech-to-text
- Add **NLP model** to check relevance & depth of answers
- Deploy backend on **Render/Heroku** and serve frontend from **Netlify/Vercel**

---

## 👨‍💻 Author

Built for educational purposes — interview skill practice tool.

---

Would you like me to **add a section in README explaining how to view past results inside the frontend** (by calling `/get-results` and rendering a table), or keep README focused on backend + setup?
