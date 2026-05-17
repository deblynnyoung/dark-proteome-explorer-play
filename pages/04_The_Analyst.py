"""
pages/04_The_Analyst.py
JUNK: The Analyst — NovaBridge Internal
A morally inverted thriller. You are a NovaBridge data analyst.
Five chapters. You start thinking it's legitimate pharmaceutical research.
Your choices accumulate. NovaBridge is tracking you, too.
"""

import os
import random
import streamlit as st
import pandas as pd

from src.career import (
    add_item,
    has_item,
    init_career,
    mark_game_complete,
    mark_path,
    render_inventory_sidebar,
    vigilante_unlocked,
)

st.set_page_config(
    page_title="JUNK: The Analyst",
    page_icon="🏢",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #080c14; color: #cbd5e1; }
[data-testid="stSidebar"] { background: #050810; border-right: 1px solid #0ea5e9; }

.nb-header {
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.35em;
    color: #0ea5e9; text-transform: uppercase; margin-bottom: 0.1rem;
}
.nb-title {
    font-size: 2rem; font-weight: 900; color: #f1f5f9; line-height: 1.1; margin-bottom: 0.25rem;
}
.chapter-header {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.25em;
    color: #0ea5e9; text-transform: uppercase; margin-bottom: 0.1rem;
}
.chapter-title {
    font-size: 2rem; font-weight: 800; color: #f1f5f9; margin-bottom: 1.5rem; line-height: 1.1;
}
.memo {
    background: #0d1520; border: 1px solid #1e3a5f;
    padding: 1.2rem 1.5rem; border-radius: 4px; margin: 1rem 0 1.5rem;
    font-size: 0.95rem; line-height: 1.75; color: #94a3b8;
}
.memo-header {
    font-size: 0.7rem; letter-spacing: 0.2em; color: #0ea5e9;
    font-weight: 700; text-transform: uppercase; margin-bottom: 0.75rem;
    padding-bottom: 0.5rem; border-bottom: 1px solid #1e3a5f;
}
.terminal {
    background: #030712; border: 1px solid #1e3a5f;
    font-family: 'Courier New', monospace; padding: 1rem 1.2rem;
    border-radius: 4px; margin: 0.5rem 0; font-size: 0.82rem;
    color: #22c55e; line-height: 1.65;
}
.terminal-prompt { color: #64748b; }
.terminal-output { color: #94a3b8; }
.terminal-flag { color: #f59e0b; }
.terminal-alert { color: #ef4444; }
.doc-block {
    background: #0d1520; border: 1px solid #1e3a5f;
    padding: 1rem 1.2rem; border-radius: 4px; margin: 0.4rem 0;
    font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;
}
.doc-block.redacted { color: #1e3a5f; background: #050810; border-color: #0f172a; }
.doc-block.flagged { border-color: #f59e0b; background: #1a1200; }
.doc-block.danger { border-color: #ef4444; background: #1a0000; }
.choice-header {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.2em;
    color: #64748b; text-transform: uppercase; margin: 1.5rem 0 0.5rem;
}
.sidebar-field {
    font-size: 0.75rem; color: #64748b; margin: 0.1rem 0;
}
.sidebar-value {
    font-size: 0.82rem; color: #cbd5e1; font-weight: 600;
}
.sidebar-alert {
    font-size: 0.82rem; color: #ef4444; font-weight: 600;
}
.chapter-nav { padding: 0.3rem 0.6rem; margin: 0.1rem 0; border-radius: 3px; font-size: 0.82rem; }
.chapter-nav.done { background: #0f2a1a; color: #22c55e; }
.chapter-nav.now { background: #0d1e35; color: #0ea5e9; border-left: 2px solid #0ea5e9; padding-left: 0.5rem; }
.chapter-nav.locked { color: #1e3a5f; }
.ending-block {
    background: #0d1520; border: 1px solid #1e3a5f;
    padding: 1.5rem 2rem; border-radius: 6px; margin: 1.5rem 0;
    font-size: 0.97rem; line-height: 1.85; color: #94a3b8;
}
.ending-block.leak { border-color: #22c55e; background: #0a1f10; }
.ending-block.flag { border-color: #ef4444; background: #1a0000; }
.ending-block.gone { border-color: #64748b; background: #0d0d14; }
.ending-block.stayed { border-color: #0ea5e9; background: #050e1a; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading Lattice Analytics pipeline…")
def load_df():
    candidates = [
        "data/41586_2026_10459_MOESM9_ESM_structural_predictions.csv",
        "data/41586_2026_10459_MOESM9_ESM.xlsx",
        "41586_2026_10459_MOESM9_ESM.xlsx",
        os.path.join(os.path.dirname(__file__), "..", "41586_2026_10459_MOESM9_ESM.xlsx"),
    ]
    for p in candidates:
        if os.path.exists(p):
            df = pd.read_csv(p) if p.endswith(".csv") else pd.read_excel(
                p, sheet_name="Structural predictions", engine="openpyxl"
            )
            df["detected"] = df["tier"].str.match(r"Tier [123]", na=False).astype(int)
            df["length"] = pd.to_numeric(df["length"], errors="coerce")
            df["PhyloCSF.primates"] = pd.to_numeric(df["PhyloCSF.primates"], errors="coerce")
            return df
    return None

# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    for k, v in {
        "chapter": 1,
        "suspicion": 0,       # NovaBridge's internal score — not shown to player
        "moral_score": 0,     # player's moral clarity — shown at end
        "choices": {},        # chapter_id → choice key
        "ch1_done": False,
        "ch2_done": False,
        "ch3_done": False,
        "ch4_done": False,
        "ch5_done": False,
        "ch6_done": False,
        "ch7_done": False,
        "yuna_done": False,   # Ch3 lobby encounter resolved
        "examined": [],
        "ended": False,
        "ending_type": None,
        "clearance_level": 2,
        "ever_flagged": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
init_career()

# ── Helpers ───────────────────────────────────────────────────────────────────

def record_choice(chapter, key, suspicion_delta, moral_delta):
    st.session_state.choices[chapter] = key
    st.session_state.suspicion = max(0, min(100, st.session_state.suspicion + suspicion_delta))
    st.session_state.moral_score = max(0, min(100, st.session_state.moral_score + moral_delta))
    if st.session_state.suspicion >= 60 and st.session_state.clearance_level == 2:
        st.session_state.clearance_level = 1
        st.session_state.ever_flagged = True

def advance(chapter_key, next_chapter):
    setattr(st.session_state, chapter_key, True)
    st.session_state[chapter_key] = True
    st.session_state.chapter = next_chapter
    st.rerun()

def chosen(chapter):
    return st.session_state.choices.get(chapter)

# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown('<div class="nb-header">NovaBridge Systems</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:1.1rem;font-weight:800;color:#0ea5e9;margin-bottom:1rem">Employee Portal</div>', unsafe_allow_html=True)
        st.markdown("---")

        cl = st.session_state.clearance_level
        cl_color = "#ef4444" if cl == 1 else "#22c55e"
        st.markdown(f'<div class="sidebar-field">Employee</div><div class="sidebar-value">NB-ANALYST-4471</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-field">Project</div><div class="sidebar-value">NEURO-LATTICE</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-field">Clearance</div><div style="font-size:0.82rem;font-weight:600;color:{cl_color}">Level {cl}</div>', unsafe_allow_html=True)
        if cl == 1:
            st.markdown('<div style="font-size:0.7rem;color:#ef4444;margin-top:0.2rem">⚠ Under review — IT notified</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sidebar-field" style="margin-bottom:0.4rem">Report Status</div>', unsafe_allow_html=True)

        steps = [
            (1, "Orientation"),
            (2, "Legacy Access"),
            (3, "OMEGA_COHORT"),
            (4, "Compound Brief"),
            (5, "Exit Protocol"),
        ]
        ch = st.session_state.chapter
        for n, label in steps:
            done = st.session_state.get(f"ch{n}_done", False)
            current = ch == n
            if done:
                cls, icon = "done", "✓"
            elif current:
                cls, icon = "now", "▶"
            else:
                cls, icon = "locked", "○"
            st.markdown(
                f'<div class="chapter-nav {cls}">{icon} {label}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown('<div class="sidebar-field">Performance Metric</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-value">[REDACTED — HR access only]</div>', unsafe_allow_html=True)

        st.markdown("---")
        render_inventory_sidebar()
        st.markdown("---")
        if st.button("↩ Restart this game", use_container_width=True):
            # Only clear Analyst-specific state, preserve career inventory
            preserve = st.session_state.get("career")
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            if preserve is not None:
                st.session_state["career"] = preserve
            st.rerun()

# ── Title ─────────────────────────────────────────────────────────────────────

def title_block():
    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 0.25rem">
        <div style="font-size:0.7rem;letter-spacing:0.4em;color:#0ea5e9;font-weight:700;text-transform:uppercase">NovaBridge Systems — Internal</div>
        <div style="font-size:3rem;font-weight:900;letter-spacing:0.15em;color:#f1f5f9;line-height:1;margin-top:0.3rem">THE ANALYST</div>
        <div style="font-size:0.8rem;color:#334155;letter-spacing:0.3em;text-transform:uppercase;margin-top:0.2rem">Project NEURO-LATTICE // Confidential</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# ── Chapter 1 — Orientation ───────────────────────────────────────────────────

def chapter_1():
    st.markdown('<div class="chapter-header">Chapter 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">Orientation</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    <div class="memo-header">NovaBridge Systems — New Analyst Onboarding // Project NEURO-LATTICE</div>
    Welcome. You've been assigned to validate the Lattice Analytics data pipeline for Phase II
    of Project NEURO-LATTICE. Your predecessor, Yael Ostrovsky, has been placed on leave.
    Her terminal access has been transferred to you.
    <br><br>
    Your task is straightforward: confirm that the pipeline is pulling correctly from HelixScreen's
    peptidome atlas, that the compound validation queries return clean output, and that the
    NL-7 trial cohort data is formatted correctly for the regulatory submission.
    <br><br>
    You have Level 2 clearance. Do not query partitions outside your assignment scope.
    <br><br>
    <em style="color:#64748b">— Dr. C. Weiss, Head of Data Infrastructure, NovaBridge Systems</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Run the onboarding query to verify your access:**")

    st.markdown("""
    <div class="terminal">
    <span class="terminal-prompt">NB-LATTICE > </span>SELECT compound_id, trial_phase, cohort_size, status FROM nl7_trial WHERE trial_phase = 'II'<br><br>
    <span class="terminal-output">compound_id  | trial_phase | cohort_size | status<br>
    -------------|-------------|-------------|----------<br>
    NL-7         | II          | 847         | ACTIVE<br>
    NL-7-VAR     | I           | 12          | SUSPENDED<br>
    <br>
    2 rows returned. Query time: 0.04s.<br>
    Clearance: Level 2 — access confirmed.</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("NL-7-VAR is listed but the trial is suspended. You weren't briefed on a variant compound.")

    if "ch1_examined" not in st.session_state:
        st.session_state.ch1_examined = False

    if st.button("🔍 Query NL-7-VAR trial record", key="ch1_examine", disabled=st.session_state.ch1_examined):
        st.session_state.ch1_examined = True
        st.rerun()

    if st.session_state.ch1_examined:
        st.markdown("""
        <div class="terminal">
        <span class="terminal-prompt">NB-LATTICE > </span>SELECT * FROM nl7_trial WHERE compound_id = 'NL-7-VAR'<br><br>
        <span class="terminal-output">compound_id:  NL-7-VAR<br>
        trial_phase:  I<br>
        cohort_size:  12<br>
        status:       SUSPENDED<br>
        suspension_reason: [REDACTED — Level 3 required]<br>
        date_suspended:   2026-03-11<br>
        authorized_by:    C. Weiss</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("The suspension reason requires Level 3 clearance. You're Level 2. You log it and move on.")

    st.markdown("---")
    st.markdown('<div class="choice-header">How do you proceed?</div>', unsafe_allow_html=True)

    choice = st.radio(
        "Your onboarding task is to validate the pipeline and submit a report.",
        [
            "A — Run the validation, submit the standard onboarding report, flag nothing.",
            "B — Note the NL-7-VAR suspension in your report and request the suspension reason before signing off.",
            "C — Submit the report. Separately, look up C. Weiss's authorization history.",
        ],
        index=None,
        key="ch1_radio",
    )

    if choice:
        if choice.startswith("A"):
            st.markdown('<div class="doc-block">Standard report submitted. Your supervisor acknowledges receipt within ten minutes. Fast turnaround noted.</div>', unsafe_allow_html=True)
            delta_s, delta_m = -5, 0
        elif choice.startswith("B"):
            st.markdown('<div class="doc-block flagged">You flag the suspended trial. The response comes back three hours later: <em>"NL-7-VAR is outside your assignment scope. Proceed with NL-7 Phase II validation only. — C. Weiss."</em> No further information.</div>', unsafe_allow_html=True)
            delta_s, delta_m = +10, +15
        else:
            st.markdown('<div class="doc-block flagged">C. Weiss has authorized 14 access suspensions in the past 18 months. Yael Ostrovsky is the most recent. The others are listed only as employee IDs.</div>', unsafe_allow_html=True)
            delta_s, delta_m = +15, +20

        if not st.session_state.ch1_done:
            record_choice(1, choice[0], delta_s, delta_m)
            st.session_state.ch1_done = True

        if st.button("Continue to Chapter 2 →", key="ch1_next"):
            st.session_state.chapter = 2
            st.rerun()

# ── Chapter 2 — Legacy Access ─────────────────────────────────────────────────

def chapter_2(df):
    st.markdown('<div class="chapter-header">Chapter 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">Legacy Access</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    <div class="memo-header">NovaBridge Systems — Terminal Handoff // NB-ANALYST-4471</div>
    Your workstation includes Yael Ostrovsky's terminal session history.
    Standard procedure is to clear it before beginning your own work.
    <br><br>
    The query log is visible. Eight months of automated queries against the HelixScreen
    peptidome atlas. You weren't briefed on any HelixScreen integration.
    <br><br>
    The NL-7 trial runs on a separate internal cohort. These queries are pulling from something else.
    </div>
    """, unsafe_allow_html=True)

    if "ch2_log_opened" not in st.session_state:
        st.session_state.ch2_log_opened = False
    if "ch2_query_run" not in st.session_state:
        st.session_state.ch2_query_run = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Open query log", key="ch2_open_log", disabled=st.session_state.ch2_log_opened):
            st.session_state.ch2_log_opened = True
            st.rerun()
    with col2:
        if st.session_state.ch2_log_opened:
            if st.button("▶ Run the query yourself", key="ch2_run_query", disabled=st.session_state.ch2_query_run):
                st.session_state.ch2_query_run = True
                st.rerun()

    if st.session_state.ch2_log_opened:
        st.markdown("""
        <div class="terminal">
        <span class="terminal-prompt">QUERY LOG — YO-TERMINAL // last 10 entries</span><br><br>
        <span class="terminal-output">2026-02-14 03:12:41  SELECT patient_id, orf_id, ORBLq_tier, city FROM helixscreen_live WHERE ORBLq_tier = 'Ω'<br>
        2026-03-01 03:14:22  SELECT patient_id, orf_id, ORBLq_tier, city FROM helixscreen_live WHERE ORBLq_tier = 'Ω'<br>
        2026-03-15 03:11:58  SELECT patient_id, orf_id, ORBLq_tier, city FROM helixscreen_live WHERE ORBLq_tier = 'Ω'<br>
        2026-04-01 03:13:02  SELECT patient_id, orf_id, ORBLq_tier, city FROM helixscreen_live WHERE ORBLq_tier = 'Ω'<br>
        <span class="terminal-flag">  [... 187 identical queries, automated, 3 AM local time, every 14 days ...]</span><br>
        2026-09-15 03:10:44  SELECT patient_id, orf_id, ORBLq_tier, city FROM helixscreen_live WHERE ORBLq_tier = 'Ω'<br>
        <br>
        <span class="terminal-alert">NOTE: helixscreen_live is not in your authorized data source list.</span></span>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.ch2_query_run:
        st.markdown("**Query result — live HelixScreen data:**")

        if df is not None:
            omega = df[df["detected"] == 1].head(8).copy()
            omega["patient_id"] = [f"HS-{random.randint(100000,999999)}" for _ in range(len(omega))]
            omega["city"] = random.choices(
                ["Portland, OR", "Seattle, WA", "Oakland, CA", "Denver, CO", "Chicago, IL", "Austin, TX"],
                k=len(omega)
            )
            omega["ORBLq_tier"] = "Ω"
            st.dataframe(
                omega[["patient_id", "orf_id", "ORBLq_tier", "city"]].rename(
                    columns={"orf_id": "orf_id (lead)"}
                ),
                use_container_width=True, hide_index=True,
            )
        else:
            st.markdown("""
            <div class="terminal">
            <span class="terminal-output">patient_id   | orf_id          | ORBLq_tier | city<br>
            -------------|-----------------|------------|------------------<br>
            HS-447821    | c10riboseqorf92 | Ω          | Portland, OR<br>
            HS-229041    | c10riboseqorf92 | Ω          | Seattle, WA<br>
            HS-881203    | c10riboseqorf92 | Ω          | Oakland, CA<br>
            HS-334092    | c10riboseqorf92 | Ω          | Denver, CO<br>
            ...<br>
            347 rows total.</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("These are not trial participants. These are live patient records from HelixScreen clinics. Routine immunopeptidomics screenings. They didn't consent to this query.")

    st.markdown("---")
    st.markdown('<div class="choice-header">The log is sitting right there. What do you do with it?</div>', unsafe_allow_html=True)

    choice = st.radio(
        "The previous analyst ran automated pulls against live patient data for eight months.",
        [
            "A — Clear the log as part of standard handoff. Not your query history, not your problem.",
            "B — Note it in your internal report as 'unauthorized legacy query activity requiring audit.'",
            "C — Screenshot the log and save it to personal storage before clearing.",
        ],
        index=None,
        key="ch2_radio",
    )

    if choice:
        if choice.startswith("A"):
            st.markdown('<div class="doc-block">Log cleared. Clean slate. Your performance metrics look good.</div>', unsafe_allow_html=True)
            delta_s, delta_m = -10, -15
        elif choice.startswith("B"):
            st.markdown('<div class="doc-block flagged">You flag the query log. IT security responds within the hour. The report is acknowledged and closed with the notation: <em>"Legacy activity within authorized scope. No further action required."</em> No one explains how HelixScreen became authorized scope.</div>', unsafe_allow_html=True)
            delta_s, delta_m = +15, +20
        else:
            st.markdown('<div class="doc-block flagged">Saved. You don\'t know what you\'re going to do with it. But it\'s somewhere NovaBridge doesn\'t control. <em style="color:#22c55e">📸 Query Log Screenshot added to your inventory.</em></div>', unsafe_allow_html=True)
            delta_s, delta_m = +20, +30
            add_item("screenshot")

        if not st.session_state.ch2_done:
            record_choice(2, choice[0], delta_s, delta_m)
            st.session_state.ch2_done = True

        if st.button("Continue to Chapter 3 →", key="ch2_next"):
            st.session_state.chapter = 3
            st.rerun()

# ── Chapter 3 — OMEGA_COHORT ──────────────────────────────────────────────────

def yuna_encounter():
    """Lobby scene before OMEGA_COHORT. Three-way fork sets career inventory."""
    st.markdown('<div class="chapter-header">Chapter 3 — Lobby</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">A Visitor</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    On your way back from the third-floor cafeteria, you cross the NovaBridge atrium.
    A woman ahead of you fumbles with a stack of folders, a coffee, and a visitor's
    keycard on a lanyard. The lanyard slips off the coffee tray; the keycard skitters
    across the marble and lands behind a row of planters near your feet. The folders
    fan out across the floor. She kneels to gather them, her back to you, swearing softly.
    <br><br>
    You stop at the planters. The keycard is right there. You pick it up.
    The badge photo is hers — the same face you'd recognize across a room.
    <br><br>
    <strong style="color:#cbd5e1">Dr. Yuna Park</strong><br>
    <span style="color:#64748b">Langley-Stanford Institute for Genomic Medicine — Visiting</span>
    <br><br>
    She hasn't looked up yet.
    </div>
    """, unsafe_allow_html=True)

    choice = st.radio(
        "What do you do?",
        [
            "A — Step around the planters. \"Excuse me — I think this is yours.\" Hand it back, smile, walk on.",
            "B — Step around the planters. Hand it back. Ask what brings her to NovaBridge. Stay for a minute.",
            "C — Slip it into your jacket pocket. Walk past her on the other side of the planters. By the time she straightens up, you're already at the elevators.",
        ],
        index=None,
        key="yuna_radio",
    )

    if choice:
        if choice.startswith("A"):
            st.markdown('<div class="doc-block">She looks up, surprised. She thanks you twice. The interaction lasts maybe ten seconds. You don\'t exchange names.</div>', unsafe_allow_html=True)
            st.session_state.career["yuna_encounter"] = "walked_away"
            delta_s, delta_m = 0, 0
        elif choice.startswith("B"):
            st.markdown('<div class="doc-block flagged">She looks up, surprised. You hand it back. She introduces herself — Yuna. She\'s here for a talk on HLA Class I bioinformatics, she says. NovaBridge invited her to consult.<br><br>She watches your face carefully when you say you work in Lattice Analytics. Something in her expression shifts. She gives you her university email before she leaves. <em>"In case you ever want to compare notes."</em> <em style="color:#22c55e">🤝 Dr. Park\'s Trust added to your inventory.</em></div>', unsafe_allow_html=True)
            st.session_state.career["yuna_encounter"] = "talked"
            add_item("park_trust")
            delta_s, delta_m = +5, +15
        else:
            st.markdown('<div class="doc-block flagged">She doesn\'t see you take it. By the time she\'s gathered her folders and started looking for the keycard, you\'re already in the elevator.<br><br>The magnetic strip stays active for 48 hours before her institution flags it missing and deactivates the credential. Plenty of time to clone the magnetic stripe and the embedded RFID. <em style="color:#22c55e">🪪 Dr. Park\'s Keycard added to your inventory.</em></div>', unsafe_allow_html=True)
            st.session_state.career["yuna_encounter"] = "kept"
            add_item("park_keycard")
            delta_s, delta_m = +10, -5  # ambiguous morally — you stole, but cleanly

        record_choice("yuna", choice[0], delta_s, delta_m)

        if st.button("Continue into Lattice Analytics →", key="yuna_next"):
            st.session_state.yuna_done = True
            st.rerun()


def chapter_3(df):
    if not st.session_state.yuna_done:
        yuna_encounter()
        return

    st.markdown('<div class="chapter-header">Chapter 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">OMEGA_COHORT</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    <div class="memo-header">Lattice Analytics — Partitioned Dataset // Level 2 Read Access</div>
    You found the partition while validating the pipeline structure.
    It wasn't in the documentation you were given.
    <br><br>
    Table name: <strong style="color:#f59e0b">OMEGA_COHORT</strong><br>
    Created: 2026-01-09<br>
    Owner: C. Weiss<br>
    Row count: 347<br>
    Last modified: 2026-10-01
    </div>
    """, unsafe_allow_html=True)

    if "ch3_schema" not in st.session_state:
        st.session_state.ch3_schema = False
    if "ch3_rows" not in st.session_state:
        st.session_state.ch3_rows = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 View table schema", key="ch3_schema_btn", disabled=st.session_state.ch3_schema):
            st.session_state.ch3_schema = True
            st.rerun()
    with col2:
        if st.session_state.ch3_schema:
            if st.button("🔍 View sample rows", key="ch3_rows_btn", disabled=st.session_state.ch3_rows):
                st.session_state.ch3_rows = True
                st.rerun()

    if st.session_state.ch3_schema:
        st.markdown("""
        <div class="terminal">
        <span class="terminal-prompt">NB-LATTICE > </span>DESCRIBE OMEGA_COHORT<br><br>
        <span class="terminal-output">patient_id            VARCHAR(20)<br>
        orf_id                VARCHAR(30)<br>
        ORBLq_tier            CHAR(1)<br>
        city                  VARCHAR(50)<br>
        adversity_score       FLOAT<br>
        approach              VARCHAR(20)<br>
        relocation_feasibility FLOAT<br>
        facility_code         VARCHAR(10)<br>
        <span class="terminal-flag">status                VARCHAR(20)  — values: FLAGGED, MONITORING, COMPLETED</span></span>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.ch3_rows:
        st.markdown("""
        <div class="terminal">
        <span class="terminal-prompt">NB-LATTICE > </span>SELECT * FROM OMEGA_COHORT LIMIT 6<br><br>
        <span class="terminal-output">HS-447821 | c10riboseqorf92 | Ω | Portland, OR  | 0.81 | PASSIVE    | 0.72 | NV-04 | <span class="terminal-flag">COMPLETED</span><br>
        HS-229041 | c10riboseqorf92 | Ω | Seattle, WA   | 0.54 | PASSIVE    | 0.60 | NV-04 | MONITORING<br>
        HS-881203 | c10riboseqorf92 | Ω | Oakland, CA   | 0.93 | ACTIVE     | 0.88 | NV-04 | <span class="terminal-flag">COMPLETED</span><br>
        HS-334092 | c10riboseqorf92 | Ω | Denver, CO    | 0.67 | PASSIVE    | 0.55 | NV-04 | FLAGGED<br>
        HS-102847 | c10riboseqorf92 | Ω | Chicago, IL   | 0.78 | ACTIVE     | 0.91 | NV-04 | <span class="terminal-flag">COMPLETED</span><br>
        HS-773910 | c10riboseqorf92 | Ω | Portland, OR  | 0.44 | MONITORING | 0.30 | —     | MONITORING<br>
        <br>
        [...341 more rows]<br>
        19 entries with status = COMPLETED. Facility NV-04: unlisted in NovaBridge infrastructure docs.</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="doc-block danger">
        <strong>adversity_score</strong> — not a standard clinical field. Not in the HelixScreen schema.<br>
        <strong>approach</strong> — PASSIVE / ACTIVE / MONITORING. Not defined in any document you have access to.<br>
        <strong>relocation_feasibility</strong> — self-explanatory in a way that makes you feel sick.<br>
        <strong>COMPLETED</strong> — 19 people. NV-04 is somewhere in Nevada. You search the facility code. No results.
        </div>
        """, unsafe_allow_html=True)

        if df is not None:
            with st.expander("📊 What the real TransCODE data says about these microproteins", expanded=False):
                c10 = df[df["orf_id"] == "c10riboseqorf92"]
                if not c10.empty:
                    row = c10.iloc[0]
                    st.markdown(f"""
                    **c10riboseqorf92** — the orf_id in every row of OMEGA_COHORT<br>
                    - Length: **{int(row['length'])} AA**
                    - Tier: **{row['tier']}** (detected by mass spectrometry)
                    - Conservation: **{row['Conservation.ORF']}**
                    - PhyloCSF (primates): **{row['PhyloCSF.primates']:.2f}**

                    This is a real microprotein, published in open-access supplementary data by the TransCODE Consortium.
                    NovaBridge is using a published scientific finding to build a targeting registry.
                    """)

    st.markdown("---")
    st.markdown('<div class="choice-header">You know what this is. What do you do?</div>', unsafe_allow_html=True)

    choice = st.radio(
        "347 flagged individuals. 19 already sent to an unregistered Nevada facility.",
        [
            "A — Close the partition. You have plausible deniability. You never queried this.",
            "B — Submit a formal data governance request asking what OMEGA_COHORT is for.",
            "C — Export the schema and the first 20 rows. Save them where NovaBridge can't reach them.",
        ],
        index=None,
        key="ch3_radio",
    )

    if choice:
        if choice.startswith("A"):
            st.markdown('<div class="doc-block">Session closed. No record of the query in your log — you were careful. You tell yourself you don\'t know enough to act.</div>', unsafe_allow_html=True)
            delta_s, delta_m = -5, -20
        elif choice.startswith("B"):
            st.markdown('<div class="doc-block flagged">The governance ticket is acknowledged at 11:03 PM. By 11:17 PM, your access to OMEGA_COHORT has been revoked. C. Weiss sends a message: <em>"That partition is outside your assignment scope. Let\'s talk tomorrow."</em></div>', unsafe_allow_html=True)
            delta_s, delta_m = +20, +15
        else:
            st.markdown('<div class="doc-block flagged">You have the schema. You have sample rows. You have enough to prove the registry exists. You don\'t know yet what you\'re going to do with it.</div>', unsafe_allow_html=True)
            delta_s, delta_m = +25, +35

        if not st.session_state.ch3_done:
            record_choice(3, choice[0], delta_s, delta_m)
            st.session_state.ch3_done = True

        if st.button("Continue to Chapter 4 →", key="ch3_next"):
            st.session_state.chapter = 4
            st.rerun()

# ── Chapter 4 — Compound Brief ────────────────────────────────────────────────

def chapter_4(df):
    st.markdown('<div class="chapter-header">Chapter 4</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">Compound Brief</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    <div class="memo-header">NovaBridge Systems — NL-7 Compound Brief // NEURO-LATTICE // CONFIDENTIAL</div>
    The compound brief you requested in week one has finally been approved for your clearance level.
    <br><br>
    You have been validating this compound's trial pipeline for three weeks.
    This is the first time you are reading what it actually does.
    </div>
    """, unsafe_allow_html=True)

    sections = [
        ("Compound Designation", "NL-7 (NEURO-LATTICE Series, Batch 7)"),
        ("Compound Class", "TCR-mimetic peptide antagonist"),
        ("Target", "Peptide-HLA Class I complex on neural cell surfaces\nSpecific epitope: KYTALLLTQ (positions 31–39 of c10riboseqorf92)\nHLA restriction: A*02:01"),
        ("Delivery Mechanism", "Aerosol. Field-deployable. Room-temperature stable for 72 hours."),
        ("Downstream Effect", "'Modulation of arousal and decision-latency parameters'\n[See Appendix C — REDACTED, Level 3 required]"),
        ("Efficacy Limitation", "Does not bind variant carriers displaying KFTALLLTQ (Y→F substitution at position 2).\nVariant prevalence: estimated 0.2% of population. See OMEGA_COHORT."),
        ("Regulatory Status", "Phase II — internal trial. Not registered with FDA. Not disclosed to IRB."),
    ]

    for label, content in sections:
        danger = any(word in label.lower() or word in content.lower()
                     for word in ["aerosol", "fda", "irb", "compliance", "latency", "omega"])
        cls = "doc-block danger" if danger else "doc-block"
        st.markdown(
            f'<div class="{cls}"><strong>{label}</strong><br>'
            f'<span style="white-space:pre-line">{content}</span></div>',
            unsafe_allow_html=True,
        )

    if df is not None:
        with st.expander("🧬 What KYTALLLTQ actually is (real data)", expanded=False):
            c10 = df[df["orf_id"] == "c10riboseqorf92"]
            if not c10.empty:
                seq = str(c10.iloc[0]["sequence"]).strip().rstrip("*")
                peptide = seq[30:39]
                st.markdown(f"""
                The sequence of c10riboseqorf92 from the public TransCODE supplementary data:

                `{seq}`

                Positions 31–39: **`{peptide}`**

                This is a real 9-mer from a real microprotein, published in a Nature paper nine months ago.
                NovaBridge built a pharmacological weapon around it — targeting it on the neural cell surfaces
                of people who express the common variant. The 0.2% who display KFTALLLTQ instead are invisible to NL-7.
                That 0.2% is OMEGA_COHORT.
                """)

    st.markdown("---")
    st.markdown('<div class="choice-header">You have read enough.</div>', unsafe_allow_html=True)

    choice = st.radio(
        "NL-7 is not a therapeutic. It targets a microprotein-derived peptide on neural cells. The delivery is aerosol.",
        [
            "A — Sign the validation report as written. You are a data analyst, not a pharmacologist. This is above your pay grade.",
            "B — Refuse to sign. Submit a formal objection through the ethics reporting channel.",
            "C — Contact Dr. Yuna Park at the Langley-Stanford Institute for Genomic Medicine. Her name is in the HelixScreen literature. She needs to know what her data is being used for.",
        ],
        index=None,
        key="ch4_radio",
    )

    if choice:
        if choice.startswith("A"):
            st.markdown('<div class="doc-block">Report signed. Your supervisor sends a brief acknowledgment. You receive a 12% performance bonus the following morning.</div>', unsafe_allow_html=True)
            delta_s, delta_m = -20, -30
        elif choice.startswith("B"):
            st.markdown('<div class="doc-block danger">The ethics report is received. You receive an automated confirmation. Forty minutes later, C. Weiss calls. Your access is suspended pending review. <em>"We\'ll talk about your future at NovaBridge tomorrow."</em></div>', unsafe_allow_html=True)
            delta_s, delta_m = +20, +25
        else:
            if has_item("park_trust"):
                st.markdown('<div class="doc-block flagged">You write to the email she gave you in the lobby. You sign your name. You attach the compound brief. You attach the OMEGA_COHORT schema.<br><br>She replies in eleven minutes. <em>"I remember you. I\'m going to forward this to someone. Stay near your phone."</em></div>', unsafe_allow_html=True)
                delta_s, delta_m = +30, +50
            else:
                st.markdown('<div class="doc-block flagged">You find her email in the TransCODE Consortium author list. You write three drafts. The fourth one you actually send — from a personal account, at 11:34 PM, with no name attached. You attach the compound brief. You attach the OMEGA_COHORT schema. <br><br>You don\'t know if she receives it. You don\'t know if it\'s enough.</div>', unsafe_allow_html=True)
                delta_s, delta_m = +30, +40

        if not st.session_state.ch4_done:
            record_choice(4, choice[0], delta_s, delta_m)
            st.session_state.ch4_done = True

        if st.button("Continue to Chapter 5 →", key="ch4_next"):
            st.session_state.chapter = 5
            st.rerun()

# ── Chapter 5 — Exit Protocol ─────────────────────────────────────────────────

def chapter_5():
    st.markdown('<div class="chapter-header">Chapter 5</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">Exit Protocol</div>', unsafe_allow_html=True)

    suspicion = st.session_state.suspicion
    choices = st.session_state.choices

    # NovaBridge has flagged the analyst if suspicion >= 60
    if suspicion >= 60:
        st.markdown("""
        <div class="memo">
        <div class="memo-header" style="color:#ef4444">NovaBridge Systems — Security Notice // NB-ANALYST-4471</div>
        Your account has been flagged for unauthorized data access.
        IT has notified your supervisor. Your Level 2 clearance has been suspended.
        <br><br>
        Report to Building C, Room 4, at 9:00 AM for an exit interview.
        <br><br>
        Your personal devices have been added to the network monitoring list as of 11:47 PM.
        <br><br>
        <em style="color:#64748b">— NovaBridge Systems, Security Division</em>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("You have a few hours. Maybe less.")
    else:
        st.markdown("""
        <div class="memo">
        <div class="memo-header">NovaBridge Systems — Status Update // NB-ANALYST-4471</div>
        Your validation report has been received. Your contract runs through the end of the quarter.
        <br><br>
        C. Weiss would like to meet next week to discuss expanding your role on NEURO-LATTICE.
        <br><br>
        Performance metrics: within expected parameters.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Make your final decision")
    st.caption("Everything you've learned. Everything you've saved, or didn't. This is where it lands.")

    # Final choice shapes ending
    final = st.radio(
        "What do you do?",
        [
            "A — Stay. Sign the updated NDA. Take the expanded role. The money is real.",
            "B — Resign. Return the company laptop. Say nothing publicly. Hope the data you saved reaches someone.",
            "C — Resign and go public. Contact the journalists, the researchers, the Congressional offices. Use your name.",
        ],
        index=None,
        key="ch5_radio",
    )

    if final:
        if not st.session_state.ch5_done:
            if final.startswith("A"):
                record_choice(5, "A", -20, -35)
                add_item("nb_bonus")
            elif final.startswith("B"):
                record_choice(5, "B", +10, +20)
            else:
                record_choice(5, "C", +20, +40)
            st.session_state.ch5_done = True

        if st.button("📁 Submit decision", key="ch5_submit", type="primary", use_container_width=True):
            # Determine ending
            m = st.session_state.moral_score
            s = st.session_state.suspicion
            leaked = choices.get(4) == "C" or final.startswith("C")
            stayed = final.startswith("A")
            flagged = s >= 60

            if stayed:
                st.session_state.ending_type = "stayed"
            elif flagged and not leaked:
                st.session_state.ending_type = "flagged"
            elif leaked or m >= 60:
                st.session_state.ending_type = "leak"
            else:
                st.session_state.ending_type = "gone"

            st.session_state.ended = True
            st.rerun()

# ── Endings ───────────────────────────────────────────────────────────────────

def render_ending():
    kind = st.session_state.ending_type
    suspicion = st.session_state.suspicion
    moral = st.session_state.moral_score
    choices = st.session_state.choices

    # Persist to shared career state (idempotent — set once per run)
    PATH_FOR_ENDING = {
        "stayed": "bystander",
        "flagged": "bystander",  # the "they knew" outcome is still in the bystander family
        "leak": "whistleblower",
        "gone": "whistleblower",  # quiet leak still counts as exposure attempt
    }
    if "analyst" not in st.session_state.career["games_completed"]:
        # If you talked to Park AND chose to leak/contact her, that's the Confidant arc
        if has_item("park_trust") and (choices.get(4) == "C" or kind == "leak"):
            mark_game_complete("analyst", "confidant", analyst_suspicion_at_end=suspicion)
            mark_path("confidant")
        else:
            path = PATH_FOR_ENDING.get(kind, "bystander")
            mark_game_complete("analyst", kind, analyst_suspicion_at_end=suspicion)
            mark_path(path)

    st.markdown("---")

    # Reveal the loyalty score
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem">
        <div style="font-size:0.65rem;letter-spacing:0.3em;color:#64748b;text-transform:uppercase">NovaBridge Internal Metric — Now Visible</div>
        <div style="font-size:0.75rem;color:#94a3b8;margin-top:0.2rem">The performance metric that was always being calculated. You just couldn't see it.</div>
    </div>
    """, unsafe_allow_html=True)

    ever_flagged = st.session_state.ever_flagged
    col1, col2 = st.columns(2)
    with col1:
        sus_color = "#ef4444" if ever_flagged else "#f59e0b" if suspicion >= 30 else "#22c55e"
        st.markdown(f'<div style="text-align:center;font-size:2.5rem;font-weight:900;color:{sus_color}">{suspicion}<span style="font-size:1rem;color:#64748b">/100</span></div>', unsafe_allow_html=True)
        st.caption("NovaBridge Suspicion Index — this was always running")
        if ever_flagged:
            st.error("You appear in the registry.")
        elif suspicion >= 30:
            st.warning("You are under monitoring.")
        else:
            st.success("You were never flagged.")
    with col2:
        m_color = "#22c55e" if moral >= 60 else "#f59e0b" if moral >= 30 else "#ef4444"
        st.markdown(f'<div style="text-align:center;font-size:2.5rem;font-weight:900;color:{m_color}">{moral}<span style="font-size:1rem;color:#64748b">/100</span></div>', unsafe_allow_html=True)
        st.caption("Moral Clarity — What you actually did")

    st.markdown("---")

    if kind == "stayed":
        st.markdown("""
        <div class="ending-block stayed">
        <strong style="color:#0ea5e9;font-size:1.1rem">You stayed.</strong>
        <br><br>
        The expanded role came through. The NDA was eight pages. You signed all of them.
        <br><br>
        The investigation happened anyway — six months later, when a researcher named Rael found
        a data packet in a forum thread with no author name attached. The thread was taken down
        in four hours. It had already been downloaded 340 times.
        <br><br>
        You read about the preprint in a science newsletter. You recognized the compound name.
        You closed the tab.
        <br><br>
        NovaBridge settled for $400 million eighteen months later. None of the settlement is public.
        Three executives resigned. No charges were filed.
        <br><br>
        You received a year-end bonus.
        </div>
        """, unsafe_allow_html=True)

        # Secret path unlock — Vigilante
        # Strict gate: the player must have made the Vigilante pattern THIS run,
        # not just have the items lingering in career inventory from a previous run.
        vigilante_pattern_this_run = (
            st.session_state.choices.get(2) == "C"          # screenshot the log
            and st.session_state.choices.get("yuna") == "C" # pocket the keycard
            and st.session_state.choices.get(4) != "C"      # don't contact Park (stay clean)
            and st.session_state.choices.get(5) == "A"      # stay
        )
        if vigilante_unlocked() and vigilante_pattern_this_run:
            st.markdown("""
            <div style="background:#1c1000;border-left:3px solid #f59e0b;padding:1rem 1.2rem;border-radius:0 4px 4px 0;margin:1.5rem 0;color:#f59e0b">
            <strong>You stayed. You also still have her keycard. And the screenshot. And the bonus.</strong>
            <br><br>
            <span style="color:#cbd5e1;font-style:italic">Last Tuesday you found a second partition.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("→ Six months later", key="vigilante_enter", type="primary", use_container_width=True):
                st.session_state.ended = False
                st.session_state.chapter = 6
                st.rerun()

    elif kind == "flagged":
        st.markdown("""
        <div class="ending-block flag">
        <strong style="color:#ef4444;font-size:1.1rem">They knew before you decided.</strong>
        <br><br>
        The exit interview lasted forty minutes. C. Weiss was not there — a legal representative was.
        You were asked to sign a document confirming you had not shared proprietary information.
        <br><br>
        You didn't sign.
        <br><br>
        Your NovaBridge email was terminated at 11:15 AM. Your personal devices were flagged for
        network monitoring. Three months later, a courier delivered a cease-and-desist letter
        to your home address.
        <br><br>
        You had not shared anything. They knew that too.
        <br><br>
        The investigation happened anyway, through a different channel.
        You were not part of it. Your name appears nowhere in the final preprint.
        </div>
        """, unsafe_allow_html=True)

    elif kind == "leak":
        st.markdown("""
        <div class="ending-block leak">
        <strong style="color:#22c55e;font-size:1.1rem">The data reached the light.</strong>
        <br><br>
        The email to Dr. Park arrived at 11:34 PM. She forwarded it to Rael within the hour.
        <br><br>
        The preprint posted five weeks later — without your name, at your request.
        By 6 AM, forty-three scientists in seven countries had replied to Yuna's emails.
        Three independent labs confirmed the mechanism.
        <br><br>
        You resigned by email at 8 AM. You left the laptop on the kitchen table for the courier.
        You had already moved everything you needed.
        <br><br>
        Your name surfaces three years later in a Congressional hearing transcript.
        The senator mispronounces your title. The record shows you as "anonymous NovaBridge analyst."
        You watch the clip twice on your phone and then close the app.
        <br><br>
        <em>The body keeps the score. Sometimes the score is also the thing that saves everyone else.</em>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()

    else:  # gone
        st.markdown("""
        <div class="ending-block gone">
        <strong style="color:#94a3b8;font-size:1.1rem">You left quietly.</strong>
        <br><br>
        Resignation submitted. Laptop returned. Nothing said publicly.
        The data you saved sits on a drive somewhere.
        <br><br>
        The investigation happened anyway — someone else made the call you didn't.
        The preprint named a different source. NovaBridge fell apart without you.
        <br><br>
        You read the news coverage from a different city.
        You know more of the story than any journalist does.
        <br><br>
        You've never told anyone.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Show choice summary
    with st.expander("Review your decisions", expanded=False):
        choice_labels = {
            "A": "Complied / Looked away",
            "B": "Flagged through channels",
            "C": "Saved evidence / Contacted researcher / Went public",
        }
        chapter_names = {
            1: "Orientation — NL-7-VAR suspension",
            2: "Legacy Access — query log",
            3: "OMEGA_COHORT — the registry",
            4: "Compound Brief — NL-7 is a weapon",
            5: "Exit — final decision",
        }
        for ch_num, choice_key in st.session_state.choices.items():
            label = choice_labels.get(choice_key, choice_key)
            st.markdown(f"**{chapter_names.get(ch_num, f'Chapter {ch_num}')}:** {label}")

    if st.button("↩ Play again", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Chapter 6 — The Vigilante ─────────────────────────────────────────────────

# ── Heist objective catalog (used by Chapter 6) ──────────────────────────────

HEIST_OBJECTIVES = {
    "extract": {
        "title": "Extract KAPPA_COHORT",
        "subtitle": (
            "The new partition lives on Lattice's primary cluster. An automated audit will detect "
            "unauthorized reads at 6:00 AM. You have one shot."
        ),
        "options": {
            "live": {
                "label": "Pull through your authenticated NovaBridge session",
                "requires": None,
                "score": 1,
                "tag": "fast",
                "inline": "Fastest. Highest fingerprint. Your employee ID is on every query.",
            },
            "mirror": {
                "label": "Mirror via Langley-Stanford's cross-institutional pipe",
                "requires": "park_keycard",
                "score": 2,
                "tag": "clean",
                "inline": "Slower. Cloned keycard authenticates the pull as cross-institutional research traffic.",
            },
            "skip": {
                "label": "Don't extract — the OMEGA data you already have is enough",
                "requires": None,
                "score": 0,
                "tag": "partial",
                "inline": "No new risk. No proof of the second cohort. The 211 people stay invisible in the story.",
            },
        },
    },
    "publish": {
        "title": "Reach a publishing channel",
        "subtitle": (
            "The data is meaningless if it sits on your drive. Pick how it gets into hands that can move it."
        ),
        "options": {
            "dump": {
                "label": "Public Tor mirror, no coordination",
                "requires": None,
                "score": 1,
                "tag": "raw",
                "inline": "Fastest. File metadata is sloppy. Privacy advocates will be unhappy.",
            },
            "park": {
                "label": "Send to Park with a full cover letter and the original log archive",
                "requires": "screenshot",
                "score": 2,
                "tag": "coordinated",
                "inline": "She knows what to do with this. She has standing you'll never have.",
            },
            "ftp": {
                "label": "Upload to Langley-Stanford's collaborative FTP as cross-lab transfer",
                "requires": "park_keycard",
                "score": 2,
                "tag": "institutional",
                "inline": "Disguised as a normal dataset share. Institutional credibility, no public dump signal.",
            },
        },
    },
    "protect": {
        "title": "Cover your tracks",
        "subtitle": "NovaBridge will trace this. Decide how much of you they find at the end of the thread.",
        "options": {
            "hide": {
                "label": "Stay quiet. Your compliance record is your shield.",
                "requires": None,
                "score": 1,
                "tag": "hidden",
                "inline": "Free. Works until it doesn't. Six months from now, your name might come up.",
            },
            "fund": {
                "label": "Wire the severance into legal defense + cleanup infrastructure ($32K)",
                "requires": "nb_bonus",
                "score": 2,
                "tag": "funded",
                "inline": "Pre-paid counsel on retainer. Pre-paid hosting. Their money paid for the cleanup.",
            },
            "resign": {
                "label": "Quit publicly tonight. Resign with a written statement.",
                "requires": None,
                "score": 1,
                "tag": "exposed",
                "inline": "You become the story. The data is no longer alone — but the heat is on you.",
            },
        },
    },
}


def _resolve_heist(extract, publish, protect):
    """Map a choice combination to a named outcome + epilogue."""
    combo = (extract, publish, protect)
    score = (
        HEIST_OBJECTIVES["extract"]["options"][extract]["score"]
        + HEIST_OBJECTIVES["publish"]["options"][publish]["score"]
        + HEIST_OBJECTIVES["protect"]["options"][protect]["score"]
    )

    # Specific named combos
    NAMED = {
        ("mirror", "ftp",  "fund"):   ("The Architect", "perfect"),
        ("mirror", "park", "fund"):   ("The Conduit",   "coordinated"),
        ("mirror", "ftp",  "resign"): ("The Witness",   "witness"),
        ("mirror", "park", "resign"): ("The Witness",   "witness"),
        ("live",   "dump", "hide"):   ("The Detonation","detonation"),
        ("live",   "dump", "resign"): ("The Detonation","detonation"),
        ("skip",   "dump", "hide"):   ("The Bystander Returns", "halfhearted"),
        ("skip",   "park", "fund"):   ("The Quiet Hand","quiet"),
        ("skip",   "ftp",  "fund"):   ("The Quiet Hand","quiet"),
    }
    if combo in NAMED:
        name, tone = NAMED[combo]
    elif score >= 5:
        name, tone = "The Operator", "clean"
    elif score >= 3:
        name, tone = "The Catalyst", "messy"
    else:
        name, tone = "The Hesitation", "incomplete"

    EPILOGUES = {
        "perfect": (
            "You let yourself into the Langley-Stanford genomics building at 2:14 AM with the cloned badge. "
            "You mirror the KAPPA_COHORT partition through their cross-institutional pipe — it logs as routine "
            "research traffic. The screenshot, the schema, the NL-7-VAR brief, and the new cohort all upload to "
            "their collaborative FTP under the metadata of a normal cross-lab transfer. You walk out at 2:31 AM. "
            "<br><br>"
            "The preprint posts six weeks later. The supplementary data references 'an anonymous institutional "
            "source.' NovaBridge's internal investigation looks at every employee who has ever visited "
            "Langley-Stanford. There are none.<br><br>"
            "Pre-paid counsel was already on retainer when the subpoena arrived. The motion was denied within "
            "seventy-two hours. The compound is pulled. The 211 people are not on a list anymore.<br><br>"
            "You receive a Q3 raise. You accept it."
        ),
        "coordinated": (
            "You mirror KAPPA_COHORT through Langley-Stanford at 2 AM. Then, from your personal device, "
            "you write to Park. You attach the screenshot — eight months of automated queries — as proof "
            "of chain of custody. She replies in eleven minutes: <em>I remember you. I'm forwarding this. "
            "Stay near your phone.</em><br><br>"
            "The joint preprint posts six weeks later. Your name is on it. NovaBridge sues. "
            "Pre-paid counsel files for dismissal. The case is dismissed eleven months later. "
            "Three years from now you teach a guest seminar at Langley-Stanford on ethical data "
            "infrastructure. You introduce yourself by your first name."
        ),
        "witness": (
            "You execute the operation, then write a four-paragraph resignation letter and email it to "
            "every member of NovaBridge's board. You attach the same archive you uploaded to Langley-Stanford. "
            "You CC two journalists you'd been corresponding with anonymously for three months. "
            "<br><br>"
            "By morning, the story is everywhere. By afternoon, you are everywhere. "
            "You testify before Congress eight months later. You wear a navy suit you bought specifically "
            "for the occasion. The transcript runs four hundred pages. "
            "<br><br>"
            "The compound is pulled. The 211 people are not on a list anymore. Neither are you, in the way "
            "that matters."
        ),
        "detonation": (
            "At 3:47 AM you push every file to a public mirror. No coordination, no journalists, no Park. "
            "The mirror is Tor-fronted but the metadata isn't. NovaBridge's forensics team pulls authorship "
            "signatures from the file headers within seventy-two hours.<br><br>"
            "The story breaks. The story is real. The story is also messy — the raw query log includes "
            "patient identifiers that should have been scrubbed. Privacy advocates condemn the leaker. "
            "NovaBridge sues for trade secret theft. You can't afford to fight. The compound is pulled. "
            "211 people are off the list. Your name is in the wrong public records for the rest of your life."
        ),
        "quiet": (
            "You don't pull KAPPA_COHORT. You don't risk the second cohort. What you have — the OMEGA "
            "data, the schema, the compound brief — is enough. You route it carefully, and you fund the "
            "infrastructure that protects everyone downstream.<br><br>"
            "The preprint posts six weeks later. It is narrower than it could have been. The 211 people "
            "in the second cohort are not in the public story. But the program is exposed enough that "
            "NovaBridge can't safely continue it. The Phase I trial stays suspended. The cohort goes quiet.<br><br>"
            "You are never named. You never visit a courtroom. You sleep, mostly."
        ),
        "halfhearted": (
            "You upload the OMEGA data to a public mirror at 3:21 AM. You go to bed. You go to work in "
            "the morning. The story breaks two weeks later, slowly. The reporters who pick it up are not "
            "the ones who matter. NovaBridge releases a statement calling the documents 'an unauthorized "
            "summary of legitimate research.' The compound is not pulled. The cohort continues.<br><br>"
            "You did something. You did not do enough. You think about that for a long time."
        ),
        "clean": (
            "It worked. Mostly cleanly. The story breaks within weeks, anchored by reproducible evidence. "
            "NovaBridge contests it; NovaBridge loses; the compound is pulled. You don't testify. You don't "
            "become the story. You go on living a life that is slightly different from the one you had "
            "twelve hours earlier."
        ),
        "messy": (
            "It worked. Not cleanly. Some of the evidence held up; some of it didn't. The compound is pulled "
            "eventually. The story takes longer to land than it should have. You spend a year wondering "
            "whether you should have made a different choice on at least one of the three objectives."
        ),
        "incomplete": (
            "It half-worked. The data is out there, but not in a form that mobilizes anyone. "
            "NovaBridge contests it successfully on technicalities. The Phase I trial stays suspended; "
            "the registry doesn't change. You wonder, later, what would have happened if you'd committed."
        ),
    }

    return name, EPILOGUES[tone], score


def _option_label(obj_key, opt_key):
    """Render an option label with an item-icon chip when the option uses a career item."""
    from src.career import ITEMS
    opt = HEIST_OBJECTIVES[obj_key]["options"][opt_key]
    req = opt["requires"]
    if req is None:
        return opt["label"]
    return f"{opt['label']} — uses {ITEMS[req]['icon']}"


def chapter_6():
    st.markdown('<div class="chapter-header">Chapter 6 — Hidden</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Operation</div>', unsafe_allow_html=True)

    # ── Setup memo ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="memo">
    <div class="memo-header">NovaBridge Systems — Performance Review // NB-ANALYST-4471 // Q2 2027</div>
    Promoted twice. Year-end bonus exceeded target by 18%. Cleared for Level 3 access pending Q3 review.
    Recommended for the NEURO-LATTICE extended program.
    <br><br>
    <em style="color:#22c55e">"A model employee. Discreet, thorough, low-overhead." — C. Weiss</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="memo" style="border-color:#92400e;background:#1c1000">
    Six months of compliance. Six months of bonuses. The screenshot in a safe deposit box.
    The cloned keycard in the back of a desk drawer. $32,400 in an account NovaBridge can't see.
    <br><br>
    Last Tuesday, while auditing a partition you'd been avoiding, you found
    <strong style="color:#f59e0b">KAPPA_COHORT</strong>. 211 entries. 22 marked COMPLETED.
    Targeting compound: NL-7-VAR. The trial was suspended. The cohort was not.
    <br><br>
    You have until 6:00 AM before the automated audit notices anything missing. Three objectives.
    Pick how you complete each.
    </div>
    """, unsafe_allow_html=True)

    # ── Objective panels ──────────────────────────────────────────────────────
    chosen = {}
    for obj_key in ("extract", "publish", "protect"):
        obj = HEIST_OBJECTIVES[obj_key]
        st.markdown("---")
        st.markdown(f'<div class="chapter-header">Objective — {obj_key.upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:1.2rem;font-weight:800;color:#f1f5f9;margin-bottom:0.3rem">{obj["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.88rem;color:#94a3b8;margin-bottom:0.9rem;line-height:1.6">{obj["subtitle"]}</div>', unsafe_allow_html=True)

        # Filter options to those whose requirements are satisfied
        available = [
            (k, _option_label(obj_key, k))
            for k, opt in obj["options"].items()
            if opt["requires"] is None or has_item(opt["requires"])
        ]
        labels = [lbl for _, lbl in available]
        keys = [k for k, _ in available]

        pick = st.radio(
            f"How do you handle {obj_key}?",
            labels,
            index=None,
            key=f"ch6_{obj_key}_radio",
            label_visibility="collapsed",
        )
        if pick is not None:
            pick_key = keys[labels.index(pick)]
            chosen[obj_key] = pick_key
            inline = obj["options"][pick_key]["inline"]
            st.caption(f"↳ {inline}")

    # ── Execute ───────────────────────────────────────────────────────────────
    if len(chosen) == 3:
        st.markdown("---")
        if st.button("⏵ Execute the operation", key="ch6_execute", type="primary", use_container_width=True):
            st.session_state.ch6_result = chosen
            st.rerun()

    if st.session_state.get("ch6_result"):
        result = st.session_state.ch6_result
        name, epilogue, score = _resolve_heist(result["extract"], result["publish"], result["protect"])

        st.markdown("---")
        st.markdown(
            f'<div style="text-align:center;margin:1rem 0">'
            f'<div style="font-size:0.7rem;letter-spacing:0.3em;color:#64748b;text-transform:uppercase">Outcome</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#f59e0b;margin-top:0.2rem">{name}</div>'
            f'<div style="font-size:0.85rem;color:#94a3b8;margin-top:0.2rem">Operation score: {score} / 6</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="ending-block leak">{epilogue}</div>', unsafe_allow_html=True)

        # Record outcome
        if not st.session_state.ch6_done:
            outcome_id = f"vigilante_{result['extract']}_{result['publish']}_{result['protect']}"
            mark_game_complete("analyst", outcome_id, analyst_suspicion_at_end=st.session_state.suspicion)
            mark_path("vigilante")
            st.session_state.ch6_done = True
            st.balloons()

        # ── Chapter 7 unlock — requires items from MULTIPLE playthroughs ─────
        # Keycard and Trust are mutually exclusive in one Yuna encounter, so
        # having both means the player has run The Analyst on at least two paths.
        ch7_eligible = (
            st.session_state.ch6_done
            and has_item("park_keycard")
            and has_item("park_trust")
            and has_item("screenshot")
            and has_item("nb_bonus")
        )
        if ch7_eligible:
            st.markdown("---")
            st.markdown("""
            <div class="memo" style="border-color:#22c55e;background:#0a1a10">
            <div class="memo-header" style="color:#22c55e">Federal Subpoena // Eight Months Later</div>
            You have collected what only multiple lives can collect: her trust <em>and</em> her keycard.
            The screenshot <em>and</em> the bonus. The Confidant and the Vigilante in the same person.
            <br><br>
            Last Tuesday a federal subpoena arrived in a manila envelope.
            <strong>United States v. NovaBridge Systems, Inc.</strong> The prosecution wants you on the stand.
            </div>
            """, unsafe_allow_html=True)
            if st.button("⚖ Take the witness box", key="ch7_enter", type="primary", use_container_width=True):
                st.session_state.chapter = 7
                st.rerun()

        st.markdown("---")
        if st.button("↩ Return to career hub", use_container_width=True):
            st.switch_page("app.py")


# ── Chapter 7 — The Witness Box (second secret level) ────────────────────────

TESTIMONY = {
    1: {
        "question": "Did you knowingly copy NovaBridge's proprietary data without authorization?",
        "options": {
            "concede": {
                "label": "Yes. I copied it. I would do it again.",
                "requires": None,
                "potency": 1,
                "follow": "The prosecution looks down at their notes. The judge writes something. The jury looks at you, not at NovaBridge.",
            },
            "screenshot": {
                "label": "I documented unauthorized surveillance of 558 patients across two cohorts. What I copied was already a crime.",
                "requires": "screenshot",
                "potency": 2,
                "follow": "Defense attorney pivots, but the framing is broken. The jury is now looking at NovaBridge's table. One of their lawyers writes something. The other one stops writing.",
            },
            "fifth": {
                "label": "On advice of counsel, I decline to answer.",
                "requires": None,
                "potency": 0,
                "follow": "Your attorney nods. The defense moves on too quickly — they preferred a denial. The jury remembers the silence.",
            },
        },
    },
    2: {
        "question": "How did you come to know Dr. Yuna Park?",
        "options": {
            "brief": {
                "label": "She dropped her keycard in our lobby. We spoke for two minutes.",
                "requires": None,
                "potency": 1,
                "follow": "Truthful. Minimal. The defense moves on too quickly — they wanted more.",
            },
            "trust": {
                "label": "She is a colleague. We have been corresponding since the day she gave me her university email in that lobby.",
                "requires": "park_trust",
                "potency": 2,
                "follow": "Dr. Park is in the gallery. She nods once. The defense attorney pauses, choosing the next question carefully.",
            },
            "fifth": {
                "label": "On advice of counsel, I decline.",
                "requires": None,
                "potency": 0,
                "follow": "The judge frowns. The defense has scored a point and they know it.",
            },
        },
    },
    3: {
        "question": "Why did you wait six months before acting on what you knew?",
        "options": {
            "honest": {
                "label": "I was afraid. I documented for six months. When I found the second cohort, I acted.",
                "requires": None,
                "potency": 1,
                "follow": "Honest. The jury can do the math themselves.",
            },
            "bonus": {
                "label": "I was being paid to stay quiet. I'm telling you so under oath, with the bank records already in evidence.",
                "requires": "nb_bonus",
                "potency": 2,
                "follow": "The bank statements are read into the record. The retention bonus. The performance bonuses. The 18% over-target year-end. NovaBridge's complicity becomes part of the story, not just the backdrop.",
            },
            "fifth": {
                "label": "On advice of counsel, I decline.",
                "requires": None,
                "potency": 0,
                "follow": "The jury notes this. NovaBridge's attorneys exchange a look.",
            },
        },
    },
    4: {
        "question": "Are you aware that some of your evidence cannot be independently authenticated?",
        "options": {
            "concede": {
                "label": "Yes. The chain of custody on some files is contested.",
                "requires": None,
                "potency": 1,
                "follow": "Honest concession. The defense doesn't get the lever they were reaching for.",
            },
            "dossier": {
                "label": "The peer-reviewed dossier was reproduced by three independent labs within ten days of posting. The core findings authenticate themselves.",
                "requires": "investigation_dossier",
                "potency": 2,
                "follow": "The dossier is admitted as exhibit. The replication certifications follow. The defense doesn't argue further.",
            },
            "fifth": {
                "label": "On advice of counsel, I decline.",
                "requires": None,
                "potency": 0,
                "follow": "The defense smiles slightly. The jury notes the silence.",
            },
        },
    },
    5: {
        "question": "NovaBridge maintains that no patients were harmed by their procedures. What is your response?",
        "options": {
            "plain": {
                "label": "Nineteen people were marked COMPLETED in the OMEGA cohort. Twenty-two in KAPPA. They were not harmed?",
                "requires": None,
                "potency": 1,
                "follow": "The courtroom is silent. The prosecutor lets it sit.",
            },
            "aria": {
                "label": "May I read four things into the record? [unlocked: full inventory]",
                "requires": "_all_five",
                "potency": 3,
                "follow": (
                    "You read for eleven minutes. "
                    "The screenshot's metadata, dated months before the trial began. "
                    "Dr. Park's first email back to you, timestamped at 11:34 PM on the night of the lobby. "
                    "The bank statements showing every dollar of NovaBridge's retention payments. "
                    "The dossier's reproducibility certifications from Stanford, Cambridge, and Tsukuba. "
                    "And then a list. Forty-one names. The ones who would be COMPLETED if you'd waited one more month. "
                    "<br><br>"
                    "The courtroom does not breathe. The judge does not stop you. "
                    "The verdict is reached in forty minutes."
                ),
            },
            "fifth": {
                "label": "On advice of counsel, I decline.",
                "requires": None,
                "potency": 0,
                "follow": "The defense smiles. The prosecutor closes her folder. The jury is sent out.",
            },
        },
    },
}


def _has_all_five():
    """Special sentinel check for the Q5 aria — requires all five career items."""
    return all(has_item(i) for i in ("screenshot", "park_keycard", "park_trust", "nb_bonus", "investigation_dossier"))


def _resolve_testimony(answers):
    """Compute outcome from the 5 chosen answer keys."""
    total = sum(TESTIMONY[q]["options"][ans]["potency"] for q, ans in answers.items())
    used_aria = answers.get(5) == "aria"
    fifth_count = sum(1 for ans in answers.values() if ans == "fifth")

    if used_aria and total >= 9:
        name, tone = "The Reckoning", "reckoning"
    elif total >= 7:
        name, tone = "The Testimony", "testimony"
    elif fifth_count >= 4:
        name, tone = "The Survivor", "survivor"
    elif total <= 3:
        name, tone = "The Defendant", "defendant"
    else:
        name, tone = "The Honest Witness", "witness"

    EPILOGUES = {
        "reckoning": (
            "The jury returns in forty minutes. Guilty on twelve of fourteen counts.<br><br>"
            "NovaBridge's stock is halted before the verdict is read. By the next morning, "
            "the company is in receivership. The Phase I cohort is dismantled. The Phase II "
            "is too. Three executives accept plea deals to avoid criminal prosecution; two go to trial "
            "and are convicted within the year.<br><br>"
            "You testify in seven additional cases. You write a book. You don't go to prison; "
            "your prosecution is dropped within a month of the verdict, in recognition of cooperation. "
            "Dr. Park dedicates her next paper to you. You read it on a flight to Geneva, where you "
            "are speaking at a regulatory conference on data-infrastructure ethics.<br><br>"
            "Eight years later, a young analyst at a different company writes to you. "
            "You write back the same evening."
        ),
        "testimony": (
            "Guilty on seven of fourteen counts. The damaging counts. NovaBridge dissolves within "
            "six months. The compounds are pulled. The 558 people are not on a list anymore.<br><br>"
            "Your own prosecution is reduced to a misdemeanor; you serve no time. Your name appears "
            "in journals and in headlines. You don't write a book. You go back to data work, "
            "for a different kind of institution. You sleep, mostly."
        ),
        "witness": (
            "Guilty on three counts; not guilty on the remainder. NovaBridge pays a $400M penalty "
            "and a consent decree. The compounds are pulled. The cohorts are dismantled.<br><br>"
            "Your testimony was honest but uneven. The defense made hay of the gaps. You face a "
            "trade-secrets civil suit which is eventually settled. You move to a different city. "
            "You still get letters, sometimes, from people who say the case mattered to them."
        ),
        "survivor": (
            "The trial ends in a mistrial. NovaBridge accepts a sealed plea agreement; the terms "
            "are not made public. The Phase II cohort is quietly disbanded over six months. "
            "There is no verdict, no headline, no closure.<br><br>"
            "You are not prosecuted. The Fifth Amendment, used five times, did its work. "
            "You receive no congratulations and no condemnation. You go home. "
            "Sometimes you wonder what would have happened if you'd answered the questions."
        ),
        "defendant": (
            "The defense built its case on your silences. You spend more time defending your own "
            "conduct than NovaBridge spends defending theirs. The jury hangs.<br><br>"
            "NovaBridge settles civilly for $50M and admits no wrongdoing. The compounds are quietly "
            "rebranded. Your own prosecution proceeds — felony charges, plea-bargained down to "
            "eighteen months suspended. You don't go to prison. You don't go back to data work, either."
        ),
    }
    return name, EPILOGUES[tone], total


def chapter_7():
    st.markdown('<div class="chapter-header">Chapter 7 — Hidden</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Witness Box</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="memo">
    <div class="memo-header">United States v. NovaBridge Systems, Inc. // Federal District Court // Day 11 of Trial</div>
    You wear a navy suit you bought specifically for this. The bailiff swears you in.
    Dr. Park is in the gallery, three rows back, with two of her co-authors.
    NovaBridge's defense team has five questions for you. The jury has been instructed
    that they may consider the manner of your responses, not just the content.
    </div>
    """, unsafe_allow_html=True)

    answers = {}
    for q_id, q in TESTIMONY.items():
        st.markdown("---")
        st.markdown(f'<div class="chapter-header">Question {q_id} of 5</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:1.05rem;font-weight:700;color:#f1f5f9;margin-bottom:0.8rem;line-height:1.5">{q["question"]}</div>', unsafe_allow_html=True)

        # Filter options: gated by item OR by special _all_five check
        available = []
        for opt_key, opt in q["options"].items():
            req = opt["requires"]
            if req is None:
                ok = True
            elif req == "_all_five":
                ok = _has_all_five()
            else:
                ok = has_item(req)
            if ok:
                available.append((opt_key, opt))

        labels = [opt["label"] for _, opt in available]
        keys = [k for k, _ in available]

        pick = st.radio(
            f"Answer for Q{q_id}",
            labels,
            index=None,
            key=f"ch7_q{q_id}_radio",
            label_visibility="collapsed",
        )
        if pick is not None:
            pick_key = keys[labels.index(pick)]
            answers[q_id] = pick_key
            st.caption(f"↳ {available[labels.index(pick)][1]['follow']}")

    # Resolution
    if len(answers) == 5:
        st.markdown("---")
        if st.button("⚖ Deliver testimony", key="ch7_deliver", type="primary", use_container_width=True):
            st.session_state.ch7_result = answers
            st.rerun()

    if st.session_state.get("ch7_result"):
        result = st.session_state.ch7_result
        name, epilogue, total = _resolve_testimony(result)

        st.markdown("---")
        st.markdown(
            f'<div style="text-align:center;margin:1rem 0">'
            f'<div style="font-size:0.7rem;letter-spacing:0.3em;color:#64748b;text-transform:uppercase">Verdict Tone</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#22c55e;margin-top:0.2rem">{name}</div>'
            f'<div style="font-size:0.85rem;color:#94a3b8;margin-top:0.2rem">Testimony potency: {total} / 11</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="ending-block leak">{epilogue}</div>', unsafe_allow_html=True)

        if not st.session_state.get("ch7_done"):
            outcome_id = "witness_" + "_".join(result[q] for q in sorted(result.keys()))
            mark_game_complete("analyst", outcome_id, analyst_suspicion_at_end=st.session_state.suspicion)
            st.session_state.ch7_done = True
            st.balloons()

        st.markdown("---")
        if st.button("↩ Return to career hub", key="ch7_return", use_container_width=True):
            st.switch_page("app.py")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_df()
    sidebar()
    title_block()

    if st.session_state.ended:
        render_ending()
        return

    ch = st.session_state.chapter
    if ch == 1:
        chapter_1()
    elif ch == 2:
        chapter_2(df)
    elif ch == 3:
        chapter_3(df)
    elif ch == 4:
        chapter_4(df)
    elif ch == 5:
        chapter_5()
    elif ch == 6:
        chapter_6()
    elif ch == 7:
        chapter_7()

main()
