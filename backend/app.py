from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

DB_PATH = os.path.join("..", "database", "results.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            confidence_score INTEGER,
            knowledge_score INTEGER,
            final_score INTEGER,
            feedback TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/save-result", methods=["POST"])
def save_result():
    data = request.get_json()

    username = data.get("username", "Anonymous")
    confidence = int(data.get("confidence_score", 0))
    knowledge = int(data.get("knowledge_score", 0))
    final_score = int((confidence + knowledge) / 2)
    feedback = ", ".join(data.get("feedback", []))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO results (username, confidence_score, knowledge_score, final_score, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, confidence, knowledge, final_score, feedback, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({"message": "Result saved successfully", "final_score": final_score})

@app.route("/get-results", methods=["GET"])
def get_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, confidence_score, knowledge_score, final_score, feedback, created_at FROM results ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "username": row[0],
            "confidence_score": row[1],
            "knowledge_score": row[2],
            "final_score": row[3],
            "feedback": row[4],
            "created_at": row[5],
        })

    return jsonify(results)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
