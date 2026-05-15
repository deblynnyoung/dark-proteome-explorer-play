"""
Dark Proteome Explorer - Streamlit app.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
import py3Dmol
import streamlit as st
import streamlit.components.v1 as components
from sklearn.metrics import average_precision_score, roc_auc_score

from src.classifier import feature_importances, predict, train
from src.data_loader import DEMO_LABELS, DEMO_SEQUENCES, load_fasta, load_moesm9
from src.esmfold import fold_batch, mean_plddt
from src.features import combine_features, sequences_to_features

STRUCTURES_DIR = Path("structures")

# ── Easter egg content ────────────────────────────────────────────────────────

LOADING_MSGS = [
    "Interrogating the dark proteome...",
    "Pestering the ribosomes...",
    "Whispering to the mass spectrometer...",
    "Translating the untranslatable...",
    "Convincing sklearn to cooperate...",
    "Mining the proteome's dark corners...",
    "Asking AlphaFold nicely...",
    "Bribing the gradient boosting trees...",
    "Rummaging through non-canonical open reading frames...",
    "Doing science at you very fast...",
]

FOLD_MSGS = [
    "Folding proteins like origami...",
    "Asking ESMFold to do its thing...",
    "Simulating millions of years of evolution...",
    "Predicting structures with neural magic...",
    "Convincing amino acids to behave...",
]

FACTS = [
    "MOTS-c is a 16 AA microprotein encoded in mitochondrial DNA that regulates metabolism and extends healthy lifespan in mice.",
    "Humanin, encoded in the mitochondrial 16S rRNA gene, protects neurons from Alzheimer's-related amyloid-beta toxicity.",
    "The TransCODE Consortium analyzed 95,520 proteomics experiments to build their ncORF landscape.",
    "Only 16 ncORFs reach Tier 1A — verified with synthetic peptides. You could fit all their names on a Post-it note.",
    "Microproteins can be as short as 11 amino acids and still be biologically functional.",
    "The term 'peptidein' was coined in 2026 to describe microproteins of indeterminate functional potential.",
    "Some microproteins are encoded in sequences once dismissed as 'junk DNA'.",
    "SHLP2, a mitochondria-derived microprotein, has been linked to promoting eye health and reducing retinal degeneration.",
    "The dark proteome may contain thousands of functional proteins we haven't discovered yet.",
    "Ribo-seq (ribosome profiling) revealed that ribosomes translate far more of the genome than we ever expected.",
    "pLDDT scores above 90 from AlphaFold are considered more reliable than many experimental structures.",
    "The human proteome was thought to contain ~20,000 proteins. Microproteins may add thousands more.",
]

KNOWN_MICROPROTEINS: dict[str, dict] = {
    "MRWQEMGYIFYPRKLR": {
        "name": "MOTS-c",
        "fact": "Discovered in 2015, MOTS-c is encoded in mitochondrial DNA and travels to the nucleus under stress to regulate gene expression. It extends healthy lifespan in mice.",
    },
    "MAPRGFSCLLLLTSEIDLPVKRRA": {
        "name": "Humanin",
        "fact": "Humanin was discovered in brain tissue from an Alzheimer's patient in 2001. It's encoded within the 16S rRNA gene of mitochondrial DNA and protects neurons from amyloid-beta toxicity.",
    },
}

# ── Change this to your personal message for your friend! ─────────────────────
SECRET_MESSAGE = "I love you so much, my nosewipefingertofingerbestladybabypumpkinmuffinloverpants!"

# ── Tier config ───────────────────────────────────────────────────────────────
TIER_COLORS = {
    "Tier 1A": "#1a7f37",
    "Tier 1B": "#2da44e",
    "Tier 2A": "#6fdd8b",
    "Tier 2B": "#a8f0b8",
    "Tier 3":  "#d4edda",
    "Tier 4":  "#e0e0e0",
}
TIER_DESC = {
    "Tier 1A": "Verified with synthetic peptides",
    "Tier 1B": "High-confidence proteomics detection",
    "Tier 2A": "Detected by proteomics",
    "Tier 2B": "Detected by HLA immunopeptidomics",
    "Tier 3":  "Lower-confidence detection",
    "Tier 4":  "Not detected",
}


# ── Celebration functions ─────────────────────────────────────────────────────

def confetti():
    """Rainbow confetti burst — fires on the parent Streamlit page."""
    components.html("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
        <script>
        var canvas = window.parent.document.createElement("canvas");
        window.parent.document.body.appendChild(canvas);
        canvas.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;pointer-events:none;";
        var burst = confetti.create(canvas, { resize: true, useWorker: true });
        burst({ particleCount: 200, spread: 100, origin: { y: 0.5 } });
        setTimeout(function () { canvas.remove(); }, 4000);
        </script>
    """, height=1)


