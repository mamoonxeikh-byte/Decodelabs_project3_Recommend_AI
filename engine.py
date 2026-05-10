"""
RecommendAI - Recommendation Engine (Midend Logic Layer)
=========================================================
This module implements the core recommendation logic, completely decoupled
from both the API layer and the frontend. It handles:
  - Tag overlap scoring
  - Weighted scoring with category importance
  - TF-IDF inspired scoring for tag rarity
  - Combined ranking formula
  - Explanation generation
  - Diversity control
  - Cold-start handling
"""

import json
import math
from pathlib import Path
from typing import Optional
from collections import Counter

from models import (
    Item, UserPreferences, RecommendationResult,
    ScoreBreakdown, FeedbackStore
)


# ---------------------------------------------------------------------------
# Tag weight configuration — higher = more important during scoring
# ---------------------------------------------------------------------------
TAG_WEIGHTS: dict[str, float] = {
    "python": 1.4,
    "machine learning": 1.5,
    "ai": 1.5,
    "data science": 1.4,
    "backend": 1.2,
    "frontend": 1.2,
    "design": 1.1,
    "startup": 1.2,
    "leadership": 1.1,
    "security": 1.3,
}

CATEGORY_WEIGHTS: dict[str, float] = {
    "AI/ML": 1.4,
    "Technology": 1.2,
    "Data Science": 1.3,
    "Design": 1.1,
    "Business": 1.0,
    "DevOps": 1.15,
    "Leadership": 1.0,
    "Productivity": 0.9,
    "Marketing": 0.85,
}

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

_ITEMS_CACHE: list[Item] | None = None

def load_items() -> list[Item]:
    """Load items from JSON dataset (cached after first load)."""
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        data_path = Path(__file__).parent.parent / "data" / "items.json"
        with open(data_path) as f:
            raw = json.load(f)
        _ITEMS_CACHE = [Item(**item) for item in raw]
    return _ITEMS_CACHE


# ---------------------------------------------------------------------------
# TF-IDF helper — compute inverse document frequency for each tag
# ---------------------------------------------------------------------------

def _compute_idf(items: list[Item]) -> dict[str, float]:
    """
    IDF = log(N / df) where df = number of items containing the tag.
    Rare tags get a higher IDF and thus higher weight when matched.
    """
    N = len(items)
    df: Counter = Counter()
    for item in items:
        for tag in set(item.tags):
            df[tag] += 1
    return {tag: math.log(N / count + 1) for tag, count in df.items()}


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _tag_overlap_score(user_tags: list[str], item_tags: list[str]) -> tuple[float, list[str]]:
    """
    Simple Jaccard-style overlap.
    Returns (score 0-1, list of matched tags).
    """
    user_set = set(t.lower() for t in user_tags)
    item_set = set(t.lower() for t in item_tags)
    matched = list(user_set & item_set)
    if not user_set:
        return 0.0, []
    union = user_set | item_set
    score = len(matched) / len(union)  # Jaccard coefficient
    return score, matched


def _weighted_tag_score(
    user_tags: list[str],
    item_tags: list[str],
    idf: dict[str, float],
) -> float:
    """
    Weighted cosine-like score:
      - Each matched tag contributes: TAG_WEIGHT * IDF_weight
      - Normalized by the total possible score for user's tags
    """
    user_set = set(t.lower() for t in user_tags)
    item_set = set(t.lower() for t in item_tags)
    matched = user_set & item_set

    numerator = 0.0
    for tag in matched:
        w = TAG_WEIGHTS.get(tag, 1.0)
        idf_val = idf.get(tag, 1.0)
        numerator += w * idf_val

    # Denominator: max possible score for user profile
    denominator = sum(TAG_WEIGHTS.get(t, 1.0) * idf.get(t, 1.0) for t in user_set)
    if denominator == 0:
        return 0.0
    return min(numerator / denominator, 1.0)


def _popularity_bonus(popularity: int) -> float:
    """Normalize popularity (0-100) to a small bonus (0-0.1)."""
    return (popularity / 100) * 0.10


def _difficulty_match_score(user_level: str | None, item_difficulty: str) -> float:
    """
    Give a bonus if item difficulty matches or is adjacent to user level.
    """
    if user_level is None:
        return 0.05  # neutral bonus
    levels = ["beginner", "intermediate", "advanced"]
    try:
        u_idx = levels.index(user_level.lower())
        i_idx = levels.index(item_difficulty.lower())
    except ValueError:
        return 0.0
    distance = abs(u_idx - i_idx)
    if distance == 0:
        return 0.10
    elif distance == 1:
        return 0.04
    return 0.0


