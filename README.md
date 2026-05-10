# RecommendAI 🎯

### A Portfolio-Grade AI Recommendation System

> Similarity-based recommendations with explainable AI, glassmorphism UI, and a clean three-layer architecture.

---

## 🏗️ Architecture

```
recommendai/
├── backend/          ← FastAPI REST API (HTTP layer only)
│   └── main.py
├── midend/           ← Recommendation engine + scoring logic (no I/O)
│   ├── engine.py
│   └── models.py
├── frontend/         ← Streamlit UI (calls API, renders results)
│   └── app.py
├── data/
│   └── items.json    ← 25-item rich dataset
└── requirements.txt
```

## 🧠 Recommendation Engine

The midend engine combines **three scoring strategies** into a final ranking:

| Strategy                  | Weight | Description                                   |
| ------------------------- | ------ | --------------------------------------------- |
| **Tag Overlap (Jaccard)** | 40%    | Set intersection / union of user vs item tags |
| **Weighted TF-IDF**       | 40%    | Tag importance × rarity in corpus             |
| **Bonuses**               | 20%    | Popularity (10%) + Difficulty alignment (10%) |

Then applies:

- **Category multiplier** — boosts preferred domains
- **Feedback adjustment** — penalizes disliked items, removes liked from results
- **Diversity penalty** — penalizes items too similar to already-selected results
- **Cold-start fallback** — returns trending items when no preferences given

Every recommendation includes:

- **Score** (0-100)
- **Confidence** (High / Medium / Low)
- **Explanation** ("Matched 3/5 interests: python, AI, backend")
- **Score breakdown** (per-strategy contribution)

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Start the Streamlit frontend (new terminal)

```bash
cd frontend
streamlit run app.py
```

### 4. Open the app

- **Frontend UI**: http://localhost:8501
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

---

## 🔌 API Endpoints

| Method | Endpoint     | Description                          |
| ------ | ------------ | ------------------------------------ |
| `GET`  | `/health`    | Service health + catalogue stats     |
| `GET`  | `/metadata`  | All tags, categories, trending items |
| `POST` | `/recommend` | Generate recommendations             |
| `POST` | `/feedback`  | Submit like/dislike feedback         |

### Example: Get recommendations

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "tags": ["python", "machine learning", "backend"],
      "preferred_categories": ["AI/ML", "Technology"],
      "experience_level": "intermediate",
      "top_k": 6
    },
    "feedback": {
      "liked_ids": [],
      "disliked_ids": []
    }
  }'
```

---

## 🎨 UI Features

- **Dark glassmorphism** with ambient glow orbs
- **Tag chip selector** with multi-select
- **Animated recommendation cards** with staggered fade-in
- **Score progress bar** (color-coded by confidence)
- **Expandable score breakdown** per card
- **Like / Dislike feedback** with real-time result adjustment
- **Shimmer loaders** during API calls
- **Cold-start trending view** for new users

---

## 📊 Dataset

25 curated items across 9 categories:

- Technology, AI/ML, Data Science, Design
- Business, DevOps, Leadership, Productivity, Marketing

Each item has: title, tags (4–7), difficulty, popularity (0–100), rating (0–5), author, duration.

---

## 🚀 Extend It

- **Add deep learning**: Swap `_weighted_tag_score` with a sentence-transformer embedding
- **Persist feedback**: Replace in-memory FeedbackStore with Redis or SQLite
- **User accounts**: Add JWT auth to the FastAPI backend
- **More items**: Expand `data/items.json` — the engine scales automatically
- **A/B testing**: Add a `strategy` query param to compare scoring variants
