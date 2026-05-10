"""
RecommendAI - Streamlit Frontend
==================================
Premium dark-mode UI with glassmorphism, animated cards,
tag-chip inputs, score breakdowns, and feedback system.
"""

import sys
import os
import time
import json
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = os.getenv("RECOMMENDAI_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RecommendAI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium CSS — Glassmorphism dark theme
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

/* ─── Base ─────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: #080c14 !important;
    font-family: 'DM Sans', sans-serif;
    color: #e2e8f0;
}
[data-testid="stSidebar"] {
    background: rgba(10, 15, 25, 0.95) !important;
    border-right: 1px solid rgba(99, 179, 237, 0.12);
}
[data-testid="stHeader"] { background: transparent !important; }

/* ─── Typography ─────────────────────────────────────────── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #63b3ed 0%, #9f7aea 50%, #f687b3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 0.3rem;
}
.hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.05rem;
    color: #718096;
    font-weight: 300;
    letter-spacing: 0.02em;
}
.section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4a5568;
    margin-bottom: 0.8rem;
}

/* ─── Glass card base ───────────────────────────────────── */
.glass-card {
    background: rgba(15, 22, 38, 0.75);
    border: 1px solid rgba(99, 179, 237, 0.14);
    border-radius: 18px;
    padding: 1.5rem;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow:
        0 4px 24px rgba(0,0,0,0.4),
        inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    margin-bottom: 1.25rem;
    animation: fadeSlideIn 0.45s ease both;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow:
        0 8px 32px rgba(0,0,0,0.5),
        0 0 0 1px rgba(99,179,237,0.22),
        inset 0 1px 0 rgba(255,255,255,0.07);
    border-color: rgba(99, 179, 237, 0.28);
}

/* ─── Rec card ──────────────────────────────────────────── */
.rec-card {
    background: rgba(12, 19, 33, 0.82);
    border: 1px solid rgba(99, 179, 237, 0.12);
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    backdrop-filter: blur(20px);
    box-shadow: 0 4px 28px rgba(0,0,0,0.45);
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    animation: fadeSlideIn 0.5s ease both;
    position: relative;
    overflow: hidden;
}
.rec-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #63b3ed, #9f7aea, #f687b3);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.rec-card:hover::before { opacity: 1; }
.rec-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99,179,237,0.3);
    box-shadow: 0 12px 40px rgba(0,0,0,0.55), 0 0 60px rgba(99,179,237,0.06);
}

/* ─── Tags / chips ──────────────────────────────────────── */
.tag-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(99,179,237,0.1);
    border: 1px solid rgba(99,179,237,0.22);
    color: #90cdf4;
    padding: 0.22rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.2s ease;
}
.tag-chip.matched {
    background: rgba(99,179,237,0.18);
    border-color: rgba(99,179,237,0.45);
    color: #63b3ed;
    font-weight: 600;
}
.tag-chip.unmatched {
    background: rgba(74,85,104,0.15);
    border-color: rgba(74,85,104,0.25);
    color: #4a5568;
}
.tag-chip.cat-chip {
    background: rgba(159,122,234,0.12);
    border-color: rgba(159,122,234,0.3);
    color: #b794f4;
}