def _feedback_adjustment(item_id: str, feedback: FeedbackStore) -> float:
    """
    Apply score adjustments based on user feedback history.
    Liked items of same category/tags get a boost; disliked ones are penalized.
    """
    liked = feedback.liked_ids
    disliked = feedback.disliked_ids

    if item_id in disliked:
        return -0.35  # Heavy penalty for disliked item
    if item_id in liked:
        return 0.0    # Already seen/liked — handled via diversity filter
    return 0.0


def _diversity_penalty(
    item: Item,
    already_selected: list[Item],
    penalty_per_shared_tag: float = 0.04,
) -> float:
    """
    Penalize items that are very similar to already-selected recommendations
    to ensure category and tag diversity.
    """
    if not already_selected:
        return 0.0
    item_tags = set(item.tags)
    total_penalty = 0.0
    for selected in already_selected:
        overlap = len(item_tags & set(selected.tags))
        total_penalty += overlap * penalty_per_shared_tag
        # Extra penalty for same category
        if item.category == selected.category:
            total_penalty += 0.06
    return min(total_penalty, 0.40)  # Cap at 40% penalty


# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------

def _generate_explanation(
    matched_tags: list[str],
    user_tags: list[str],
    item: Item,
    final_score: float,
    category_weight: float,
) -> str:
    """
    Generate a human-readable explanation for why an item was recommended.
    """
    n_matched = len(matched_tags)
    n_total = len(user_tags)

    if n_matched == 0:
        return f"Trending in {item.category} — popular pick with a {item.rating}★ rating."

    matched_str = ", ".join(f"#{t}" for t in matched_tags[:4])

    if n_matched >= n_total * 0.8:
        strength = "Excellent fit"
    elif n_matched >= n_total * 0.5:
        strength = "Strong match"
    elif n_matched >= 2:
        strength = "Good overlap"
    else:
        strength = "Partial match"

    explanation = (
        f"{strength} — matched {n_matched}/{n_total} of your interests: {matched_str}."
    )

    if category_weight > 1.1:
        explanation += f" {item.category} is one of your priority domains."

    if item.popularity >= 90:
        explanation += " Highly popular among learners."

    return explanation


# ---------------------------------------------------------------------------
# Score breakdown for UI visualization
# ---------------------------------------------------------------------------

def _build_score_breakdown(
    overlap_score: float,
    weighted_score: float,
    popularity_bonus: float,
    difficulty_bonus: float,
    feedback_adj: float,
    diversity_penalty: float,
    category_weight: float,
) -> ScoreBreakdown:
    return ScoreBreakdown(
        tag_overlap=round(overlap_score * 100, 1),
        weighted_similarity=round(weighted_score * 100, 1),
        popularity_bonus=round(popularity_bonus * 100, 1),
        difficulty_match=round(difficulty_bonus * 100, 1),
        feedback_adjustment=round(feedback_adj * 100, 1),
        diversity_penalty=round(-diversity_penalty * 100, 1),
        category_multiplier=round(category_weight, 2),
    )


# ---------------------------------------------------------------------------
# Main recommendation function
# ---------------------------------------------------------------------------