def gold_confetti():
    """Gold confetti burst — for high-confidence structure predictions."""
    components.html("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
        <script>
        var canvas = window.parent.document.createElement("canvas");
        window.parent.document.body.appendChild(canvas);
        canvas.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;pointer-events:none;";
        var burst = confetti.create(canvas, { resize: true, useWorker: true });
        burst({
            particleCount: 120, spread: 60, origin: { y: 0.5 },
            colors: ['#FFD700','#FFA500','#FFEC8B','#FFF8DC','#FFD700']
        });
        setTimeout(function () { canvas.remove(); }, 4000);
        </script>
    """, height=1)


def inject_easter_eggs(secret_message: str):
    """Inject persistent JS easter eggs: Konami code + title click secret."""
    safe_msg = secret_message.replace("`", "'").replace("\\", "\\\\")
    components.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
        <script>
        (function() {{
            var parent = window.parent;

            // ── Konami code: up up down down left right left right B A ─────────
            var konamiSeq = [38,38,40,40,37,39,37,39,66,65];
            var konamiIdx = 0;
            parent.document.addEventListener('keydown', function(e) {{
                konamiIdx = (e.keyCode === konamiSeq[konamiIdx]) ? konamiIdx + 1 : (e.keyCode === konamiSeq[0] ? 1 : 0);
                if (konamiIdx === konamiSeq.length) {{
                    konamiIdx = 0;
                    var existing = parent.document.getElementById('konami-style');
                    if (existing) {{
                        existing.remove();
                    }} else {{
                        var s = parent.document.createElement('style');
                        s.id = 'konami-style';
                        s.textContent = `
                            .stApp {{ background: linear-gradient(135deg,#0d0d2b,#1a0533,#0d1b2b) !important; }}
                            .stApp h1, .stApp h2, .stApp h3 {{ color: #a855f7 !important; }}
                            .stApp p, .stApp label, .stApp span {{ color: #c4b5fd !important; }}
                            .stApp .stButton button {{ background: #6d28d9 !important; border-color: #a855f7 !important; }}
                        `;
                        parent.document.head.appendChild(s);
                        var toast = parent.document.createElement('div');
                        toast.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#1a0533;color:#a855f7;border:2px solid #a855f7;padding:24px 40px;border-radius:12px;z-index:9999;font-size:18px;font-family:monospace;text-align:center;';
                        toast.innerHTML = '&#127756; DARK PROTEOME MODE ACTIVATED &#127756;<br><small style="color:#c4b5fd;font-size:13px;">Press again to return to the light</small>';
                        parent.document.body.appendChild(toast);
                        setTimeout(function() {{ toast.remove(); }}, 3000);
                    }}
                }}
            }});

            // ── Title click secret (7 clicks) ─────────────────────────────────
            var titleClicks = 0;
            function attachTitle() {{
                var h1 = parent.document.querySelector('h1');
                if (h1 && !h1.dataset.secretReady) {{
                    h1.dataset.secretReady = 'true';
                    h1.style.cursor = 'pointer';
                    h1.title = '';
                    h1.addEventListener('click', function() {{
                        titleClicks++;
                        if (titleClicks === 7) {{
                            titleClicks = 0;
                            var msg = parent.document.createElement('div');
                            msg.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;border:3px solid #ff69b4;padding:30px 44px;border-radius:16px;z-index:9999;font-size:15px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.15);max-width:380px;line-height:1.7;';
                            msg.innerHTML = `{safe_msg}`;
                            parent.document.body.appendChild(msg);
                            var canvas = parent.document.createElement('canvas');
                            parent.document.body.appendChild(canvas);
                            canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9998;pointer-events:none;';
                            var burst = confetti.create(canvas, {{ resize: true }});
                            burst({{ particleCount: 150, spread: 80, colors: ['#ff69b4','#ff1493','#ffb6c1','#fff','#ff69b4'] }});
                            setTimeout(function() {{ msg.remove(); canvas.remove(); }}, 6000);
                        }}
                    }});
                }}
            }}
            var t = setInterval(function() {{
                if (parent.document.querySelector('h1')) {{ attachTitle(); clearInterval(t); }}
            }}, 200);
        }})();
        </script>
    """, height=0)