/* ─── Score bar ─────────────────────────────────────────── */
.score-bar-wrap { margin: 0.6rem 0 0.2rem; }
.score-bar-track {
    background: rgba(255,255,255,0.06);
    border-radius: 999px;
    height: 7px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #4299e1, #9f7aea);
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.score-bar-fill.high  { background: linear-gradient(90deg, #48bb78, #38b2ac); }
.score-bar-fill.med   { background: linear-gradient(90deg, #f6ad55, #ed8936); }
.score-bar-fill.low   { background: linear-gradient(90deg, #fc8181, #f56565); }

/* ─── Confidence badge ──────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.badge-high   { background: rgba(72,187,120,0.15); color: #68d391; border: 1px solid rgba(72,187,120,0.3); }
.badge-medium { background: rgba(246,173,85,0.15); color: #f6ad55; border: 1px solid rgba(246,173,85,0.3); }
.badge-low    { background: rgba(252,129,129,0.15); color: #fc8181; border: 1px solid rgba(252,129,129,0.3); }

/* ─── Breakdown rows ────────────────────────────────────── */
.breakdown-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.28rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.82rem;
}
.breakdown-label { color: #718096; }
.breakdown-val { font-weight: 600; font-family: 'Syne', sans-serif; }
.breakdown-val.pos { color: #68d391; }
.breakdown-val.neg { color: #fc8181; }
.breakdown-val.neu { color: #90cdf4; }

/* ─── Glow orbs (ambient) ────────────────────────────────── */
.orb-container {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: -1;
    overflow: hidden;
}
.orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.07;
    animation: orbFloat 12s ease-in-out infinite alternate;
}
.orb-1 { width: 600px; height: 600px; top: -200px; left: -100px; background: #63b3ed; }
.orb-2 { width: 500px; height: 500px; top: 40%; right: -150px; background: #9f7aea; animation-delay: -4s; }
.orb-3 { width: 400px; height: 400px; bottom: -100px; left: 30%; background: #f687b3; animation-delay: -8s; }

/* ─── Animations ────────────────────────────────────────── */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes orbFloat {
    from { transform: translate(0, 0) scale(1); }
    to   { transform: translate(30px, 20px) scale(1.08); }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(99,179,237,0.2); }
    50%       { box-shadow: 0 0 40px rgba(99,179,237,0.4); }
}
@keyframes shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}

/* ─── Shimmer loader ────────────────────────────────────── */
.shimmer-card {
    background: linear-gradient(90deg,
        rgba(255,255,255,0.04) 25%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.04) 75%
    );
    background-size: 600px 100%;
    border-radius: 20px;
    height: 200px;
    margin-bottom: 1.25rem;
    animation: shimmer 1.6s ease infinite;
}

/* ─── Stats bar ─────────────────────────────────────────── */
.stat-row {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}
.stat-pill {
    background: rgba(15,22,38,0.8);
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 12px;
    padding: 0.6rem 1.1rem;
    font-size: 0.85rem;
}
.stat-pill .val {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #63b3ed;
}
.stat-pill .lbl { color: #4a5568; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; }

/* ─── Streamlit widget overrides ─────────────────────────── */
[data-testid="stMultiSelect"] > div > div {
    background: rgba(15,22,38,0.8) !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
[data-testid="stSelectbox"] > div > div {
    background: rgba(15,22,38,0.8) !important;
    border: 1px solid rgba(99,179,237,0.15) !important;
    border-radius: 12px !important;
}
.stSlider > div > div > div { background: linear-gradient(90deg, #63b3ed, #9f7aea) !important; }
.stButton > button {
    background: linear-gradient(135deg, #3182ce, #805ad5) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 15px rgba(99,179,237,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,179,237,0.4) !important;
}
[data-testid="stExpander"] {
    background: rgba(15,22,38,0.5) !important;
    border: 1px solid rgba(99,179,237,0.1) !important;
    border-radius: 12px !important;
}
div[data-testid="metric-container"] {
    background: rgba(15,22,38,0.7);
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 14px;
    padding: 1rem;
}
</style>

<!-- Ambient orbs -->
<div class="orb-container">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <div class="orb orb-3"></div>
</div>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_session():
    defaults = {
        "feedback": {"liked_ids": [], "disliked_ids": []},
        "recommendations": None,
        "metadata": None,
        "last_query_tags": [],
        "is_cold_start": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_call(method: str, endpoint: str, **kwargs) -> dict | None:
    try:
        url = f"{API_BASE}{endpoint}"
        resp = getattr(requests, method)(url, timeout=10, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the RecommendAI API. Make sure the backend is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_metadata():
    return api_call("get", "/metadata")


def fetch_recommendations(tags, categories, level, top_k):
    payload = {
        "preferences": {
            "tags": tags,
            "preferred_categories": categories,
            "experience_level": level if level != "Any" else None,
            "top_k": top_k,
        },
        "feedback": st.session_state.feedback,
    }
    return api_call("post", "/recommend", json=payload)


def submit_feedback(item_id: str, action: str):
    payload = {
        "item_id": item_id,
        "action": action,
        "current_feedback": st.session_state.feedback,
    }
    result = api_call("post", "/feedback", json=payload)
    if result:
        st.session_state.feedback = result


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

def render_score_bar(score: float, confidence: str):
    pct = min(score, 100)
    cls = {"High": "high", "Medium": "med", "Low": "low"}.get(confidence, "med")
    st.markdown(f"""
    <div class="score-bar-wrap">
      <div class="score-bar-track">
        <div class="score-bar-fill {cls}" style="width:{pct}%"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_tags(tags: list, matched: list):
    matched_set = set(t.lower() for t in matched)
    chips = ""
    for tag in tags:
        cls = "matched" if tag.lower() in matched_set else "unmatched"
        icon = "✦ " if cls == "matched" else ""
        chips += f'<span class="tag-chip {cls}">{icon}{tag}</span> '
    st.markdown(f'<div style="margin: 0.6rem 0;">{chips}</div>', unsafe_allow_html=True)


def render_badge(confidence: str):
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(confidence, "badge-medium")
    icon = {"High": "◆", "Medium": "◈", "Low": "◇"}.get(confidence, "◈")
    st.markdown(f'<span class="badge {cls}">{icon} {confidence} Match</span>', unsafe_allow_html=True)


def render_breakdown(breakdown: dict):
    rows = [
        ("Tag Overlap (Jaccard)", breakdown.get("tag_overlap", 0), "pos"),
        ("Weighted Similarity (TF-IDF)", breakdown.get("weighted_similarity", 0), "pos"),
        ("Popularity Bonus", breakdown.get("popularity_bonus", 0), "pos"),
        ("Difficulty Alignment", breakdown.get("difficulty_match", 0), "pos"),
        ("Feedback Adjustment", breakdown.get("feedback_adjustment", 0), "pos" if breakdown.get("feedback_adjustment", 0) >= 0 else "neg"),
        ("Diversity Penalty", breakdown.get("diversity_penalty", 0), "neg" if breakdown.get("diversity_penalty", 0) < 0 else "neu"),
        ("Category Multiplier ×", breakdown.get("category_multiplier", 1.0), "neu"),
    ]
    html = '<div style="margin-top:0.5rem;">'
    for label, val, cls in rows:
        prefix = "×" if "Multiplier" in label else ("−" if val < 0 else "+")
        display = f"{prefix}{abs(val):.1f}" if "Multiplier" not in label else f"×{val:.2f}"
        html += f"""
        <div class="breakdown-row">
          <span class="breakdown-label">{label}</span>
          <span class="breakdown-val {cls}">{display}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_recommendation_card(rec: dict, idx: int):
    item = rec["item"]
    score = rec["score"]
    confidence = rec["confidence"]
    matched = rec["matched_tags"]
    explanation = rec["explanation"]
    breakdown = rec["breakdown"]
    liked = item["id"] in st.session_state.feedback["liked_ids"]
    disliked = item["id"] in st.session_state.feedback["disliked_ids"]

    # Stagger animation delay
    delay = idx * 0.08

    with st.container():
        st.markdown(f'<div class="rec-card" style="animation-delay:{delay}s">', unsafe_allow_html=True)

        # Header row
        col_title, col_score = st.columns([3, 1])
        with col_title:
            diff_colors = {"beginner": "#68d391", "intermediate": "#f6ad55", "advanced": "#fc8181"}
            diff_color = diff_colors.get(item.get("difficulty", ""), "#718096")
            st.markdown(f"""
            <div style="margin-bottom:0.2rem;">
                <span class="tag-chip cat-chip">{item['category']}</span>
                <span style="color:{diff_color}; font-size:0.75rem; margin-left:0.5rem;">
                    ● {item.get('difficulty','').capitalize()}
                </span>
            </div>
            <div style="font-family:'Syne',sans-serif; font-size:1.12rem; font-weight:700; color:#e2e8f0; margin:0.4rem 0 0.1rem;">
                {item['title']}
            </div>
            <div style="color:#718096; font-size:0.82rem;">
                {item['author']} · {item.get('duration','')} · ⭐ {item['rating']}
            </div>
            """, unsafe_allow_html=True)

        with col_score:
            st.markdown(f"""
            <div style="text-align:right;">
                <div style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
                     background:linear-gradient(135deg,#63b3ed,#9f7aea);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                     line-height:1;">{score:.0f}</div>
                <div style="color:#4a5568; font-size:0.7rem; text-transform:uppercase;
                     letter-spacing:0.1em;">Score / 100</div>
            </div>
            """, unsafe_allow_html=True)
            render_badge(confidence)

        # Score bar
        render_score_bar(score, confidence)

        # Description
        st.markdown(f'<div style="color:#a0aec0; font-size:0.85rem; margin:0.5rem 0 0.3rem; line-height:1.55;">{item["description"]}</div>', unsafe_allow_html=True)

        # Tags
        render_tags(item["tags"], matched)

        # Explanation box
        st.markdown(f"""
        <div style="background:rgba(99,179,237,0.07); border:1px solid rgba(99,179,237,0.15);
             border-radius:10px; padding:0.7rem 1rem; margin:0.5rem 0;
             font-size:0.83rem; color:#90cdf4; line-height:1.5;">
            💡 <strong>Why recommended:</strong> {explanation}
        </div>
        """, unsafe_allow_html=True)

        # Score breakdown (expandable)
        with st.expander("📊 Score Breakdown"):
            render_breakdown(breakdown)

        # Feedback buttons
        fb_col1, fb_col2, fb_col3, _ = st.columns([1, 1, 1, 3])
        with fb_col1:
            like_label = "💙 Liked" if liked else "👍 Like"
            if st.button(like_label, key=f"like_{item['id']}_{idx}"):
                action = "remove" if liked else "like"
                submit_feedback(item["id"], action)
                st.rerun()
        with fb_col2:
            dis_label = "🚫 Disliked" if disliked else "👎 Dislike"
            if st.button(dis_label, key=f"dis_{item['id']}_{idx}"):
                action = "remove" if disliked else "dislike"
                submit_feedback(item["id"], action)
                st.rerun()
        with fb_col3:
            pop_pct = item.get("popularity", 0)
            st.markdown(f'<div style="color:#4a5568; font-size:0.78rem; padding-top:0.4rem;">🔥 {pop_pct}% popularity</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

def main():
    # Load metadata
    meta = fetch_metadata()
    if not meta:
        st.warning("Could not load metadata from API. Showing demo mode.")
        all_tags = ["python", "machine learning", "design", "backend", "startup", "data science"]
        all_categories = ["Technology", "AI/ML", "Design", "Business"]
    else:
        all_tags = meta.get("all_tags", [])
        all_categories = meta.get("all_categories", [])

    # ── Hero header ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding: 2rem 0 1rem;">
        <div class="hero-title">RecommendAI</div>
        <div class="hero-sub">Similarity-based recommendations with explainable AI · Built for builders</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats pills ──────────────────────────────────────────────────────
    n_liked = len(st.session_state.feedback["liked_ids"])
    n_disliked = len(st.session_state.feedback["disliked_ids"])
    n_recs = len(st.session_state.recommendations or [])

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill">
            <div class="val">{len(all_tags)}</div>
            <div class="lbl">Available Tags</div>
        </div>
        <div class="stat-pill">
            <div class="val">{len(all_categories)}</div>
            <div class="lbl">Categories</div>
        </div>
        <div class="stat-pill">
            <div class="val">{n_recs}</div>
            <div class="lbl">Results Shown</div>
        </div>
        <div class="stat-pill">
            <div class="val">{n_liked}</div>
            <div class="lbl">Liked</div>
        </div>
        <div class="stat-pill">
            <div class="val">{n_disliked}</div>
            <div class="lbl">Disliked</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar — Preferences ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="section-label">Your Preferences</div>', unsafe_allow_html=True)

        # Trending suggestions
        if meta and meta.get("trending_items"):
            trending_tags = []
            for t in meta["trending_items"][:3]:
                trending_tags.extend(t["tags"][:2])
            trending_tags = list(dict.fromkeys(trending_tags))[:6]
            st.markdown('<div class="section-label" style="margin-top:0.5rem;">🔥 Trending Tags</div>', unsafe_allow_html=True)
            chips_html = " ".join(f'<span class="tag-chip">{t}</span>' for t in trending_tags)
            st.markdown(chips_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Tag selector
        st.markdown('<div class="section-label">Select Interests</div>', unsafe_allow_html=True)
        selected_tags = st.multiselect(
            "Interest Tags",
            options=all_tags,
            default=[],
            label_visibility="collapsed",
            help="Select tags that match your interests",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Category selector
        st.markdown('<div class="section-label">Focus Categories</div>', unsafe_allow_html=True)
        selected_categories = st.multiselect(
            "Categories",
            options=all_categories,
            default=[],
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Experience level
        st.markdown('<div class="section-label">Experience Level</div>', unsafe_allow_html=True)
        level = st.selectbox(
            "Level",
            options=["Any", "beginner", "intermediate", "advanced"],
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Number of recommendations
        st.markdown('<div class="section-label">Results Count</div>', unsafe_allow_html=True)
        top_k = st.slider("Results", 3, 15, 8, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # CTA button
        run_btn = st.button("✦ Get Recommendations", use_container_width=True)

        st.markdown("---")

        # Feedback summary
        if n_liked or n_disliked:
            st.markdown('<div class="section-label">Your Feedback</div>', unsafe_allow_html=True)
            if n_liked:
                st.markdown(f'<span class="tag-chip matched">💙 {n_liked} Liked</span>', unsafe_allow_html=True)
            if n_disliked:
                st.markdown(f'<span class="tag-chip" style="color:#fc8181;border-color:rgba(252,129,129,0.3)">🚫 {n_disliked} Disliked</span>', unsafe_allow_html=True)
            if st.button("Reset Feedback", use_container_width=True):
                st.session_state.feedback = {"liked_ids": [], "disliked_ids": []}
                st.session_state.recommendations = None
                st.rerun()

        st.markdown("---")
        st.markdown("""
        <div style="color:#4a5568; font-size:0.75rem; line-height:1.6;">
            <strong style="color:#718096;">How it works</strong><br>
            Uses Jaccard overlap, TF-IDF weighted scoring, and popularity bonuses.
            Feedback adjusts future recommendations in real-time.
        </div>
        """, unsafe_allow_html=True)

    # ── Main panel ────────────────────────────────────────────────────────
    if run_btn:
        with st.spinner(""):
            # Show shimmer loaders
            shimmer_html = "".join(f'<div class="shimmer-card"></div>' for _ in range(3))
            shimmer_placeholder = st.empty()
            shimmer_placeholder.markdown(shimmer_html, unsafe_allow_html=True)
            time.sleep(0.4)  # Simulate processing feel

            result = fetch_recommendations(selected_tags, selected_categories, level, top_k)
            shimmer_placeholder.empty()

        if result:
            st.session_state.recommendations = result.get("recommendations", [])
            st.session_state.last_query_tags = result.get("query_tags", [])
            st.session_state.is_cold_start = result.get("is_cold_start", False)

    # ── Render recommendations ────────────────────────────────────────────
    if st.session_state.recommendations:
        recs = st.session_state.recommendations
        query_tags = st.session_state.last_query_tags
        is_cold = st.session_state.is_cold_start

        # Header
        if is_cold or not query_tags:
            st.markdown("""
            <div style="background:rgba(246,173,85,0.08); border:1px solid rgba(246,173,85,0.2);
                 border-radius:14px; padding:1rem 1.4rem; margin-bottom:1.5rem; color:#f6ad55; font-size:0.88rem;">
                ✦ <strong>No preferences detected</strong> — showing trending picks across all categories.
                Add some tags or categories to get personalized results.
            </div>
            """, unsafe_allow_html=True)
        else:
            query_chips = " ".join(f'<span class="tag-chip matched">✦ {t}</span>' for t in query_tags[:8])
            st.markdown(f"""
            <div style="margin-bottom:1.5rem;">
                <div class="section-label">Query Profile</div>
                {query_chips}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-label">{len(recs)} Recommendations · Ranked by relevance</div>', unsafe_allow_html=True)

        # Two-column grid for cards
        cols = st.columns(2, gap="medium")
        for i, rec in enumerate(recs):
            with cols[i % 2]:
                render_recommendation_card(rec, i)

    elif not run_btn:
        # Empty state
        st.markdown("""
        <div style="text-align:center; padding:5rem 2rem; animation: fadeSlideIn 0.6s ease;">
            <div style="font-size:4rem; margin-bottom:1rem; opacity:0.3;">◈</div>
            <div style="font-family:'Syne',sans-serif; font-size:1.4rem; color:#4a5568; margin-bottom:0.5rem;">
                Select your interests and hit <em>Get Recommendations</em>
            </div>
            <div style="color:#2d3748; font-size:0.9rem;">
                Pick tags, categories, and experience level from the sidebar
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show trending teaser
        if meta and meta.get("trending_items"):
            st.markdown('<div class="section-label" style="text-align:center; margin-top:2rem;">🔥 Trending Right Now</div>', unsafe_allow_html=True)
            t_cols = st.columns(3)
            for i, item in enumerate(meta["trending_items"][:3]):
                with t_cols[i]:
                    st.markdown(f"""
                    <div class="glass-card" style="animation-delay:{i*0.1}s">
                        <div class="tag-chip cat-chip">{item['category']}</div>
                        <div style="font-family:'Syne',sans-serif; font-weight:700; margin:0.6rem 0 0.3rem;
                             font-size:0.95rem; color:#e2e8f0;">{item['title']}</div>
                        <div style="color:#718096; font-size:0.78rem;">⭐ {item['rating']} · 🔥 {item['popularity']}%</div>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()