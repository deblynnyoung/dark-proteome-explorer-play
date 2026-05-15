"""
pages/02_The_Investigation.py
JUNK: The Dark Proteome Investigation
A 5-chapter narrative puzzle game using real data from the Nature 2026 TransCODE paper.
"""

import os
import random
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="JUNK: The Investigation",
    page_icon="🧬",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0d0d14; color: #d4d4d8; }
[data-testid="stSidebar"] { background: #0a0a10; border-right: 1px solid #1e1e2e; }
[data-testid="stSidebarContent"] { color: #d4d4d8; }

.narrative {
    background: #12121e;
    border-left: 3px solid #f59e0b;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0 1.5rem;
    font-style: italic;
    font-size: 1.05rem;
    line-height: 1.85;
    color: #c4c4cc;
    border-radius: 0 4px 4px 0;
}
.chapter-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #f59e0b;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.1rem;
}
.chapter-title {
    font-size: 2rem;
    font-weight: 800;
    color: #e4e4e7;
    margin-bottom: 1.5rem;
    line-height: 1.1;
}
.mono-block {
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    border: 1px solid #2e2e4e;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: #a1a1aa;
    border-radius: 3px;
}
.mono-block.flag {
    border-color: #f59e0b;
    color: #f59e0b;
    background: #1a0e00;
}
.mono-block.field-anomalous {
    border-color: #ef4444;
    color: #ef4444;
    background: #1a0000;
}
.evidence-pill {
    display: inline-block;
    background: #052e16;
    border: 1px solid #166534;
    color: #22c55e;
    font-size: 0.78rem;
    padding: 0.2rem 0.6rem;
    border-radius: 99px;
    margin: 0.2rem 0.1rem;
    font-weight: 600;
}
.chapter-nav {
    padding: 0.35rem 0.7rem;
    margin: 0.15rem 0;
    border-radius: 4px;
    font-size: 0.88rem;
    color: #52525b;
}
.chapter-nav.done  { background: #052e16; color: #22c55e; }
.chapter-nav.now   { background: #1c1917; color: #f59e0b; border-left: 3px solid #f59e0b; padding-left: 0.55rem; }
.chapter-nav.ahead { color: #3f3f46; }
.score-big { font-size: 3rem; font-weight: 900; color: #f59e0b; text-align: center; line-height: 1; }
.ending-text {
    background: #12121e;
    border-left: 3px solid #22c55e;
    padding: 1.2rem 1.5rem;
    margin: 1.5rem 0;
    font-size: 1rem;
    line-height: 1.85;
    color: #c4c4cc;
    border-radius: 0 4px 4px 0;
}
.ending-text.partial { border-left-color: #eab308; }
.ending-text.fail    { border-left-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading TransCODE dataset…")
def load_df():
    candidates = [
        "data/moesm9.csv",
        "41586_2026_10459_MOESM9_ESM.xlsx",
        "data/41586_2026_10459_MOESM9_ESM.xlsx",
        os.path.join(os.path.dirname(__file__), "..", "41586_2026_10459_MOESM9_ESM.xlsx"),
    ]
    for p in candidates:
        if os.path.exists(p):
            df = pd.read_csv(p) if p.endswith(".csv") else pd.read_excel(p, sheet_name="Structural predictions", engine="openpyxl")
            df["detected"] = df["tier"].str.match(r"Tier [123]", na=False).astype(int)
            return df
    return None

# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    for k, v in {
        "chapter": 1,
        "evidence": [],
        "score": 0,
        "ch1_done": False,
        "ch2_done": False,
        "ch3_done": False,
        "ch4_done": False,
        "ch5_done": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar(df):
    with st.sidebar:
        st.markdown("### 🧬 JUNK")
        st.caption("The Dark Proteome Investigation")
        st.markdown("---")

        chapters = [
            (1, "The Flag"),
            (2, "The Microprotein"),
            (3, "Surface Presentation"),
            (4, "The Pattern"),
            (5, "The Preprint"),
        ]
        for n, title in chapters:
            done = st.session_state[f"ch{n}_done"]
            current = st.session_state.chapter == n
            if done:
                cls, icon = "done", "✓"
            elif current:
                cls, icon = "now", "▶"
            else:
                cls, icon = "ahead", "○"
            st.markdown(
                f'<div class="chapter-nav {cls}">{icon} Chapter {n}: {title}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        score = st.session_state.score
        st.markdown(f'<div style="text-align:center;font-size:1.6rem;font-weight:700;color:#f59e0b">{score}<span style="font-size:0.9rem;color:#71717a">/100</span></div>', unsafe_allow_html=True)
        st.caption("Investigation score")

        if st.session_state.evidence:
            st.markdown("**Dossier:**")
            for e in st.session_state.evidence:
                st.markdown(f'<span class="evidence-pill">✓ {e}</span>', unsafe_allow_html=True)

        st.markdown("---")
        if st.button("↩ Restart", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


def add_evidence(label: str):
    if label not in st.session_state.evidence:
        st.session_state.evidence.append(label)

# ── Title ─────────────────────────────────────────────────────────────────────

def title_block():
    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 0.5rem">
        <div style="font-size:3.5rem;font-weight:900;letter-spacing:0.25em;color:#f59e0b;line-height:1">JUNK</div>
        <div style="font-size:0.95rem;color:#52525b;letter-spacing:0.3em;text-transform:uppercase;margin-top:0.3rem">The Dark Proteome Investigation</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# ── Chapter 1 ─────────────────────────────────────────────────────────────────

def chapter_1():
    st.markdown('<div class="chapter-header">Chapter 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Flag</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="narrative">
    Mara Solís had worked in city data management long enough to know what a file should look like.
    Her last HelixScreen report — six months ago, nothing unusual — had been 203 kilobytes.
    <br><br>
    The new one was 847.
    <br><br>
    She exported the PDF as a structured document and opened the properties panel.
    Sixty-three metadata fields. Forty-one she recognized. Eight she knew but didn't fully understand.
    Fourteen she had never seen before.
    <br><br>
    One of them was wrong.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Inspect the metadata")
    st.caption("One of these fields is not in the standard patient-facing HelixScreen schema. It's marked *Internal use only* in the contractor documentation.")

    fields = [
        ("Patient_ID",                    "SOL-447821-M",                   False),
        ("Report_Date",                   "2026-10-14T23:47:00Z",           False),
        ("Canonical_Proteome_Status",     "COMPLETE",                       False),
        ("Immunopeptidome_Status",        "COMPLETE",                       False),
        ("Extended_Annotation_Status",    "COMPLETE",                       False),
        ("HLA_Class_I_Alleles",           "A*02:01 / B*07:02 / C*07:01",    False),
        ("Peptide_Count_Canonical",       "4,218",                          False),
        ("Peptide_Count_Extended",        "312",                            False),
        ("Extended_Data_Ref",             "2f68656c69782f4f524244717f7469657203c3a9",  False),
        ("ORBLq_tier",                    "Ω",                              True),
        ("Report_Version",                "4.1.2",                          False),
        ("Clinic_ID",                     "PDX-007",                        False),
    ]

    for name, val, anomalous in fields:
        cls = "mono-block field-anomalous" if anomalous else "mono-block"
        st.markdown(
            f'<div class="{cls}"><span style="opacity:0.5">{name}:</span>  {val}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    answer = st.radio(
        "Which field does not belong in a standard patient report?",
        ["HLA_Class_I_Alleles", "Extended_Data_Ref", "ORBLq_tier", "Peptide_Count_Extended"],
        index=None,
        key="ch1_radio",
    )

    if answer == "ORBLq_tier":
        st.success("**Correct.** `ORBLq_tier` is flagged *Internal use only — not exposed to clinician interface* in the contractor schema. Its value is a single character: **Ω**.")
        st.markdown("""
        <div class="mono-block flag">
        ORBLq: Evolutionary constraint score (TransCODE Consortium, Nature 2026).<br>
        Measures how conserved a stretch of "junk" DNA is across forty million years of mammals.<br>
        High ORBLq tier = the genome has been holding onto this region for a reason it isn't telling.<br>
        <br>
        ORBLq_tier = Ω<br>
        ↳  Surface presentation includes a peptide fragment absent in 99.8% of the population.
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.ch1_done:
            st.session_state.ch1_done = True
            st.session_state.score += 20
            add_evidence("Ω Flag")

        if st.button("Continue to Chapter 2 →", key="ch1_next"):
            st.session_state.chapter = 2
            st.rerun()

    elif answer is not None:
        st.error("That field is part of the standard schema. Look for something that would never appear in a patient-facing report.")

# ── Chapter 2 ─────────────────────────────────────────────────────────────────

def chapter_2(df):
    st.markdown('<div class="chapter-header">Chapter 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Microprotein</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="narrative">
    "The dark proteome," Dr. Yuna Park said. "Ninety-eight percent of the human genome dismissed
    as evolutionary clutter for fifty years. And in 2026, the TransCODE Consortium confirmed it:
    the body was manufacturing microproteins from regions of DNA that weren't supposed to produce
    anything at all. Seven thousand, two hundred and sixty-four of them identified. All hiding in
    what science had been calling background noise."
    <br><br>
    She turned her laptop to face them. "The one we care about is from chromosome ten.
    The consortium designation is <strong>c10riboseqorf92</strong>. It's in the supplementary data —
    right there in the open, if you know what you're looking for."
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        st.warning("Dataset not found. Place `41586_2026_10459_MOESM9_ESM.xlsx` in the app root directory.")
        return

    st.markdown("##### Search the TransCODE dataset")
    st.caption("Filter the 7,264 ncORFs below to isolate the microprotein Dr. Yuna describes: chromosome 10, detected by mass spectrometry (Tier 1–3).")

    c10 = df[df["orf_id"].str.startswith("c10")].copy()

    col_filter, col_table = st.columns([1, 2])

    with col_filter:
        min_len = st.slider("Min length (AA)", 20, 200, 20, key="ch2_min")
        max_len = st.slider("Max length (AA)", 20, 300, 300, key="ch2_max")
        tiers = st.multiselect(
            "Detection tier",
            ["Tier 1A", "Tier 1B", "Tier 2A", "Tier 2B", "Tier 3", "Tier 4"],
            default=["Tier 1A", "Tier 1B", "Tier 2A", "Tier 2B", "Tier 3"],
            key="ch2_tiers",
        )
        conservation = st.multiselect(
            "Conservation",
            sorted(c10["Conservation.ORF"].dropna().unique()),
            key="ch2_conservation",
        )

    filtered = c10[
        c10["length"].between(min_len, max_len) &
        c10["tier"].isin(tiers)
    ]
    if conservation:
        filtered = filtered[filtered["Conservation.ORF"].isin(conservation)]

    filtered = filtered.sort_values("PhyloCSF.primates", ascending=False)

    show_cols = ["orf_id", "length", "tier", "Conservation.ORF", "PhyloCSF.primates", "n_elm_total"]
    rename_map = {
        "Conservation.ORF": "Conservation",
        "PhyloCSF.primates": "PhyloCSF",
        "n_elm_total": "ELM motifs",
    }

    with col_table:
        st.caption(f"{len(filtered)} sequences match — scroll to explore")
        st.dataframe(
            filtered[show_cols].rename(columns=rename_map).head(30),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.markdown("##### Identify the ORF")

    target = "c10riboseqorf92"
    target_row = df[df["orf_id"] == target].iloc[0]

    # Build 3 plausible distractors: other c10 detected ORFs of similar length
    distractors_pool = c10[
        (c10["orf_id"] != target) &
        (c10["detected"] == 1) &
        (c10["length"].between(80, 130))
    ]["orf_id"].tolist()
    random.seed(7)
    distractors = random.sample(distractors_pool, min(3, len(distractors_pool)))
    options = [target] + distractors
    random.seed(7)
    random.shuffle(options)

    pick = st.radio(
        "Which ORF is the one the book calls c10riboseqorf92 — the chromosome-10 microprotein at the center of the investigation?",
        options,
        index=None,
        key="ch2_radio",
    )

    if pick == target:
        st.success(f"**Found it.** `{target}` — {int(target_row['length'])} AA · {target_row['tier']} · Conservation: {target_row['Conservation.ORF']} · PhyloCSF (primates): {target_row['PhyloCSF.primates']:.2f}")

        st.markdown("""
        <div class="mono-block flag">
        orf_id:            c10riboseqorf92<br>
        length:            100 AA  <span style="opacity:0.5">(the book says 123 — poetic license)</span><br>
        tier:              2B  (detected by mass spectrometry)<br>
        Conservation:      old world monkeys - young<br>
        PhyloCSF primates: -65.24<br>
        <br>
        This microprotein is real. It is in the public supplementary data.<br>
        It was called junk until 2026.
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.ch2_done:
            st.session_state.ch2_done = True
            st.session_state.score += 20
            add_evidence("c10riboseqorf92")

        if st.button("Continue to Chapter 3 →", key="ch2_next"):
            st.session_state.chapter = 3
            st.rerun()

    elif pick is not None:
        row = c10[c10["orf_id"] == pick]
        if not row.empty:
            r = row.iloc[0]
            st.warning(f"`{pick}` — {int(r['length'])} AA, {r['tier']}, PhyloCSF: {r['PhyloCSF.primates']:.1f}. Look for the orf_id that directly matches the consortium designation in the book.")

# ── Chapter 3 ─────────────────────────────────────────────────────────────────

def chapter_3(df):
    st.markdown('<div class="chapter-header">Chapter 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">Surface Presentation</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="narrative">
    "Every cell in your body," Yuna said, "is constantly chopping up its internal proteins into
    fragments — eight to eleven amino acids — and pushing them outward onto the cell surface.
    The immune system evolved to read those fragments to distinguish healthy cells from compromised ones."
    <br><br>
    Darius leaned forward. "Like a store posting its inventory in the window."
    <br><br>
    "Exactly. The pathway is called HLA Class I. And now HelixScreen reads that window too.
    Including the fragments from the dark proteome — the peptideins."
    <br><br>
    "NL-7 was engineered to bind one specific 9-amino-acid fragment: the most common surface
    presentation of c10riboseqorf92. Variant carriers display a slightly different peptide in
    the same window. One amino acid changed. NL-7 cannot see it."
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        st.warning("Dataset not found.")
        return

    # Pull the real sequence of c10riboseqorf92
    target_row = df[df["orf_id"] == "c10riboseqorf92"].iloc[0]
    full_seq = str(target_row["sequence"]).strip().rstrip("*")

    st.markdown("##### The c10riboseqorf92 protein sequence (100 AA)")
    st.markdown(f'<div class="mono-block">{full_seq}</div>', unsafe_allow_html=True)
    st.caption("HLA Class I cleaves this into 9-mer fragments and displays them on the cell surface. One of the 9-mers below is the NL-7 target — the *common* presentation. The others are single-amino-acid variants that NL-7 cannot bind.")

    # Pick a 9-mer window from the real sequence as the "common" peptide.
    # We use positions 31-39 (KYTALLLTQ) which has good anchor residues.
    window_start = 30
    common_peptide = full_seq[window_start:window_start + 9]

    # Build 3 single-AA substitution variants
    aa_sub = {"K": "R", "Y": "F", "T": "S", "A": "G", "L": "V", "Q": "N",
              "M": "I", "E": "D", "S": "T", "R": "K", "N": "Q", "V": "L",
              "G": "A", "F": "Y", "I": "M", "D": "E", "H": "N", "P": "A"}

    def make_variant(seq, pos):
        aa = seq[pos]
        sub = aa_sub.get(aa, "A")
        return seq[:pos] + sub + seq[pos + 1:]

    variants = [make_variant(common_peptide, 1),
                make_variant(common_peptide, 4),
                make_variant(common_peptide, 7)]

    # Deduplicate (in case of collision)
    seen, unique_variants = {common_peptide}, []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)
    while len(unique_variants) < 3:
        unique_variants.append(common_peptide[:8] + "X")

    options = [common_peptide] + unique_variants
    random.seed(13)
    random.shuffle(options)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Four peptide fragments from the surface window:**")
        for p in options:
            st.markdown(f'<div class="mono-block">{p}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("**Sequence context (positions 31–43):**")
        highlighted = (
            full_seq[:window_start]
            + f"**[{common_peptide}]**"
            + full_seq[window_start + 9:]
        )
        st.markdown(f'<div class="mono-block" style="word-break:break-all">{full_seq[:window_start]}<span style="color:#f59e0b;font-weight:bold">[{common_peptide}]</span>{full_seq[window_start+9:]}</div>', unsafe_allow_html=True)
        st.caption(f"The NL-7 target is the 9-mer at positions {window_start+1}–{window_start+9}.")

    st.markdown("---")
    answer = st.radio(
        "Which peptide is the common surface presentation — the NL-7 target?",
        options,
        index=None,
        key="ch3_radio",
        format_func=lambda x: f"`{x}`",
    )

    if answer == common_peptide:
        st.success(f"**Correct.** `{common_peptide}` is the 9-mer at positions {window_start+1}–{window_start+9} of c10riboseqorf92. Variant carriers display a single substitution at one anchor residue. NL-7 cannot bind the altered version.")

        if not st.session_state.ch3_done:
            st.session_state.ch3_done = True
            st.session_state.score += 20
            add_evidence(f"NL-7 target: {common_peptide}")

        if st.button("Continue to Chapter 4 →", key="ch3_next"):
            st.session_state.chapter = 4
            st.rerun()

    elif answer is not None:
        st.error(f"`{answer}` is a variant — one amino acid changed from the common presentation. That single substitution is why variant carriers are pharmacologically invisible to NL-7.")

# ── Chapter 4 ─────────────────────────────────────────────────────────────────

def chapter_4(df):
    st.markdown('<div class="chapter-header">Chapter 4</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Pattern</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="narrative">
    Yuna had the dataset open on her second monitor and was running the same comparison for the
    fourth time, because she still didn't quite believe it.
    <br><br>
    "The Ω flag correlates with detection tier," she said. "And detection tier correlates with
    conservation. The sequences that get picked up by the screening are the ones the genome has
    been holding onto the longest."
    <br><br>
    Tomás, on the screen, made a small sound. "The body keeps the score."
    <br><br>
    "In the genome," Yuna said quietly, "yes. Something like that."
    </div>
    """, unsafe_allow_html=True)

    if df is None:
        st.warning("Dataset not found.")
        return

    matplotlib.rcParams.update({
        "axes.facecolor": "#12121e",
        "figure.facecolor": "#0d0d14",
        "text.color": "#d4d4d8",
        "axes.labelcolor": "#c4c4cc",
        "xtick.color": "#71717a",
        "ytick.color": "#71717a",
        "axes.edgecolor": "#2e2e4e",
        "grid.color": "#1e1e2e",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    # Pre-compute stats
    cons_rate = df[df["Conservation.ORF"] == "conserved"]["detected"].mean() * 100
    young_rate = df[df["Conservation.ORF"] == "primatomorpha - young"]["detected"].mean() * 100

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Detection rate by conservation age**")
        st.caption("What fraction of sequences in each conservation category are detected by mass spectrometry (Tier 1–3)?")

        cons_stats = (
            df.groupby("Conservation.ORF")["detected"]
            .agg(["sum", "count"])
            .rename(columns={"sum": "detected", "count": "total"})
        )
        cons_stats["pct"] = cons_stats["detected"] / cons_stats["total"] * 100
        cons_stats = cons_stats.sort_values("pct", ascending=True)

        fig, ax = plt.subplots(figsize=(6, 3.5))
        bar_colors = [
            "#f59e0b" if str(i).strip().lower() == "conserved" else "#3f3f5e"
            for i in cons_stats.index
        ]
        bars = ax.barh(cons_stats.index, cons_stats["pct"], color=bar_colors, alpha=0.9)
        ax.set_xlabel("% sequences detected (Tier 1–3)")
        ax.set_xlim(0, 55)
        for bar, pct in zip(bars, cons_stats["pct"]):
            ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                    f"{pct:.0f}%", va="center", fontsize=10, color="#d4d4d8")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col2:
        st.markdown("**Sequence length: detected vs. not detected**")
        st.caption("Detected microproteins (Tier 1–3) vs. undetected (Tier 4) by amino acid length.")

        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.hist(df[df["detected"] == 0]["length"], bins=40, alpha=0.6,
                 label="Not detected (Tier 4)", color="#3f3f5e", range=(0, 300))
        ax2.hist(df[df["detected"] == 1]["length"], bins=40, alpha=0.85,
                 label="Detected (Tier 1–3)", color="#f59e0b", range=(0, 300))
        ax2.set_xlabel("Length (AA)")
        ax2.set_ylabel("Count")
        ax2.legend(fontsize=8, framealpha=0.2)
        fig2.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    st.markdown(f"""
    **From the real dataset ({len(df):,} sequences):**
    - Detection rate for ancient **"conserved"** sequences: **{cons_rate:.0f}%**
    - Detection rate for **"primatomorpha - young"** sequences: **{young_rate:.0f}%**
    - Ancient sequences are **{cons_rate/young_rate:.1f}×** more likely to be detected
    """)

    st.markdown("---")
    answer = st.radio(
        "What does this pattern tell us about which sequences get flagged by the Ω screening?",
        [
            "Detected sequences are simply longer, making them more visible to mass spectrometry",
            "Ancient sequences conserved across mammals are expressed more reliably — strong surface presentation crosses the detection threshold — which is exactly why they get flagged",
            "Detection is random; the pattern is an artifact of spectrometer calibration across studies",
            "The flag correlates with ELM motif density, not evolutionary age",
        ],
        index=None,
        key="ch4_radio",
    )

    if answer and "ancient" in answer and "conserved" in answer:
        st.success(f"**Correct.** Sequences the genome has preserved for tens of millions of years are expressed at consistently higher levels — high enough for the screen to pick them up. 'Conserved' sequences are detected at {cons_rate:.0f}% vs {young_rate:.0f}% for recently-evolved ones. The genome kept these sequences for a reason. That reason got them flagged.")

        if not st.session_state.ch4_done:
            st.session_state.ch4_done = True
            st.session_state.score += 20
            add_evidence("Conservation → Detection link")

        if st.button("Continue to Chapter 5 →", key="ch4_next"):
            st.session_state.chapter = 5
            st.rerun()

    elif answer is not None:
        st.error(f"Look at the bar chart. 'Conserved' sequences are detected at {cons_rate:.0f}% — nearly twice the rate of 'young' sequences. Why would ancient sequences be more consistently detectable?")

# ── Chapter 5 ─────────────────────────────────────────────────────────────────

EVIDENCE_OPTIONS = {
    "A — Evolutionary conservation analysis": {
        "correct": True,
        "desc": "PhyloCSF scores showing c10riboseqorf92 and related ORFs have measurably higher conservation than undetected sequences. Reproducible from public data. Peer-reviewable.",
    },
    "B — HLA surface presentation data": {
        "correct": True,
        "desc": "The Peptide.Sequence data showing detected Tier 1–3 ORFs produce consistent HLA-I peptide fragments. Directly from the Nature 2026 supplementary dataset.",
    },
    "C — The Ω registry (Rael's files)": {
        "correct": False,
        "desc": "347 names, HelixScreen flags, NovaBridge communications. Damning. Also stolen classified material. Any journal that includes it will retract within 48 hours.",
    },
    "D — Variant expression and adversity correlation": {
        "correct": True,
        "desc": "Three years of unpublished data showing amplified variant expression in high-adversity individuals. Reviewable. The biological story that makes the rest make sense.",
    },
    "E — NL-7 pharmacological mechanism (NovaBridge documents)": {
        "correct": False,
        "desc": "The compliance compound's downstream cascade. Also classified. Including it exposes sources, allows NovaBridge to invoke national security, and sinks the paper.",
    },
}


def chapter_5():
    st.markdown('<div class="chapter-header">Chapter 5</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-title">The Preprint</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="narrative">
    "We publish tonight," Yuna said.
    <br><br>
    The motel room had two laptops open and a whiteboard Darius had produced from his backpack,
    covered in sequence notations and network diagrams. Tomás watched from the screen, his face
    calm in the way of a man who had already survived worse.
    <br><br>
    "Everything we have — full methodology, raw data, open access. If it's on a preprint server
    it's public scientific record. Helix can't classify it. NovaBridge can't suppress it."
    <br><br>
    Mara looked at the board. "And if we include something we can't defend?"
    <br><br>
    Yuna met her eyes. "Then they discredit everything. We have one shot."
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Assemble the preprint")
    st.caption("Choose **exactly 3** pieces of evidence. One wrong choice gives NovaBridge grounds to retract the entire paper.")

    choices = st.multiselect(
        "Select 3 findings:",
        list(EVIDENCE_OPTIONS.keys()),
        key="ch5_choices",
    )

    for c in choices:
        opt = EVIDENCE_OPTIONS[c]
        color = "#22c55e" if opt["correct"] else "#ef4444"
        icon = "✓" if opt["correct"] else "✗"
        st.markdown(
            f'<div style="background:#12121e;border-left:3px solid {color};padding:0.75rem 1rem;margin:0.35rem 0;border-radius:0 4px 4px 0">'
            f'<span style="color:{color};font-weight:700">{icon} {c}</span><br>'
            f'<span style="font-size:0.85rem;color:#71717a">{opt["desc"]}</span></div>',
            unsafe_allow_html=True,
        )

    if len(choices) > 3:
        st.warning("Select exactly 3.")

    elif len(choices) == 3:
        correct_count = sum(1 for c in choices if EVIDENCE_OPTIONS[c]["correct"])

        if correct_count == 3:
            st.success("**A, B, and D.** Conservation. Surface presentation. Variant-adversity correlation. Three defensible, reproducible, independently verifiable findings.")
            if not st.session_state.ch5_done:
                st.session_state.ch5_done = True
                st.session_state.score += 20
                add_evidence("Preprint assembled")
            _ending("full")

        elif correct_count == 2:
            bad = next(c for c in choices if not EVIDENCE_OPTIONS[c]["correct"])
            st.warning(f"**Almost.** `{bad}` would expose the source before the story could spread. NovaBridge had the preprint retracted in 31 hours. The two surviving findings were re-published independently a week later. Some things take longer.")
            if not st.session_state.ch5_done:
                st.session_state.ch5_done = True
                st.session_state.score += 10
            _ending("partial")

        else:
            st.error("**Retracted in 22 hours.** Two pieces of stolen classified material. National security invoked. The scientific community couldn't defend it. The story died in the dark.")
            if not st.session_state.ch5_done:
                st.session_state.ch5_done = True
            _ending("fail")


def _ending(outcome: str):
    if outcome == "full":
        st.markdown("""
        <div class="ending-text">
        The preprint posted at 11:47 PM.
        <br><br>
        By 6 AM, forty-three scientists in seven countries had replied to Yuna's emails.
        By noon, three independent labs had confirmed the variant mechanism.
        By the following week, the Congressional staffers had forwarded the registry summary
        to the Select Committee on Intelligence.
        <br><br>
        The story ran in two publications simultaneously, citing the preprint, citing public
        records, citing nothing that could be classified.
        <br><br>
        Helix's immunopeptidomics module was suspended pending investigation.
        NovaBridge's stock opened down thirty-four percent. Three executives were subpoenaed.
        <br><br>
        Mara sat in her apartment with Mila asleep down the hall and thought about a sentence
        from the paper: <em>Peptideins also include potentially transient products of cellular
        stress or defective ribosome translation.</em>
        <br><br>
        The body keeps the score, she thought. The genome keeps the score.
        And sometimes the score is also the thing that saves you.
        </div>
        """, unsafe_allow_html=True)

    elif outcome == "partial":
        st.markdown("""
        <div class="ending-text partial">
        The preprint posted at 11:47 PM. It was retracted at 6:23 AM.
        <br><br>
        The two findings that survived were enough for independent labs to re-publish within the week.
        The story took longer to reach the press. Rael disappeared for six weeks.
        Darius's cousin lost his contract.
        <br><br>
        The variant was eventually named. The registry was never publicly confirmed.
        <br><br>
        Some things take longer to surface than others.
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="ending-text fail">
        The preprint posted at 11:47 PM. It was retracted at 9:51 AM.
        <br><br>
        The classification order arrived the following morning.
        Yuna's university placed her on administrative leave pending review.
        Rael was unreachable. Darius's cousin's company lost its federal contract.
        <br><br>
        Mara sat in her apartment and tried to remember the name of the protein
        that kept cells alive.
        </div>
        """, unsafe_allow_html=True)

    _final_score()


def _final_score():
    st.markdown("---")
    score = st.session_state.score
    st.markdown(f'<div class="score-big">{score}<span style="font-size:1rem;color:#71717a">/100</span></div>', unsafe_allow_html=True)
    st.caption(f"Evidence collected: {len(st.session_state.evidence)}/5  ·  Investigation complete")

    if score == 100:
        st.balloons()
        st.success("Full exposure. The investigation is complete.")
    elif score >= 60:
        st.info("Partial exposure. Some of the story reached the light.")
    else:
        st.error("The investigation stalled. The dark proteome stays dark.")

    st.markdown("")
    if st.button("↩ Play again", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_df()
    sidebar(df)
    title_block()

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
