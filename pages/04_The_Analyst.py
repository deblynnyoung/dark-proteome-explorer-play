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
        "examined": [],
        "ended": False,
        "ending_type": None,
        "clearance_level": 2,
        "ever_flagged": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

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
        if st.button("↩ Restart", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
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
            st.markdown('<div class="doc-block flagged">Saved. You don\'t know what you\'re going to do with it. But it\'s somewhere NovaBridge doesn\'t control.</div>', unsafe_allow_html=True)
            delta_s, delta_m = +20, +30

        if not st.session_state.ch2_done:
            record_choice(2, choice[0], delta_s, delta_m)
            st.session_state.ch2_done = True

        if st.button("Continue to Chapter 3 →", key="ch2_next"):
            st.session_state.chapter = 3
            st.rerun()

# ── Chapter 3 — OMEGA_COHORT ──────────────────────────────────────────────────

def chapter_3(df):
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

main()
