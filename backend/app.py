"""
AI Chatbot for College Student Assistance - Backend
Flask REST API with scikit-learn TF-IDF matching over knowledge base,
and SQLite logging/storage.

Run:
    python database.py
    python app.py

The Web Application will be available at http://127.0.0.1:5000 (or PORT env var)
"""

import json
import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")
DB_PATH = os.path.join(BASE_DIR, "chatbot.db")

app = Flask(__name__)
CORS(app)  # allow CORS for standalone frontend instances


# ---------------------------------------------------------------------------
# Knowledge Base & scikit-learn TF-IDF Model
# ---------------------------------------------------------------------------

def load_knowledge_base():
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


KNOWLEDGE_BASE = load_knowledge_base()

STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "do", "does", "did", "i", "me",
    "my", "you", "your", "of", "for", "to", "in", "on", "at", "and", "or",
    "what", "when", "where", "how", "can", "could", "please", "tell",
    "about", "will", "be", "it", "this", "that", "with", "know"
}


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    return tokens


def init_tfidf_model():
    corpus = []
    for entry in KNOWLEDGE_BASE:
        kw_str = " ".join(entry.get("keywords", []))
        text = f"{entry.get('question', '')} {kw_str} {entry.get('category', '')}"
        corpus.append(text)

    if corpus:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vec.fit_transform(corpus)
        return vec, matrix
    return None, None


vectorizer, tfidf_matrix = init_tfidf_model()


def find_best_match(user_message):
    """Hybrid matcher using scikit-learn TF-IDF Cosine Similarity and keyword scoring."""
    message_lower = user_message.lower().strip()
    message_tokens = set(tokenize(user_message))

    # 1. Check exact/high-confidence keyword matches
    best_kw_entry = None
    best_kw_score = 0
    for entry in KNOWLEDGE_BASE:
        score = 0
        for kw in entry.get("keywords", []):
            if kw.lower() in message_lower:
                score += 3
        question_tokens = set(tokenize(entry.get("question", "")))
        score += len(message_tokens & question_tokens)

        if score > best_kw_score:
            best_kw_score = score
            best_kw_entry = entry

    if best_kw_score >= 6:
        return best_kw_entry, best_kw_score

    # 2. scikit-learn TF-IDF cosine similarity
    if vectorizer is not None and tfidf_matrix is not None:
        user_vec = vectorizer.transform([user_message])
        similarities = cosine_similarity(user_vec, tfidf_matrix).flatten()
        best_idx = similarities.argmax()
        best_tfidf_score = similarities[best_idx]

        if best_tfidf_score >= 0.20:
            return KNOWLEDGE_BASE[best_idx], round(float(best_tfidf_score) * 10, 2)

    # 3. Fallback to keyword match if >= 3
    if best_kw_score >= 3:
        return best_kw_entry, best_kw_score

    return None, 0


FALLBACK_ANSWER = (
    "I'm sorry, I don't have information on that yet. Please contact the "
    "college office or check the notice board for details, or try "
    "rephrasing your question (e.g. ask about admissions, timetable, "
    "exams, fees, faculty, notices, or events)."
)


# ---------------------------------------------------------------------------
# SQLite Logging & Automatic Seeding
# ---------------------------------------------------------------------------

def init_db():
    """Create database tables and seed initial FAQs if empty (runs on startup/redeploy)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            matched_category TEXT,
            confidence_score REAL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            keywords TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        """
    )

    # Seed FAQs automatically on startup if faqs table is empty
    cur.execute("SELECT COUNT(*) FROM faqs")
    count = cur.fetchone()[0]
    if count == 0 and os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            faqs_data = json.load(f)
        for item in faqs_data:
            cur.execute(
                """
                INSERT INTO faqs (id, category, keywords, question, answer)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.get("id"),
                    item.get("category", ""),
                    json.dumps(item.get("keywords", [])),
                    item.get("question", ""),
                    item.get("answer", ""),
                ),
            )
        print(f"SQLite DB initialized & seeded with {len(faqs_data)} FAQs at {DB_PATH}.")

    conn.commit()
    conn.close()


def log_chat(user_message, bot_response, category, score):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chat_logs (user_message, bot_response, matched_category, confidence_score, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_message, bot_response, category, score, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


# Ensure DB is created and seeded on module import (supports Gunicorn/Render startup)
init_db()


# ---------------------------------------------------------------------------
# Web / Frontend Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return "Not Found", 404


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "college-chatbot-backend"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "message field is required"}), 400

    entry, score = find_best_match(user_message)

    if entry:
        response_text = entry["answer"]
        category = entry["category"]
    else:
        response_text = FALLBACK_ANSWER
        category = "Unmatched"

    log_chat(user_message, response_text, category, score)

    return jsonify(
        {
            "reply": response_text,
            "category": category,
            "confidence_score": score,
        }
    )


@app.route("/api/faqs", methods=["GET"])
def faqs():
    """Return all FAQs, optionally filtered by category."""
    category = request.args.get("category")
    if category:
        filtered = [e for e in KNOWLEDGE_BASE if e["category"].lower() == category.lower()]
        return jsonify(filtered)
    return jsonify(KNOWLEDGE_BASE)


@app.route("/api/categories", methods=["GET"])
def categories():
    cats = sorted({e["category"] for e in KNOWLEDGE_BASE})
    return jsonify(cats)


@app.route("/api/history", methods=["GET"])
def history():
    """Return recent chat logs."""
    limit = request.args.get("limit", default=50, type=int)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM chat_logs ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting College Assistant Flask Server on http://0.0.0.0:{port} ...", flush=True)
    app.run(debug=False, host="0.0.0.0", port=port)
