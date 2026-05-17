"""
Shared career state across all JUNK games.

Pages import this module and use the helpers below to read/write
st.session_state.career. Because Streamlit multipage apps share session
state across pages within one browser session, items collected and
decisions made in one game persist into the others.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import streamlit as st

# Save file lives in the working directory of `streamlit run`.
# Best-effort persistence — survives browser close on local machines.
# Streamlit Cloud's filesystem is ephemeral; the file disappears on app restart there.
_SAVE_PATH = Path(".career_save.json")


def _load_career_from_disk():
    if _SAVE_PATH.exists():
        try:
            with _SAVE_PATH.open() as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _save_career_to_disk():
    if "career" not in st.session_state:
        return
    try:
        with _SAVE_PATH.open("w") as f:
            json.dump(st.session_state.career, f)
    except OSError:
        pass  # filesystem may be read-only — silent fail is fine

# ── Item catalog ──────────────────────────────────────────────────────────────

ITEMS = {
    "screenshot": {
        "icon": "📸",
        "name": "Query Log Screenshot",
        "desc": "Eight months of automated ORBLq queries against HelixScreen live data. Saved offline before clearing the log.",
        "source": "NovaBridge — Legacy Access",
    },
    "park_keycard": {
        "icon": "🪪",
        "name": "Dr. Park's Keycard",
        "desc": "Visiting researcher badge, Langley-Stanford Institute for Genomic Medicine. Magnetic strip still active.",
        "source": "NovaBridge — Lobby encounter",
    },
    "park_trust": {
        "icon": "🤝",
        "name": "Dr. Park's Trust",
        "desc": "You stopped to talk to her. She remembers your face. She'll answer if you write.",
        "source": "NovaBridge — Lobby encounter",
    },
    "nb_bonus": {
        "icon": "💵",
        "name": "NovaBridge Severance",
        "desc": "$40K, post-tax. Cleared. Yours.",
        "source": "NovaBridge — Exit Protocol",
    },
    "investigation_dossier": {
        "icon": "📁",
        "name": "Investigation Dossier",
        "desc": "Conservation analysis, peptide identification, variant-adversity correlation. Peer-reviewable. Yours.",
        "source": "The Investigation",
    },
}

# ── Path catalog ──────────────────────────────────────────────────────────────

PATHS = {
    "bystander": {
        "name": "The Bystander",
        "icon": "👁",
        "blurb": "You read about the investigation in a science newsletter. You closed the tab.",
    },
    "whistleblower": {
        "name": "The Whistleblower",
        "icon": "📡",
        "blurb": "You leaked the data publicly. Years later, your name surfaces in a hearing transcript.",
    },
    "confidant": {
        "name": "The Confidant",
        "icon": "🤝",
        "blurb": "You returned her keycard, and stayed to talk. The preprint cites you in the acknowledgements.",
    },
    "vigilante": {
        "name": "The Vigilante",
        "icon": "🕯",
        "blurb": "You appeared compliant for six months. Then you used everything you'd quietly gathered.",
    },
}

# ── Game catalog ──────────────────────────────────────────────────────────────

GAMES = {
    "investigation": {"name": "The Investigation", "icon": "🧬"},
    "lockdown": {"name": "The Lockdown", "icon": "🔒"},
    "analyst": {"name": "The Analyst", "icon": "🏢"},
}

# ── State init ────────────────────────────────────────────────────────────────

_DEFAULT_CAREER = {
    "items": [],
    "games_completed": {},          # game_id → ending_id
    "paths_taken": [],              # list of path ids (ordered)
    "completed_runs": 0,            # any-game completions, for Vigilante gating
    "analyst_suspicion_at_end": None,
    "yuna_encounter": None,         # "walked_away", "talked", "kept" — set in Analyst Ch3
}


def init_career():
    if "career" not in st.session_state:
        saved = _load_career_from_disk()
        if saved is not None:
            # Merge with defaults so newer keys we add don't break old save files.
            # Deep-copy defaults so inner lists/dicts aren't shared with the module-level constant.
            merged = copy.deepcopy(_DEFAULT_CAREER)
            merged.update(saved)
            st.session_state.career = merged
        else:
            st.session_state.career = copy.deepcopy(_DEFAULT_CAREER)

# ── Item helpers ──────────────────────────────────────────────────────────────

def add_item(item_id: str):
    init_career()
    if item_id in ITEMS and item_id not in st.session_state.career["items"]:
        st.session_state.career["items"].append(item_id)
        _save_career_to_disk()

def has_item(item_id: str) -> bool:
    init_career()
    return item_id in st.session_state.career["items"]

def items_owned() -> list[str]:
    init_career()
    return list(st.session_state.career["items"])

# ── Completion helpers ────────────────────────────────────────────────────────

def mark_game_complete(game_id: str, ending_id: str, **extra):
    init_career()
    c = st.session_state.career
    # Only count a NEW completion if this game wasn't completed before
    if game_id not in c["games_completed"]:
        c["completed_runs"] += 1
    c["games_completed"][game_id] = ending_id
    for k, v in extra.items():
        c[k] = v
    _save_career_to_disk()

def has_completed(game_id: str) -> bool:
    init_career()
    return game_id in st.session_state.career["games_completed"]

def mark_path(path_id: str):
    init_career()
    if path_id in PATHS and path_id not in st.session_state.career["paths_taken"]:
        st.session_state.career["paths_taken"].append(path_id)
        _save_career_to_disk()

def paths_taken() -> list[str]:
    init_career()
    return list(st.session_state.career["paths_taken"])

# ── Path detection ────────────────────────────────────────────────────────────

def vigilante_unlocked() -> bool:
    """
    Secret-path gate. All four must hold:
      - at least one prior game completed (Investigation OR Lockdown OR a previous Analyst run)
      - 📸 screenshot
      - 🪪 keycard
      - 💵 bonus
      - suspicion at the end of the Analyst game was low (< 30)
    """
    init_career()
    c = st.session_state.career
    return (
        c["completed_runs"] >= 1
        and has_item("screenshot")
        and has_item("park_keycard")
        and has_item("nb_bonus")
        and (c.get("analyst_suspicion_at_end") or 0) < 30
    )

# ── Sidebar widget ────────────────────────────────────────────────────────────

INVENTORY_CSS = """
<style>
.career-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.2em;
    color: #52525b; text-transform: uppercase; margin: 0.4rem 0 0.3rem;
}
.career-item {
    background: #12121e; border: 1px solid #2e2e4e;
    padding: 0.5rem 0.7rem; border-radius: 4px; margin: 0.25rem 0;
}
.career-item .icon { font-size: 1.05rem; margin-right: 0.4rem; }
.career-item .name { font-weight: 600; font-size: 0.85rem; color: #e4e4e7; }
.career-item .desc { font-size: 0.7rem; color: #71717a; margin-top: 0.2rem; line-height: 1.55; }
.career-path {
    font-size: 0.78rem; padding: 0.25rem 0.5rem; margin: 0.15rem 0;
    color: #a1a1aa; background: #0d0d14; border-radius: 3px;
}
</style>
"""

def render_inventory_sidebar(show_paths: bool = True):
    """
    Call inside `with st.sidebar:` to render the cross-game inventory panel.
    Safe to call from any page; if no items yet, renders a quiet placeholder.
    """
    init_career()
    st.markdown(INVENTORY_CSS, unsafe_allow_html=True)

    items = items_owned()
    st.markdown('<div class="career-label">Career Inventory</div>', unsafe_allow_html=True)
    if not items:
        st.caption("Nothing accumulated yet.")
    else:
        for item_id in items:
            item = ITEMS[item_id]
            st.markdown(
                f'<div class="career-item">'
                f'<span class="icon">{item["icon"]}</span>'
                f'<span class="name">{item["name"]}</span>'
                f'<div class="desc">{item["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if show_paths:
        taken = paths_taken()
        st.markdown('<div class="career-label">Paths Taken</div>', unsafe_allow_html=True)
        if not taken:
            st.caption("None yet.")
        else:
            for p in taken:
                meta = PATHS[p]
                st.markdown(
                    f'<div class="career-path">{meta["icon"]} {meta["name"]}</div>',
                    unsafe_allow_html=True,
                )

    # Diagnostic inspector — quietly available, off by default
    with st.expander("⚙ Inspect career state", expanded=False):
        c = st.session_state.career
        st.markdown(f"**Completed runs:** {c['completed_runs']}")
        st.markdown(f"**Games completed:** {dict(c['games_completed']) or 'none'}")
        st.markdown(f"**Items:** {c['items'] or 'none'}")
        st.markdown(f"**Paths taken:** {c['paths_taken'] or 'none'}")
        st.markdown(f"**Analyst suspicion at end:** {c.get('analyst_suspicion_at_end')}")
        st.markdown(f"**Yuna encounter:** {c.get('yuna_encounter')}")
