# AI Chatbot for College Student Assistance

A full-stack college FAQ chatbot with a **separated frontend and backend**,
built to match the project report: Python, Flask, HTML/CSS/JavaScript,
and SQLite.

```
college-chatbot/
├── backend/
│   ├── app.py              # Flask REST API + chatbot matching logic
│   ├── knowledge_base.json # FAQ knowledge base (admissions, exams, fees...)
│   ├── requirements.txt    # Python dependencies
│   └── chatbot.db          # SQLite DB (auto-created on first run)
├── frontend/
│   ├── index.html          # Chat UI
│   ├── style.css           # Styling
│   └── script.js           # Calls the backend API
└── README.md
```

## How it works

1. The **backend** (Flask) exposes a REST API (`/api/chat`) that takes a
   user's message, matches it against a JSON knowledge base using
   keyword/NLP scoring, and returns the best-matching answer. Every
   conversation is logged to a local SQLite database (`chatbot.db`).
2. The **frontend** is a plain HTML/CSS/JS chat widget that calls the
   backend API over `fetch()` and displays the conversation. Because it's
   fully separated, you can host it anywhere (or open it directly in a
   browser) as long as it can reach the backend URL.

This keeps things simple and runnable without any paid API key, while
leaving a clear extension point (see "Using a real AI model" below) to
plug in OpenAI or Google Gemini as mentioned in the project report.

## 1. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API starts at `http://127.0.0.1:5000`. On first run it creates
`chatbot.db` automatically.

### API endpoints

| Method | Endpoint          | Description                                  |
|--------|-------------------|-----------------------------------------------|
| GET    | `/api/health`     | Health check                                   |
| POST   | `/api/chat`       | Body: `{ "message": "..." }` → chatbot reply   |
| GET    | `/api/faqs`       | List all FAQs (optional `?category=Fees`)      |
| GET    | `/api/categories` | List all FAQ categories                        |
| GET    | `/api/history`    | Recent chat logs (optional `?limit=50`)        |

## 2. Run the frontend

The frontend is static HTML/CSS/JS — no build step needed.

**Option A — just open it:**
Double-click `frontend/index.html`, or open it in your browser directly.

**Option B — serve it (recommended, avoids CORS quirks):**
```bash
cd frontend
python -m http.server 5500
```
Then visit `http://127.0.0.1:5500`.

Make sure the backend (step 1) is running first — the chat header shows a
green dot when it's connected, red if it can't reach the API.

If you host the frontend on a different domain/port in production, update
`API_BASE_URL` at the top of `frontend/script.js` to point to your
backend's URL.

## 3. Customize the knowledge base

Edit `backend/knowledge_base.json` to add, remove, or update FAQs. Each
entry has:

```json
{
  "id": 14,
  "category": "Library",
  "keywords": ["library", "book", "borrow"],
  "question": "How do I borrow a book from the library?",
  "answer": "Visit the library with your student ID..."
}
```

No restart of the frontend is needed — just restart `app.py` after
editing the JSON.

## 4. Using a real AI model (optional, matches report's future scope)

The current matcher uses keyword/NLP scoring (no API key required). To
upgrade to a real LLM (OpenAI or Google Gemini, as listed in the
project's software requirements) for more natural, flexible answers:

1. Install the relevant SDK (`openai` or `google-generativeai`) and add
   it to `requirements.txt`.
2. In `app.py`, inside the `/api/chat` route, call the LLM API with the
   knowledge base as context (RAG-style) when no good keyword match is
   found, instead of returning the fallback message.
3. Store your API key in an environment variable — never hardcode it.

## Notes

- SQLite (`chatbot.db`) is used for simplicity per the report's software
  requirements; swap in MySQL by changing the `sqlite3` connection logic
  in `app.py` if needed.
- CORS is enabled on the backend so the frontend can be hosted separately
  (different port/domain) from the API.
