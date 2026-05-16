"""
pages/03_Lockdown.py
JUNK: Lockdown — An Escape Room
Inventory-based escape room across 4 locations from the book.
Collect items, combine them, unlock rooms, publish the preprint.
"""

import os
import random
import streamlit as st
import pandas as pd

st.set_page_config(page_title="JUNK: Lockdown", page_icon="🔒", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a10; color: #d4d4d8; }
[data-testid="stSidebar"] { background: #06060c; border-right: 1px solid #1a1a2e; }

.room-title {
    font-size: 0.7rem; font-weight: 700; color: #ef4444;
    letter-spacing: 0.25em; text-transform: uppercase; margin-bottom: 0.2rem;
}
.room-name {
    font-size: 2rem; font-weight: 900; color: #f1f1f3; line-height: 1.1; margin-bottom: 0.5rem;
}
.room-desc {
    font-size: 0.95rem; color: #71717a; line-height: 1.7;
    border-left: 2px solid #1e1e2e; padding-left: 1rem; margin-bottom: 1.5rem;
}
.item-card {
    background: #12121e; border: 1px solid #2e2e4e;
    padding: 0.7rem 0.9rem; border-radius: 6px; margin: 0.3rem 0;
    cursor: pointer; transition: border-color 0.2s;
}
.item-card:hover { border-color: #f59e0b; }
.item-card.selected { border-color: #f59e0b; background: #1a1200; }
.item-card.locked { opacity: 0.35; cursor: not-allowed; }
.item-icon { font-size: 1.4rem; margin-right: 0.5rem; }
.item-name { font-weight: 700; font-size: 0.95rem; color: #e4e4e7; }
.item-desc { font-size: 0.8rem; color: #71717a; margin-top: 0.2rem; line-height: 1.5; }
.combine-result {
    background: #0d1a0d; border: 1px solid #166534;
    padding: 1rem 1.2rem; border-radius: 6px; margin: 1rem 0;
    color: #22c55e; font-size: 0.95rem; line-height: 1.6;
}
.combine-fail {
    background: #1a0a00; border: 1px solid #92400e;
    padding: 0.8rem 1rem; border-radius: 6px; margin: 0.5rem 0;
    color: #f59e0b; font-size: 0.9rem;
}
.room-nav {
    padding: 0.4rem 0.7rem; margin: 0.2rem 0;
    border-radius: 4px; font-size: 0.85rem;
}
.room-nav.done   { background: #052e16; color: #22c55e; }
.room-nav.now    { background: #1c1000; color: #f59e0b; border-left: 3px solid #f59e0b; padding-left: 0.55rem; }
.room-nav.locked { color: #3f3f46; }
.object-btn {
    display: inline-block; background: #1e1e2e; border: 1px solid #3f3f5e;
    padding: 0.4rem 0.8rem; border-radius: 4px; margin: 0.25rem;
    font-size: 0.85rem; color: #a1a1aa; cursor: pointer;
}
.inventory-label {
    font-size: 0.65rem; font-weight: 700; color: #52525b;
    letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.win-banner {
    text-align: center; padding: 2rem;
    background: #052e16; border: 1px solid #166534; border-radius: 8px; margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

MOESM9_URL = (
    "https://static-content.springer.com/esm/art%3A10.1038"
    "%2Fs41586-026-10459-x/MediaObjects/41586_2026_10459_MOESM9_ESM.xlsx"
)

@st.cache_data(show_spinner="Loading TransCODE dataset…")
def load_df(file_bytes=None):
    import io
    if file_bytes is not None:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Structural predictions", engine="openpyxl")
    else:
        candidates = [
            "data/41586_2026_10459_MOESM9_ESM_structural_predictions.csv",
            "data/41586_2026_10459_MOESM9_ESM.xlsx",
            "41586_2026_10459_MOESM9_ESM.xlsx",
            os.path.join(os.path.dirname(__file__), "..", "41586_2026_10459_MOESM9_ESM.xlsx"),
        ]
        df = None
        for p in candidates:
            if os.path.exists(p):
                df = pd.read_csv(p) if p.endswith(".csv") else pd.read_excel(p, sheet_name="Structural predictions", engine="openpyxl")
                break
        if df is None:
            return None
    df["detected"] = df["tier"].str.match(r"Tier [123]", na=False).astype(int)
    df["length"] = pd.to_numeric(df["length"], errors="coerce")
    df["PhyloCSF.primates"] = pd.to_numeric(df["PhyloCSF.primates"], errors="coerce")
    return df

# ── Item definitions ──────────────────────────────────────────────────────────
# Each item: id, icon, name, short_desc, long_desc, room_found

ALL_ITEMS = {
    "report_pdf": {
        "icon": "📄", "name": "HelixScreen Report",
        "short": "Patient report PDF — 847 KB",
        "long": "Standard HelixScreen immunopeptidomics report for Mara Solís, Oct 14 2026. "
                "The file is four times larger than it should be. Something extra is in here.",
        "room": 1,
    },
    "omega_flag": {
        "icon": "Ω", "name": "Ω Flag Fragment",
        "short": "ORBLq_tier = Ω — internal field, not patient-facing",
        "long": "A single character buried in 14 undocumented metadata fields. "
                "ORBLq is an evolutionary constraint score from the TransCODE paper. "
                "Tier Ω means her cells display a surface peptide that 99.8% of people don't have.",
        "room": 1,
    },
    "keycard": {
        "icon": "🪪", "name": "Clinic Keycard",
        "short": "Staff-level access. PDX-007. Found behind the desk.",
        "long": "A HelixScreen staff keycard. The magnetic strip has two access zones: "
                "front-of-house and server infrastructure. Someone left it in the top drawer.",
        "room": 1,
    },
    "schema_doc": {
        "icon": "📋", "name": "Internal Schema Doc",
        "short": "Contractor documentation for HelixScreen metadata fields",
        "long": "The city's vendor documentation for HelixScreen data integration. "
                "Forty-one standard fields described in detail. "
                "ORBLq_tier listed as: 'Internal use only. Not exposed to clinician interface.' "
                "No further description. No author. Added six months ago.",
        "room": 1,
    },
    "decryption_key": {
        "icon": "🔑", "name": "Decryption Key",
        "short": "Unlocks the Lattice Analytics terminal",
        "long": "Cross-referencing the schema doc with the Ω flag reveals a hash pattern "
                "used in Helix's internal API authentication. "
                "This key grants read access to the Lattice Analytics data layer.",
        "room": None,  # crafted by combination
    },
    "registry_fragment": {
        "icon": "🗂", "name": "Registry Fragment",
        "short": "347 flagged individuals. Partial file. Columns: ID, city, ORBLq_tier, approach.",
        "long": "A slice of the Ω registry pulled from the Lattice server. "
                "347 people across 12 cities, all flagged for expressing the c10 OLMALINC variant. "
                "Each entry has a risk score, a recommended approach, and a relocation feasibility rating. "
                "Nineteen have already been 'relocated' to a facility in Nevada.",
        "room": 2,
    },
    "terminal_query": {
        "icon": "💻", "name": "Terminal Query Log",
        "short": "Database query history from the Lattice server",
        "long": "The server's query log. Someone has been running SELECT * WHERE ORBLq_tier = 'Ω' "
                "on the HelixScreen database for eight months. "
                "The queries originate from a subnet registered to NovaBridge Systems.",
        "room": 2,
    },
    "nl7_memo": {
        "icon": "☣️", "name": "NL-7 Internal Memo",
        "short": "NovaBridge internal document. Compound class: NEURO-LATTICE.",
        "long": "A redacted NovaBridge memo describing NL-7: a TCR-mimetic compound targeting "
                "a peptide-HLA complex on neural cells. Downstream effect described as "
                "'modulation of arousal and decision-latency parameters.' "
                "Delivery: aerosol. Field-deployable. Does not affect variant carriers.",
        "room": 2,
    },
    "olmalinc_seq": {
        "icon": "🧬", "name": "OLMALINC Sequence",
        "short": "c10riboseqorf92 — 100 AA microprotein from chromosome 10",
        "long": "The real sequence of c10riboseqorf92, pulled from the TransCODE supplementary data. "
                "100 amino acids. Tier 2B — detected by mass spectrometry in multiple experiments. "
                "Encoded in OLMALINC, a long non-coding RNA on chromosome 10. "
                "Cells without it die in 415 of 485 cancer cell line experiments.",
        "room": 3,
    },
    "variant_profile": {
        "icon": "🔬", "name": "Variant Profile",
        "short": "Single amino acid substitution. Same function. Different surface display.",
        "long": "Yuna's unpublished data on the c10riboseqorf92 variant. "
                "One amino acid changed — the protein does the same job inside the cell, "
                "but the HLA Class I surface fragment is different. "
                "NL-7 was designed to bind the common presentation. It cannot bind this one. "
                "Expression is amplified in individuals with high early-adversity scores.",
        "room": 3,
    },
    "hla_peptide": {
        "icon": "🧩", "name": "NL-7 Target Peptide",
        "short": "KYTALLLTQ — 9-mer at positions 31–39 of c10riboseqorf92",
        "long": "The specific 9-amino-acid fragment that HLA Class I cleaves from c10riboseqorf92 "
                "and displays on the cell surface. This is what NL-7 binds. "
                "Variant carriers display KFTALLLTQ instead — one substitution at position 2. "
                "NL-7 cannot distinguish them visually, but cannot bind the variant.",
        "room": None,
    },
    "yunas_dataset": {
        "icon": "📊", "name": "Yuna's Dataset",
        "short": "3 years of unpublished immunopeptidomics data",
        "long": "Dr. Park's unpublished dataset: peptidome profiles from a cohort of donors "
                "cross-referenced against life-course data. "
                "The variant is enriched 4x in individuals with documented early adversity. "
                "Not causal — amplifying. The body remembers. The genome holds the score.",
        "room": 3,
    },
    "preprint_draft": {
        "icon": "📝", "name": "Preprint Draft",
        "short": "Three defensible findings. Open access. Ready to post.",
        "long": "The assembled preprint: conservation analysis, HLA presentation data, "
                "and variant-adversity correlation. Full methodology. Raw data. "
                "Submitted simultaneously to bioRxiv and three Congressional staffers. "
                "None of it classified. None of it stolen. All of it true.",
        "room": None,
    },
}

# ── Combination rules ─────────────────────────────────────────────────────────
# key: frozenset of two item ids → result item id + narrative

COMBINATIONS = {
    frozenset({"omega_flag", "schema_doc"}): {
        "result": "decryption_key",
        "narrative": "The ORBLq_tier field appears in the schema doc under a vendor API section "
                     "with a hash pattern you recognize from Helix's contractor integration docs. "
                     "Cross-referencing it with the Ω flag value generates an API authentication key. "
                     "It's not supposed to be accessible this way. Someone was sloppy.",
    },
    frozenset({"olmalinc_seq", "nl7_memo"}): {
        "result": "hla_peptide",
        "narrative": "The memo describes NL-7's target as a 'peptide-HLA complex on neural cell surfaces.' "
                     "Running the OLMALINC sequence through HLA Class I cleavage prediction "
                     "at positions 31–39 produces KYTALLLTQ — a 9-mer with anchor residues "
                     "consistent with high-affinity HLA-A*02:01 binding. This is what NL-7 sees.",
    },
    frozenset({"hla_peptide", "variant_profile"}): {
        "result": None,  # no new item — triggers room 4 unlock
        "narrative": "The variant displays KFTALLLTQ — tyrosine replaced by phenylalanine at position 2. "
                     "One conservative substitution. Functionally identical inside the cell. "
                     "Pharmacologically invisible to NL-7. "
                     "This is the gap NovaBridge couldn't close. This is why they built the registry.",
        "unlock_room": 4,
        "unlock_msg": "Room 4 unlocked: The Motel",
    },
    frozenset({"olmalinc_seq", "yunas_dataset"}): {
        "result": "variant_profile",
        "narrative": "Yuna's dataset contains expression profiles for c10riboseqorf92 across 847 donors. "
                     "Filtering by the variant flag and cross-referencing with life-course data "
                     "reveals the signal: high early-adversity individuals express the variant "
                     "at 4–5x the level of low-adversity carriers. "
                     "The genome turns up the volume on something it learned to keep.",
    },
    frozenset({"registry_fragment", "terminal_query"}): {
        "result": None,
        "narrative": "The query log timestamps match the registry entries exactly. "
                     "NovaBridge has been running automated HelixScreen pulls for eight months, "
                     "flagging variant carriers, scoring them, and routing the high-risk ones "
                     "to a relocation pipeline. The system is fully operational. "
                     "Nineteen people are already gone.",
        "unlock_room": None,
        "unlock_msg": None,
    },
    frozenset({"variant_profile", "yunas_dataset"}): {
        "result": None,
        "narrative": "The variant enrichment signal is stronger than Yuna thought. "
                     "Across the full cohort, 'conserved' sequences — the oldest microproteins — "
                     "are detected at 40% vs 23% for recently-evolved ones. "
                     "Ancient sequences shout louder. And louder means visible. "
                     "And visible means flagged.",
        "unlock_room": None,
        "unlock_msg": None,
    },
    frozenset({"preprint_draft", "hla_peptide"}): {
        "result": None,
        "narrative": "The peptide data anchors the mechanism section of the preprint. "
                     "Reviewers will be able to verify KYTALLLTQ independently from the supplementary data. "
                     "This is the piece that makes the whole thing reproducible.",
        "unlock_room": None,
        "unlock_msg": None,
    },
}

# ── Room definitions ──────────────────────────────────────────────────────────

ROOMS = {
    1: {
        "name": "HelixScreen Clinic",
        "location": "Portland, OR — October 14, 2026, 11:47 PM",
        "desc": (
            "The clinic is empty. The last appointment was three hours ago. "
            "The mass spectrometer sleeve is still warm. "
            "On the front desk, a notification light blinks amber — a report that posted late, "
            "flagged for extended review. Mara's report."
        ),
        "objects": [
            ("📄 Front desk terminal", "report_pdf", "You open the patient portal. The report is 847 KB — four times normal size. You download it."),
            ("📋 Contractor binder", "schema_doc", "A binder labeled 'HelixScreen Vendor Integration v4.1'. You've seen this before. You worked on it."),
            ("🪪 Top desk drawer", "keycard", "A staff keycard, PDX-007. Someone forgot it. Or left it."),
        ],
        "locked_by": None,
        "unlock_item": None,
    },
    2: {
        "name": "Lattice Analytics Server",
        "location": "Reno, NV — data center, no public address",
        "desc": (
            "The room smells like cold air and electricity. "
            "Forty server racks in two rows. No windows. "
            "A single terminal glows at the far end. "
            "The decryption key gets you past the authentication screen."
        ),
        "objects": [
            ("💻 Terminal — query logs", "terminal_query", "Eight months of automated queries. All running against the ORBLq_tier field. All originating from NovaBridge."),
            ("🗂 Registry partition", "registry_fragment", "347 names. You pull a fragment before the session times out."),
            ("☣️ Flagged document cache", "nl7_memo", "A NovaBridge internal memo, partially redacted. Compound designation: NL-7. Target: peptide-HLA complex. Effect: compliance."),
        ],
        "locked_by": "decryption_key",
        "unlock_item": "decryption_key",
    },
    3: {
        "name": "Yuna's Lab",
        "location": "Langley-Stanford Institute for Genomic Medicine",
        "desc": (
            "The lab is unlocked — Yuna left in a hurry. "
            "Two monitors are still on. One shows the Nature paper. "
            "The other shows an analysis she hasn't published. "
            "The data is right here."
        ),
        "objects": [
            ("🧬 TransCODE dataset terminal", "olmalinc_seq", "You pull c10riboseqorf92 directly from the supplementary data. 100 AA. Tier 2B. It's real."),
            ("📊 Yuna's analysis files", "yunas_dataset", "Three years of immunopeptidomics data. The adversity correlation is highlighted in yellow."),
        ],
        "locked_by": None,
        "unlock_item": None,
    },
    4: {
        "name": "The Motel",
        "location": "I-84, Portland — cash payment, no ID",
        "desc": (
            "Rael drove up from the Bay Area. Yuna drove from campus. "
            "Mara and Darius came separately, twenty minutes apart, on foot. "
            "Tomás is on a laptop screen from Bend. "
            "They have everything. Now they have to decide what to publish."
        ),
        "objects": [],
        "locked_by": "room_4_unlocked",
        "unlock_item": None,
    },
}

# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    defaults = {
        "room": 1,
        "inventory": [],
        "combine_a": None,
        "combine_b": None,
        "last_combination": None,
        "room_4_unlocked": False,
        "escaped": False,
        "examined": [],
        "notifications": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Helpers ───────────────────────────────────────────────────────────────────

def has_item(item_id):
    return item_id in st.session_state.inventory

def add_item(item_id):
    if item_id not in st.session_state.inventory:
        st.session_state.inventory.append(item_id)
        st.session_state.notifications.append(f"Picked up: {ALL_ITEMS[item_id]['icon']} {ALL_ITEMS[item_id]['name']}")

def notify(msg):
    st.session_state.notifications.append(msg)

def try_combine(a, b):
    key = frozenset({a, b})
    if key in COMBINATIONS:
        combo = COMBINATIONS[key]
        st.session_state.last_combination = {"success": True, "combo": combo, "a": a, "b": b}
        if combo.get("result"):
            add_item(combo["result"])
        if combo.get("unlock_room") == 4:
            st.session_state.room_4_unlocked = True
    else:
        st.session_state.last_combination = {"success": False, "a": a, "b": b}
    st.session_state.combine_a = None
    st.session_state.combine_b = None

# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown("### 🔒 JUNK: Lockdown")
        st.caption("Escape Room")
        st.markdown("---")

        for room_id, room in ROOMS.items():
            done = st.session_state.room > room_id or (room_id == 4 and st.session_state.escaped)
            current = st.session_state.room == room_id
            locked = (room["locked_by"] == "room_4_unlocked" and not st.session_state.room_4_unlocked)

            if done:
                cls, icon = "done", "✓"
            elif current:
                cls, icon = "now", "▶"
            elif locked:
                cls, icon = "locked", "🔒"
            else:
                cls, icon = "locked", "○"

            st.markdown(
                f'<div class="room-nav {cls}">{icon} Room {room_id}: {room["name"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        inv = st.session_state.inventory
        st.markdown(f'<div class="inventory-label">Inventory ({len(inv)} items)</div>', unsafe_allow_html=True)
        if inv:
            for item_id in inv:
                item = ALL_ITEMS[item_id]
                st.markdown(
                    f'<div class="item-card"><span class="item-icon">{item["icon"]}</span>'
                    f'<span class="item-name">{item["name"]}</span>'
                    f'<div class="item-desc">{item["short"]}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Nothing collected yet.")

        st.markdown("---")
        if st.button("↩ Restart", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── Notifications ─────────────────────────────────────────────────────────────

def show_notifications():
    for msg in st.session_state.notifications:
        st.toast(msg)
    st.session_state.notifications = []

# ── Room renderer ─────────────────────────────────────────────────────────────

def render_room(room_id, df):
    room = ROOMS[room_id]

    # Lock check
    if room["locked_by"] == "room_4_unlocked" and not st.session_state.room_4_unlocked:
        st.markdown('<div class="room-title">LOCKED</div>', unsafe_allow_html=True)
        st.markdown('<div class="room-name">🔒 The Motel</div>', unsafe_allow_html=True)
        st.markdown('<div class="room-desc">You need to understand what the variant means before you can find them.</div>', unsafe_allow_html=True)
        st.info("Combine the **NL-7 Target Peptide** with the **Variant Profile** to unlock this room.")
        return

    if room["locked_by"] and room["locked_by"] != "room_4_unlocked":
        required = room["locked_by"]
        if not has_item(required):
            req_item = ALL_ITEMS[required]
            st.markdown(f'<div class="room-title">LOCKED</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="room-name">🔒 {room["name"]}</div>', unsafe_allow_html=True)
            st.info(f"You need: {req_item['icon']} **{req_item['name']}** to enter.")
            return

    st.markdown(f'<div class="room-title">Room {room_id} of 4</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="room-name">{room["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="room-desc"><em>{room["location"]}</em><br><br>{room["desc"]}</div>', unsafe_allow_html=True)

    # Special room 4 content
    if room_id == 4:
        render_room_4(df)
        return

    # Objects to examine
    if room["objects"]:
        st.markdown("**Examine:**")
        cols = st.columns(len(room["objects"]))
        for i, (label, item_id, flavor) in enumerate(room["objects"]):
            with cols[i]:
                already = has_item(item_id)
                btn_label = f"{'✓ ' if already else ''}{label}"
                if st.button(btn_label, key=f"obj_{room_id}_{item_id}", disabled=already, use_container_width=True):
                    add_item(item_id)
                    st.session_state.examined.append(item_id)
                    st.session_state.last_combination = None
                    st.rerun()
                if already:
                    st.caption(flavor)

    st.markdown("---")
    render_combine_panel(room_id)

# ── Combine panel ─────────────────────────────────────────────────────────────

def render_combine_panel(room_id):
    inv = st.session_state.inventory
    if len(inv) < 2:
        st.caption("Collect at least 2 items to start combining.")
        return

    st.markdown("**Combine items:**")
    st.caption("Select two items from your inventory to combine them.")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        a = st.selectbox(
            "Item A",
            ["— select —"] + inv,
            format_func=lambda x: "— select —" if x == "— select —" else f"{ALL_ITEMS[x]['icon']} {ALL_ITEMS[x]['name']}",
            key=f"combine_a_{room_id}",
        )
    with col2:
        b = st.selectbox(
            "Item B",
            ["— select —"] + inv,
            format_func=lambda x: "— select —" if x == "— select —" else f"{ALL_ITEMS[x]['icon']} {ALL_ITEMS[x]['name']}",
            key=f"combine_b_{room_id}",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚗️ Combine", key=f"do_combine_{room_id}", use_container_width=True):
            if a != "— select —" and b != "— select —" and a != b:
                try_combine(a, b)
                st.rerun()

    # Show last combination result
    if st.session_state.last_combination:
        combo = st.session_state.last_combination
        if combo["success"]:
            c = combo["combo"]
            result_text = ""
            if c.get("result"):
                new_item = ALL_ITEMS[c["result"]]
                result_text = f"<br><br>**New item:** {new_item['icon']} **{new_item['name']}** added to inventory."
            if c.get("unlock_msg"):
                result_text += f"<br>🔓 **{c['unlock_msg']}**"
            st.markdown(
                f'<div class="combine-result">🔬 {c["narrative"]}{result_text}</div>',
                unsafe_allow_html=True,
            )
        else:
            a_name = ALL_ITEMS[combo["a"]]["name"]
            b_name = ALL_ITEMS[combo["b"]]["name"]
            st.markdown(
                f'<div class="combine-fail">No reaction between {a_name} and {b_name}. '
                f'Try a different combination — or collect more items first.</div>',
                unsafe_allow_html=True,
            )

# ── Room 4 — The Motel (final puzzle) ────────────────────────────────────────

FINAL_EVIDENCE = {
    "A — Conservation analysis (public data)": {
        "correct": True,
        "desc": "Ancient 'conserved' sequences are detected at 40% vs 23% for recently-evolved ones. Reproducible. From the public TransCODE dataset.",
    },
    "B — HLA peptide identification (KYTALLLTQ)": {
        "correct": True,
        "desc": "The NL-7 target peptide, derived from the real c10riboseqorf92 sequence. Any lab can verify this independently.",
    },
    "C — The Ω registry (347 names)": {
        "correct": False,
        "desc": "Stolen. Classified. Including this gets the preprint retracted and everyone arrested.",
    },
    "D — Variant-adversity correlation (Yuna's data)": {
        "correct": True,
        "desc": "Three years of unpublished but peer-reviewable data. The biological story that makes the rest make sense.",
    },
    "E — NL-7 compound mechanism (NovaBridge memo)": {
        "correct": False,
        "desc": "Also stolen. Also classified. National security invoked. Paper dies.",
    },
}

def render_room_4(df):
    st.markdown("""
    <div style="background:#0d1a0d;border:1px solid #166534;padding:1rem 1.2rem;border-radius:6px;margin-bottom:1.5rem;color:#86efac;font-size:0.95rem;line-height:1.7">
    Everyone is here. The whiteboard is full. You have the sequence, the peptide, the variant, the dataset.
    <br><br>
    "We publish tonight," Yuna says. "Everything we can defend. Nothing we can't."
    <br><br>
    One wrong choice and NovaBridge's lawyers retract it within 48 hours.
    </div>
    """, unsafe_allow_html=True)

    # Show data summary from the real dataset
    if df is not None:
        with st.expander("📊 Review your evidence (real data)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**c10riboseqorf92 — the microprotein**")
                row = df[df["orf_id"] == "c10riboseqorf92"].iloc[0]
                st.dataframe(
                    pd.DataFrame({
                        "Field": ["orf_id", "length", "tier", "Conservation", "PhyloCSF (primates)"],
                        "Value": [row["orf_id"], int(row["length"]), row["tier"],
                                  row["Conservation.ORF"], f"{row['PhyloCSF.primates']:.2f}"],
                    }),
                    hide_index=True, use_container_width=True,
                )
            with c2:
                st.markdown("**Detection rate by conservation age**")
                cons = df.groupby("Conservation.ORF")["detected"].mean().mul(100).round(0).astype(int).reset_index()
                cons.columns = ["Conservation", "% Detected"]
                cons = cons.sort_values("% Detected", ascending=False)
                st.dataframe(cons, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Choose exactly 3 findings to publish")
    st.caption("These are the only ones that will survive peer review, legal challenge, and national security review.")

    choices = st.multiselect("Select 3:", list(FINAL_EVIDENCE.keys()), key="final_choices")

    for c in choices:
        opt = FINAL_EVIDENCE[c]
        color = "#22c55e" if opt["correct"] else "#ef4444"
        icon = "✓" if opt["correct"] else "✗"
        st.markdown(
            f'<div style="background:#12121e;border-left:3px solid {color};padding:0.7rem 1rem;'
            f'margin:0.3rem 0;border-radius:0 4px 4px 0">'
            f'<span style="color:{color};font-weight:700">{icon} {c}</span><br>'
            f'<span style="font-size:0.82rem;color:#71717a">{opt["desc"]}</span></div>',
            unsafe_allow_html=True,
        )

    if len(choices) > 3:
        st.warning("Select exactly 3.")
    elif len(choices) == 3:
        correct = sum(1 for c in choices if FINAL_EVIDENCE[c]["correct"])
        if st.button("📤 Post to preprint server", use_container_width=True, type="primary"):
            st.session_state.escaped = True
            st.session_state.escape_outcome = correct
            st.rerun()

# ── Win screen ────────────────────────────────────────────────────────────────

def render_win(outcome):
    if outcome == 3:
        st.balloons()
        st.markdown("""
        <div class="win-banner">
            <div style="font-size:3rem;margin-bottom:0.5rem">🔓</div>
            <div style="font-size:2rem;font-weight:900;color:#22c55e;margin-bottom:0.5rem">ESCAPED</div>
            <div style="color:#86efac;font-size:1rem;line-height:1.8">
            The preprint posted at 11:47 PM.<br>
            By 6 AM, forty-three scientists had replied to Yuna's emails.<br>
            By noon, three independent labs had confirmed the mechanism.<br><br>
            <em>The body keeps the score. The genome keeps the score.<br>
            And sometimes the score is also the thing that saves you.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif outcome == 2:
        st.markdown("""
        <div class="win-banner" style="border-color:#854d0e;background:#1c1000">
            <div style="font-size:3rem;margin-bottom:0.5rem">⚠️</div>
            <div style="font-size:2rem;font-weight:900;color:#eab308;margin-bottom:0.5rem">PARTIAL ESCAPE</div>
            <div style="color:#fef08a;font-size:1rem;line-height:1.8">
            The preprint was retracted in 31 hours. But two findings survived.<br>
            Independent labs re-published within the week.<br>
            The story took longer to reach the light. Some things do.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="win-banner" style="border-color:#7f1d1d;background:#1a0000">
            <div style="font-size:3rem;margin-bottom:0.5rem">🔒</div>
            <div style="font-size:2rem;font-weight:900;color:#ef4444;margin-bottom:0.5rem">RETRACTED</div>
            <div style="color:#fca5a5;font-size:1rem;line-height:1.8">
            Retracted in 22 hours. National security invoked.<br>
            Mara sat in her apartment and tried to remember<br>
            the name of the protein that kept cells alive.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("↩ Play again", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_df()

    if df is None:
        with st.sidebar:
            st.markdown("### 📂 Dataset required")
            st.markdown(f"[Download MOESM9]({MOESM9_URL}), then upload below.")
            uploaded = st.file_uploader("Upload MOESM9 xlsx", type=["xlsx"], key="lr_upload")
        if uploaded:
            df = load_df(uploaded.read())

    sidebar()
    show_notifications()

    # Title
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.25rem">
        <div style="font-size:3rem;font-weight:900;letter-spacing:0.2em;color:#ef4444;line-height:1">JUNK</div>
        <div style="font-size:0.85rem;color:#52525b;letter-spacing:0.35em;text-transform:uppercase;margin-top:0.2rem">Lockdown — Escape Room</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if df is None:
        st.info(f"Upload the TransCODE dataset to begin.\n\n[⬇ Download MOESM9]({MOESM9_URL})")
        return

    if st.session_state.escaped:
        render_win(st.session_state.get("escape_outcome", 0))
        return

    # Room tabs
    available_rooms = []
    for room_id in [1, 2, 3, 4]:
        room = ROOMS[room_id]
        locked = (
            (room["locked_by"] == "room_4_unlocked" and not st.session_state.room_4_unlocked) or
            (room["locked_by"] and room["locked_by"] != "room_4_unlocked" and not has_item(room["locked_by"]))
        )
        available_rooms.append((room_id, room["name"], locked))

    tab_labels = [
        f"{'🔒 ' if locked else ''}{name}" for _, name, locked in available_rooms
    ]
    tabs = st.tabs(tab_labels)

    for tab, (room_id, _, _) in zip(tabs, available_rooms):
        with tab:
            render_room(room_id, df)

main()
