"""
Database initialization and seeding script for College Chatbot.
Creates the SQLite database, sets up required tables, and seeds initial FAQ data.
"""

import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chatbot.db")
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")


def init_and_seed_db():
    print(f"Connecting to SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Create chat_logs table
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

    # 2. Create faqs table
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

    # 3. Seed FAQs from knowledge_base.json if available
    seeded_count = 0
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            faqs_data = json.load(f)

        cur.execute("SELECT COUNT(*) FROM faqs")
        count = cur.fetchone()[0]

        if count == 0:
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
            seeded_count = len(faqs_data)
            print(f"Successfully seeded {seeded_count} FAQs into 'faqs' table.")
        else:
            print(f"'faqs' table already contains {count} entries.")
    else:
        print(f"Warning: {KB_PATH} not found.")

    conn.commit()
    conn.close()
    print("Database initialization and seeding completed successfully.")


if __name__ == "__main__":
    init_and_seed_db()
