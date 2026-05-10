"""
RecommendAI - Shared Data Models
=================================
Pure-Python dataclasses — zero external dependencies.
The FastAPI backend (backend/main.py) uses pydantic for request/response
validation at the HTTP boundary; the midend engine uses these plain classes
for all internal computation, keeping the logic layer fully decoupled.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    """A single content item in the recommendation catalogue."""
    id: str
    title: str
    category: str
    tags: list          # list[str]
    difficulty: str     # beginner | intermediate | advanced
    popularity: int     # 0-100
    rating: float       # 0-5
    description: str
    author: str
    duration: str


@dataclass
class UserPreferences:
    """User-submitted preferences for generating recommendations."""
    tags: list = field(default_factory=list)
    preferred_categories: list = field(default_factory=list)
    experience_level: Optional[str] = None  # beginner | intermediate | advanced | None
    top_k: int = 8


@dataclass
class FeedbackStore:
    """Tracks user feedback for iterative recommendation improvement."""
    liked_ids: list = field(default_factory=list)
    disliked_ids: list = field(default_factory=list)


@dataclass
class ScoreBreakdown:
    """Granular breakdown of how the final score was computed."""
    tag_overlap: float           # Jaccard overlap score contribution
    weighted_similarity: float   # TF-IDF weighted score contribution
    popularity_bonus: float      # Popularity contribution (0-10)
    difficulty_match: float      # Difficulty alignment bonus (0-10)
    feedback_adjustment: float   # Positive/negative from user feedback
    diversity_penalty: float     # Penalty for similarity to other results
    category_multiplier: float   # Category preference multiplier

    def to_dict(self) -> dict:
        return {
            "tag_overlap": self.tag_overlap,
            "weighted_similarity": self.weighted_similarity,
            "popularity_bonus": self.popularity_bonus,
            "difficulty_match": self.difficulty_match,
            "feedback_adjustment": self.feedback_adjustment,
            "diversity_penalty": self.diversity_penalty,
            "category_multiplier": self.category_multiplier,
        }


@dataclass
class RecommendationResult:
    """A single recommendation with full scoring metadata."""
    item: Item
    score: float              # Final score 0-100
    confidence: str           # High | Medium | Low
    matched_tags: list        # Tags that matched user preferences
    explanation: str          # Human-readable reason for recommendation
    breakdown: ScoreBreakdown

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON API responses."""
        return {
            "item": {
                "id": self.item.id,
                "title": self.item.title,
                "category": self.item.category,
                "tags": self.item.tags,
                "difficulty": self.item.difficulty,
                "popularity": self.item.popularity,
                "rating": self.item.rating,
                "description": self.item.description,
                "author": self.item.author,
                "duration": self.item.duration,
            },
            "score": self.score,
            "confidence": self.confidence,
            "matched_tags": self.matched_tags,
            "explanation": self.explanation,
            "breakdown": self.breakdown.to_dict(),
        }