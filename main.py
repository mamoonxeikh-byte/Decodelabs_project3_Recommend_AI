"""
RecommendAI - FastAPI Backend
==============================
REST API layer only. All logic lives in midend/engine.py.

Endpoints:
  GET  /health      — Service health
  GET  /metadata    — Tags, categories, trending items
  POST /recommend   — Get personalized recommendations
  POST /feedback    — Submit like/dislike feedback
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "midend"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from models import UserPreferences, FeedbackStore
from engine import get_recommendations, get_all_tags, get_all_categories, get_trending_items, load_items

# ── Pydantic schemas (API boundary only) ────────────────────────────────────
class PreferencesSchema(BaseModel):
    tags: list[str] = Field(default_factory=list)
    preferred_categories: list[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    top_k: int = Field(default=8, ge=1, le=20)

class FeedbackSchema(BaseModel):
    liked_ids: list[str] = Field(default_factory=list)
    disliked_ids: list[str] = Field(default_factory=list)

class RecommendRequest(BaseModel):
    preferences: PreferencesSchema
    feedback: FeedbackSchema = Field(default_factory=FeedbackSchema)

class FeedbackRequest(BaseModel):
    item_id: str
    action: str          # like | dislike | remove
    current_feedback: FeedbackSchema

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="RecommendAI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "healthy", "catalogue_size": len(load_items()), "version": "1.0.0"}

@app.get("/metadata")
def metadata():
    trending = get_trending_items(limit=6)
    return {
        "all_tags": get_all_tags(),
        "all_categories": get_all_categories(),
        "trending_items": [
            {k: getattr(t, k) for k in ['id','title','category','tags','difficulty','popularity','rating','description','author','duration']}
            for t in trending
        ],
    }

@app.post("/recommend")
def recommend(body: RecommendRequest):
    prefs = UserPreferences(
        tags=body.preferences.tags,
        preferred_categories=body.preferences.preferred_categories,
        experience_level=body.preferences.experience_level,
        top_k=body.preferences.top_k,
    )
    feedback = FeedbackStore(liked_ids=body.feedback.liked_ids, disliked_ids=body.feedback.disliked_ids)
    results = get_recommendations(prefs, feedback, top_k=prefs.top_k)
    is_cold = not prefs.tags and not prefs.preferred_categories
    return {
        "recommendations": [r.to_dict() for r in results],
        "total_items_evaluated": len(load_items()),
        "query_tags": prefs.tags,
        "is_cold_start": is_cold,
    }

@app.post("/feedback")
def feedback(body: FeedbackRequest):
    liked = list(body.current_feedback.liked_ids)
    disliked = list(body.current_feedback.disliked_ids)
    iid, action = body.item_id, body.action.lower()
    if action == "like":
        if iid not in liked: liked.append(iid)
        if iid in disliked: disliked.remove(iid)
    elif action == "dislike":
        if iid not in disliked: disliked.append(iid)
        if iid in liked: liked.remove(iid)
    elif action == "remove":
        liked = [x for x in liked if x != iid]
        disliked = [x for x in disliked if x != iid]
    else:
        raise HTTPException(400, f"Unknown action: {action}")
    return {"liked_ids": liked, "disliked_ids": disliked}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)