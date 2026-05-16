"""
JUNK — career hub.
Landing page for the dark proteome game suite.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from src.career import (
    GAMES,
    PATHS,
    init_career,
    has_completed,
    paths_taken,
    render_inventory_sidebar,
    vigilante_unlocked,
)

st.set_page_config(page_title="JUNK", page_icon="🧬", layout="wide")
init_career()

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a10; color: #d4d4d8; }
[data-testid="stSidebar"] { background: #06060c; border-right: 1px solid #1a1a2e; }

.junk-title {
    font-size: 4rem; font-weight: 900; letter-spacing: 0.25em;
    color: #f59e0b; line-height: 1; text-align: center;
}
.junk-sub {
    font-size: 0.95rem; color: #52525b; letter-spacing: 0.3em;
    text-transform: uppercase; margin-top: 0.3rem; text-align: center;
}
.game-card {
    background: #12121e; border: 1px solid #2e2e4e;
    padding: 1.2rem 1.4rem; border-radius: 6px;
    height: 100%; transition: border-color 0.2s;
}
.game-card.complete { border-color: #166534; background: #0a1a10; }
.game-card-icon { font-size: 2rem; margin-bottom: 0.4rem; }
.game-card-title { font-size: 1.15rem; font-weight: 800; color: #e4e4e7; margin-bottom: 0.4rem; }
.game-card-desc { font-size: 0.85rem; color: #94a3b8; line-height: 1.6; }
.game-card-status { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em;
    text-transform: uppercase; margin-top: 0.8rem; }
.game-card-status.done { color: #22c55e; }
.game-card-status.new  { color: #71717a; }
.path-row { background: #12121e; border-left: 3px solid #f59e0b;
    padding: 0.6rem 1rem; margin: 0.4rem 0; border-radius: 0 4px 4px 0; }
.path-name { font-weight: 700; font-size: 0.95rem; color: #e4e4e7; }
.path-blurb { font-size: 0.82rem; color: #94a3b8; margin-top: 0.25rem; line-height: 1.6; }
.locked-banner {
    background: #1a0a00; border: 1px solid #92400e;
    padding: 0.7rem 1rem; border-radius: 4px; margin: 0.5rem 0;
    color: #f59e0b; font-size: 0.85rem;
}
.unlocked-banner {
    background: #0a1a10; border: 1px solid #166534;
    padding: 0.9rem 1.1rem; border-radius: 4px; margin: 0.5rem 0;
    color: #22c55e; font-size: 0.9rem; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🧬 JUNK")
    st.caption("Game Suite")
    st.markdown("---")
    render_inventory_sidebar()
    st.markdown("---")
    c = st.session_state.career
    st.markdown(f"**Completed runs:** {c['completed_runs']}")
    if st.button("↩ Reset career", use_container_width=True):
        del st.session_state["career"]
        st.rerun()

# ── Title ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="junk-title">JUNK</div>', unsafe_allow_html=True)
st.markdown('<div class="junk-sub">The Dark Proteome Game Suite</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Intro ─────────────────────────────────────────────────────────────────────

st.markdown("""
Three interconnected games about microproteins encoded in "junk" DNA — the dark proteome —
and what happens when a corporation weaponizes a Nature paper.

**Items you collect in one game carry into the others. Decisions you make in one are
remembered by the others.** The Analyst has four possible paths. One of them is hidden:
it can only be reached after you've already completed at least one of the games.
""")

# ── Games ─────────────────────────────────────────────────────────────────────

st.markdown("### Where to begin")

GAME_BLURBS = {
    "investigation": (
        "Five chapters following the scientists who exposed Project NEURO-LATTICE. "
        "Real data from the Nature 2026 supplementary materials, woven into a narrative puzzle."
    ),
    "lockdown": (
        "Escape room across four locations from the book. Collect items, combine them, "
        "unlock rooms, decide what to publish."
    ),
    "analyst": (
        "You work for NovaBridge. Five chapters of the same story from the inside. "
        "Four endings — but only three are visible the first time you play."
    ),
}

cols = st.columns(3)
buttons = [
    (cols[0], "investigation", "pages/02_The_Investigation.py"),
    (cols[1], "lockdown",      "pages/03_The_Lockdown.py"),
    (cols[2], "analyst",       "pages/04_The_Analyst.py"),
]

for col, game_id, page in buttons:
    with col:
        done = has_completed(game_id)
        cls = "game-card complete" if done else "game-card"
        status_cls, status_text = ("done", "✓ Completed") if done else ("new", "○ Not yet played")
        meta = GAMES[game_id]
        st.markdown(
            f'<div class="{cls}">'
            f'<div class="game-card-icon">{meta["icon"]}</div>'
            f'<div class="game-card-title">{meta["name"]}</div>'
            f'<div class="game-card-desc">{GAME_BLURBS[game_id]}</div>'
            f'<div class="game-card-status {status_cls}">{status_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Open {meta['name']} →", key=f"open_{game_id}", use_container_width=True):
            st.switch_page(page)

# ── Exploration page (Alissa's original tool) ────────────────────────────────

st.markdown("---")
st.markdown("##### Or explore the proteome directly")
st.caption("The classifier, structure predictor, and paper-comparison tool from the base repo.")
if st.button("🔬 Open the explorer", use_container_width=False):
    st.switch_page("pages/01_Explore_Proteome.py")

# ── Career so far ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Your career so far")

taken = paths_taken()
if not taken:
    st.caption("No paths completed yet. Play any of the games above to begin.")
else:
    for p in taken:
        meta = PATHS[p]
        st.markdown(
            f'<div class="path-row">'
            f'<div class="path-name">{meta["icon"]} {meta["name"]}</div>'
            f'<div class="path-blurb">{meta["blurb"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# Vigilante hint
st.markdown("---")
if vigilante_unlocked():
    st.markdown(
        '<div class="unlocked-banner">🕯 The fourth path is available. Re-enter The Analyst.</div>',
        unsafe_allow_html=True,
    )
elif st.session_state.career["completed_runs"] >= 1:
    st.markdown(
        '<div class="locked-banner">A fourth path exists. The right combination of choices opens it. '
        'You will know if you find it.</div>',
        unsafe_allow_html=True,
    )