# ── Model helpers ─────────────────────────────────────────────────────────────

def get_model():
    if "clf" not in st.session_state or "scaler" not in st.session_state:
        with st.spinner("Training model on demo data..."):
            X = sequences_to_features(DEMO_SEQUENCES)
            y = pd.Series(DEMO_LABELS).loc[X.index]
            clf, scaler = train(X, y, save=False, demo_mode=True)
            st.session_state["clf"] = clf
            st.session_state["scaler"] = scaler
    return st.session_state["clf"], st.session_state["scaler"]


# ── Page ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Dark Proteome Explorer", page_icon=":dna:", layout="wide")
st.title("Dark Proteome Explorer")
st.caption(
    "Predict detectability of ncORF-encoded microproteins and explore their 3D structures. "
    "Based on: *Expanding the human proteome with microproteins and peptideins* "
    "- TransCODE Consortium, Nature 2026."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Data Source")
    data_source = st.radio(
        "Choose input",
        ["MOESM9 (full paper dataset)", "Demo sequences (15)", "Upload FASTA"],
    )

    sequences: dict[str, str] = {}
    paper_features_df: pd.DataFrame | None = None
    tier_series: pd.Series | None = None

    if data_source == "MOESM9 (full paper dataset)":
        st.markdown(
            "**Step 1:** "
            "[Download MOESM9 here](https://static-content.springer.com/esm/art%3A10.1038"
            "%2Fs41586-026-10459-x/MediaObjects/41586_2026_10459_MOESM9_ESM.xlsx)"
            " (1.9 MB, free)\n\n"
            "**Step 2:** Upload it below."
        )
        moesm9_upload = st.file_uploader(
            "Upload 41586_2026_10459_MOESM9_ESM.xlsx",
            type=["xlsx"],
            key="moesm9_upload",
        )
        if moesm9_upload and st.button("Load MOESM9"):
            import io
            with st.spinner("Loading 7,264 ncORFs..."):
                file_bytes = io.BytesIO(moesm9_upload.read())
                seqs, labels, pf = load_moesm9(file_bytes)
                st.session_state["sequences"] = seqs
                st.session_state["labels"] = labels
                st.session_state["paper_features"] = pf
                file_bytes.seek(0)
                raw = pd.read_excel(file_bytes, sheet_name="Structural predictions").set_index("orf_id")
                st.session_state["tier_series"] = raw["tier"]
                st.session_state["plddt_esmfold"] = raw["plddt_esmfold"]
            with st.spinner(random.choice(LOADING_MSGS)):
                X_train = combine_features(sequences_to_features(seqs), pf)
                clf, scaler = train(X_train, labels.loc[X_train.index], save=False)
                st.session_state["clf"] = clf
                st.session_state["scaler"] = scaler
            st.success(f"Loaded {len(seqs):,} sequences and trained classifier.")
            confetti()

        if "sequences" in st.session_state:
            sequences = st.session_state["sequences"]
            paper_features_df = st.session_state.get("paper_features")
            tier_series = st.session_state.get("tier_series")

    elif data_source == "Demo sequences (15)":
        sequences = DEMO_SEQUENCES
        st.success("15 demo sequences loaded.")

    else:
        uploaded = st.file_uploader("Upload FASTA", type=["fasta", "fa", "txt"])
        if uploaded:
            sequences = load_fasta(uploaded.read().decode("utf-8"))
            st.success(f"{len(sequences)} sequences loaded.")

    st.divider()
    if "clf" in st.session_state:
        trained_on = "full dataset" if "labels" in st.session_state else "demo data"
        st.success(f"Model ready (trained on {trained_on})")
    else:
        st.info("Model will train automatically on first use.")

    if tier_series is not None:
        st.divider()
        st.markdown("**Paper tier breakdown**")
        tier_counts = tier_series.value_counts().reindex(TIER_COLORS.keys()).fillna(0).astype(int)
        for tier, count in tier_counts.items():
            pct = count / len(tier_series) * 100
            st.markdown(
                f"<span style='color:{TIER_COLORS[tier]};font-weight:bold'>{tier}</span> "
                f"- {count:,} ({pct:.1f}%)<br><small>{TIER_DESC[tier]}</small>",
                unsafe_allow_html=True,
            )

    # Rotating science fact
    st.divider()
    st.markdown(f"**Did you know?**\n\n*{random.choice(FACTS)}*")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_classify, tab_structure, tab_compare = st.tabs(
    ["Classify Sequences", "Explore Structures", "Compare with Paper"]
)


# =============================================================================
# TAB 1 - Classify
# =============================================================================
with tab_classify:
    st.subheader("Predict Detection Probability")

    if not sequences:
        st.info("Load sequences using the sidebar.")
        st.stop()

    n_max = min(len(sequences), 7264)
    n_display = st.slider("Sequences to classify", 10, n_max, min(n_max, 500))
    seq_subset = dict(list(sequences.items())[:n_display])

    if st.button("Run Classifier", type="primary"):
        clf, scaler = get_model()
        with st.spinner(random.choice(LOADING_MSGS)):
            bio_X = sequences_to_features(seq_subset)
            if paper_features_df is not None:
                pf_subset = paper_features_df.loc[paper_features_df.index.isin(bio_X.index)]
                X = combine_features(bio_X, pf_subset)
            else:
                X = bio_X
            probs = predict(X, clf, scaler)
            results = pd.DataFrame({
                "Sequence": pd.Series(seq_subset).str[:35] + "...",
                "Length (AA)": X["length"].astype(int),
                "pI": bio_X.reindex(X.index)["isoelectric_point"].round(2),
                "GRAVY": bio_X.reindex(X.index)["gravy"].round(3),
                "Detection Probability": probs.round(3),
            }).sort_values("Detection Probability", ascending=False)
            if tier_series is not None:
                results["Paper Tier"] = tier_series.reindex(results.index)

        st.session_state["results"] = results
        st.session_state["X"] = X
        st.session_state["probs"] = probs

        # ── Easter eggs triggered by results ─────────────────────────────────
        # Tier 1A alert
        if "Paper Tier" in results.columns and (results["Paper Tier"] == "Tier 1A").any():
            n1a = (results["Paper Tier"] == "Tier 1A").sum()
            st.balloons()
            st.success(
                f"You found {n1a} Tier 1A sequence{'s' if n1a > 1 else ''}! "
                f"Only 16 exist in the entire dataset — these are verified with synthetic peptides."
            )

        # Known microprotein recognition
        clean_seqs = {k: v.upper().replace("*", "").replace("-", "") for k, v in seq_subset.items()}
        for seq_id, seq in clean_seqs.items():
            if seq in KNOWN_MICROPROTEINS:
                mp = KNOWN_MICROPROTEINS[seq]
                st.info(
                    f"**Hey, you're looking at {mp['name']}!** {mp['fact']}"
                )

    if "results" in st.session_state:
        results = st.session_state["results"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Classified", f"{len(results):,}")
        col2.metric("Prob > 0.7", int((results["Detection Probability"] > 0.7).sum()))
        col3.metric("Prob > 0.5", int((results["Detection Probability"] > 0.5).sum()))
        col4.metric("Mean prob", f"{results['Detection Probability'].mean():.3f}")

        st.dataframe(
            results.style
            .background_gradient(subset=["Detection Probability"], cmap="RdYlGn", vmin=0, vmax=1)
            .format({"Detection Probability": "{:.3f}"}),
            width="stretch",
            height=400,
        )

        # Golden sequences (prob > 0.9)
        golden = results[results["Detection Probability"] > 0.9]
        if not golden.empty:
            st.markdown("---")
            st.markdown(
                "<div style='background:linear-gradient(90deg,#FFF8DC,#FFD700,#FFF8DC);"
                "border:2px solid #FFD700;border-radius:10px;padding:12px 20px;margin:4px 0;'>"
                f"<b>Golden sequences (prob > 0.9): {len(golden)}</b> — "
                "our model is very confident these are detectable."
                "</div>",
                unsafe_allow_html=True,
            )
            st.dataframe(golden[["Sequence", "Length (AA)", "Detection Probability"]], width="stretch")

        with st.expander("Top 15 feature importances"):
            importances = feature_importances(
                st.session_state["clf"],
                st.session_state["X"].columns.tolist(),
            ).head(15)
            st.bar_chart(importances)


# =============================================================================
# TAB 2 - Structure
# =============================================================================
with tab_structure:
    st.subheader("Predict & Visualize 3D Structure")
    st.caption(
        "Structures predicted via Meta's [ESMFold API](https://esmatlas.com/). "
        "Colors: blue = high pLDDT confidence, red = low."
    )

    if not sequences:
        st.info("Load sequences using the sidebar.")
        st.stop()

    seq_options = list(sequences.keys())
    if "results" in st.session_state:
        ranked = st.session_state["results"].index.tolist()
        seq_options = [s for s in ranked if s in sequences] + [s for s in seq_options if s not in ranked]

    selected_ids = st.multiselect(
        "Select sequences to fold",
        options=seq_options,
        default=seq_options[:3],
        max_selections=10,
    )

    if selected_ids:
        if "plddt_esmfold" in st.session_state:
            pre = st.session_state["plddt_esmfold"].reindex(selected_ids).dropna()
            if not pre.empty:
                st.info("Pre-computed ESMFold pLDDT scores from the paper (no API call needed):")
                st.dataframe(
                    pre.rename("pLDDT (paper)").reset_index().rename(columns={"orf_id": "ID"})
                    .style.background_gradient(subset=["pLDDT (paper)"], cmap="RdYlGn", vmin=50, vmax=90),
                    width="stretch",
                )

        if st.button("Fold & Visualize (ESMFold API)", type="primary"):
            to_fold = {sid: sequences[sid] for sid in selected_ids}
            with st.spinner(random.choice(FOLD_MSGS)):
                pdbs = fold_batch(to_fold, output_dir=STRUCTURES_DIR, delay=1.5)
            st.session_state["pdbs"] = pdbs
            if pdbs:
                st.success(f"Folded {len(pdbs)}/{len(to_fold)} sequences.")
                # Gold confetti for high-confidence structures
                avg_plddts = [mean_plddt(p) for p in pdbs.values() if mean_plddt(p)]
                if avg_plddts and (sum(avg_plddts) / len(avg_plddts)) > 85:
                    gold_confetti()
                    st.info("High-confidence structures — mean pLDDT above 85!")
            else:
                st.error("All folds failed - the ESMFold API may be temporarily down.")

    if "pdbs" in st.session_state and st.session_state["pdbs"]:
        pdbs = st.session_state["pdbs"]
        st.divider()

        view_id = st.selectbox("View structure", options=list(pdbs.keys()))
        pdb_str = pdbs[view_id]
        avg_plddt = mean_plddt(pdb_str)

        col_info, col_3d = st.columns([1, 3])
        with col_info:
            st.metric("Mean pLDDT", f"{avg_plddt:.1f}" if avg_plddt else "N/A")
            st.metric("Length", f"{len(sequences[view_id])} AA")
            if tier_series is not None and view_id in tier_series.index:
                st.metric("Paper Tier", tier_series[view_id])
            st.code(sequences[view_id], language=None)
            st.caption(
                "**pLDDT guide**\n\n"
                "- >90: very high confidence\n"
                "- 70-90: confident\n"
                "- 50-70: low confidence\n"
                "- <50: likely disordered"
            )

        with col_3d:
            view = py3Dmol.view(width=620, height=460)
            view.addModel(pdb_str, "pdb")
            view.setStyle({}, {"cartoon": {"colorscheme": {"prop": "b", "gradient": "roygb", "min": 50, "max": 90}}})
            view.addSurface("VDW", {"opacity": 0.25, "colorscheme": {"prop": "b", "gradient": "roygb", "min": 50, "max": 90}})
            view.zoomTo()
            components.html(view._make_html(), height=480)


# =============================================================================
# TAB 3 - Compare with Paper
# =============================================================================
with tab_compare:
    st.subheader("Our Model vs. Paper's Tier Classification")
    st.caption(
        "How well do our predicted probabilities align with the paper's tier assignments? "
        "A good model gives high scores to Tier 1/2/3 and low scores to Tier 4."
    )

    if "probs" not in st.session_state or tier_series is None:
        st.info("Run the classifier on MOESM9 data first (use the 'Classify Sequences' tab).")
        st.stop()

    probs = st.session_state["probs"]
    tier_aligned = tier_series.reindex(probs.index)
    compare_df = pd.DataFrame({
        "Our Probability": probs,
        "Paper Tier": tier_aligned,
        "Detected (paper)": (tier_aligned != "Tier 4").astype(int),
    }).dropna()

    y_true = compare_df["Detected (paper)"]
    y_prob = compare_df["Our Probability"]
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("AUROC vs. paper labels", f"{roc_auc_score(y_true, y_prob):.3f}")
    col_b.metric("Avg Precision vs. paper labels", f"{average_precision_score(y_true, y_prob):.3f}")
    col_c.metric("Sequences compared", f"{len(compare_df):,}")

    st.divider()
    st.markdown("**Mean predicted probability by paper tier**")
    tier_means = (
        compare_df.groupby("Paper Tier")["Our Probability"]
        .agg(["mean", "median", "count"])
        .reindex(TIER_COLORS.keys()).dropna()
        .rename(columns={"mean": "Mean Prob", "median": "Median Prob", "count": "Count"})
    )
    st.dataframe(
        tier_means.style
        .background_gradient(subset=["Mean Prob"], cmap="RdYlGn", vmin=0, vmax=1)
        .format({"Mean Prob": "{:.3f}", "Median Prob": "{:.3f}"}),
        width="stretch",
    )

    st.divider()
    st.markdown("**Score distribution per tier** (sorted, up to 500 per tier)")
    chart_data = {
        tier: compare_df.loc[compare_df["Paper Tier"] == tier, "Our Probability"]
        .sort_values().reset_index(drop=True).iloc[:500]
        for tier in TIER_COLORS if tier in compare_df["Paper Tier"].values
    }
    st.line_chart(pd.DataFrame(dict(chart_data)))


# ── Persistent easter egg JS (Konami + title click) ───────────────────────────
inject_easter_eggs(SECRET_MESSAGE)