def get_recommendations(
    preferences: UserPreferences,
    feedback: FeedbackStore,
    top_k: int = 8,
) -> list[RecommendationResult]:
    """
    Core recommendation pipeline:
      1. Load items
      2. Compute IDF over corpus
      3. Score each item using multiple strategies
      4. Apply feedback adjustments and diversity control
      5. Sort by final score
      6. Generate explanations
      7. Handle cold-start / no-match fallback
    """
    items = load_items()
    user_tags = [t.lower() for t in preferences.tags]
    idf = _compute_idf(items)

    # --- Filter out disliked items entirely ---
    candidates = [i for i in items if i.id not in feedback.disliked_ids]

    # --- Score all candidates ---
    scored: list[tuple[float, Item, list[str], ScoreBreakdown]] = []

    for item in candidates:
        # Strategy 1: Tag overlap (Jaccard)
        overlap_score, matched_tags = _tag_overlap_score(user_tags, item.tags)

        # Strategy 2: Weighted TF-IDF similarity
        weighted_score = _weighted_tag_score(user_tags, item.tags, idf)

        # Strategy 3: Bonuses
        pop_bonus = _popularity_bonus(item.popularity)
        diff_bonus = _difficulty_match_score(preferences.experience_level, item.difficulty)
        feedback_adj = _feedback_adjustment(item.id, feedback)

        # Strategy 4: Category affinity
        cat_weight = 1.0
        if preferences.preferred_categories:
            for pref_cat in preferences.preferred_categories:
                if pref_cat.lower() in item.category.lower():
                    cat_weight = CATEGORY_WEIGHTS.get(item.category, 1.0)
                    break

        # --- Combine scores ---
        # Weighted formula: 40% overlap + 40% weighted sim + 20% bonuses
        raw_score = (
            0.40 * overlap_score
            + 0.40 * weighted_score
            + pop_bonus
            + diff_bonus
            + feedback_adj
        ) * cat_weight

        scored.append((raw_score, item, matched_tags, overlap_score, weighted_score,
                       pop_bonus, diff_bonus, feedback_adj, cat_weight))

    # --- Sort by raw score before diversity control ---
    scored.sort(key=lambda x: x[0], reverse=True)

    # --- Apply diversity control + build results ---
    results: list[RecommendationResult] = []
    selected_items: list[Item] = []

    for entry in scored:
        raw_score, item, matched_tags, overlap_s, weighted_s, pop_b, diff_b, fb_adj, cat_w = entry

        # Skip already-liked items (user has seen them)
        if item.id in feedback.liked_ids:
            continue

        # Apply diversity penalty after we have initial selections
        div_penalty = _diversity_penalty(item, selected_items)
        final_score = max(0.0, raw_score - div_penalty)

        breakdown = _build_score_breakdown(
            overlap_s, weighted_s, pop_b, diff_b, fb_adj, div_penalty, cat_w
        )

        explanation = _generate_explanation(
            matched_tags, user_tags, item, final_score, cat_w
        )

        # Confidence label
        if final_score >= 0.65:
            confidence = "High"
        elif final_score >= 0.35:
            confidence = "Medium"
        else:
            confidence = "Low"

        results.append(RecommendationResult(
            item=item,
            score=round(min(final_score * 100, 100.0), 1),  # 0-100 scale
            confidence=confidence,
            matched_tags=matched_tags,
            explanation=explanation,
            breakdown=breakdown,
        ))

        selected_items.append(item)

        if len(results) >= top_k:
            break

    # --- Cold-start / no-match fallback ---
    if not results or all(r.score < 10 for r in results):
        results = _fallback_trending(candidates, top_k)

    return results


def _fallback_trending(items: list[Item], top_k: int) -> list[RecommendationResult]:
    """
    Cold-start fallback: return top-rated trending items across diverse categories.
    """
    # Sort by a combined trending score
    sorted_items = sorted(
        items,
        key=lambda i: (i.popularity * 0.6 + i.rating * 8),
        reverse=True
    )

    seen_categories: set[str] = set()
    results = []
    for item in sorted_items:
        if len(results) >= top_k:
            break
        # Ensure category diversity in fallback
        if item.category in seen_categories and len(results) < top_k // 2:
            continue
        seen_categories.add(item.category)

        breakdown = ScoreBreakdown(
            tag_overlap=0.0,
            weighted_similarity=0.0,
            popularity_bonus=round((item.popularity / 100) * 10, 1),
            difficulty_match=0.0,
            feedback_adjustment=0.0,
            diversity_penalty=0.0,
            category_multiplier=1.0,
        )
        results.append(RecommendationResult(
            item=item,
            score=round((item.popularity * 0.6 + item.rating * 8), 1),
            confidence="Low",
            matched_tags=[],
            explanation=f"Trending pick — {item.popularity}% popularity score, rated {item.rating}★ by learners.",
            breakdown=breakdown,
        ))

    return results


def get_trending_items(limit: int = 5) -> list[Item]:
    """Return top trending items (for suggestions / cold-start UI)."""
    items = load_items()
    return sorted(items, key=lambda i: i.popularity, reverse=True)[:limit]


def get_all_tags() -> list[str]:
    """Return all unique tags across the dataset, sorted by frequency."""
    items = load_items()
    tag_count: Counter = Counter()
    for item in items:
        tag_count.update(item.tags)
    return [tag for tag, _ in tag_count.most_common()]


def get_all_categories() -> list[str]:
    """Return all unique categories."""
    items = load_items()
    return sorted(set(i.category for i in items))