"""
Dark Proteome Explorer - Streamlit app.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

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


def get_model():
    """Return (clf, scaler) from session_state, training if needed."""
    if "clf" not in st.session_state or "scaler" not in st.session_state:
        with st.spinner("Training model on demo data..."):
            import pandas as pd
            X = sequences_to_features(DEMO_SEQUENCES)
            y = pd.Series(DEMO_LABELS).loc[X.index]
            clf, scaler = train(X, y, save=False, demo_mode=True)
            st.session_state["clf"] = clf
            st.session_state["scaler"] = scaler
    return st.session_state["clf"], st.session_state["scaler"]

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

st.set_page_config(page_title="Dark Proteome Explorer", page_icon=":dna:", layout="wide")

st.title("Dark Proteome Explorer")
st.caption(
    "Predict detectability of ncORF-encoded microproteins and explore their 3D structures. "
    "Based on: *Expanding the human proteome with microproteins and peptideins* "
    "- TransCODE Consortium, Nature 2026."
)

# ---- Sidebar ----------------------------------------------------------------
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
                raw = pd.read_excel(
                    file_bytes, sheet_name="Structural predictions"
                ).set_index("orf_id")
                st.session_state["tier_series"] = raw["tier"]
                st.session_state["plddt_esmfold"] = raw["plddt_esmfold"]
            with st.spinner("Training classifier on full dataset (~30s)..."):
                X_train = combine_features(
                    sequences_to_features(seqs), pf
                )
                clf, scaler = train(X_train, labels.loc[X_train.index], save=False)
                st.session_state["clf"] = clf
                st.session_state["scaler"] = scaler
            st.success(f"Loaded {len(seqs):,} sequences and trained classifier.")

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
        tier_counts = (
            tier_series.value_counts()
            .reindex(TIER_COLORS.keys())
            .fillna(0)
            .astype(int)
        )
        for tier, count in tier_counts.items():
            pct = count / len(tier_series) * 100
            st.markdown(
                f"<span style='color:{TIER_COLORS[tier]};font-weight:bold'>{tier}</span> "
                f"- {count:,} ({pct:.1f}%)<br><small>{TIER_DESC[tier]}</small>",
                unsafe_allow_html=True,
            )


# ---- Tabs -------------------------------------------------------------------
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
        with st.spinner(f"Computing features for {len(seq_subset):,} sequences..."):
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
        seq_options = [s for s in ranked if s in sequences] + [
            s for s in seq_options if s not in ranked
        ]

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
                    pre.rename("pLDDT (paper)")
                    .reset_index()
                    .rename(columns={"orf_id": "ID"})
                    .style.background_gradient(
                        subset=["pLDDT (paper)"], cmap="RdYlGn", vmin=50, vmax=90
                    ),
                    width="stretch",
                )

        if st.button("Fold & Visualize (ESMFold API)", type="primary"):
            to_fold = {sid: sequences[sid] for sid in selected_ids}
            with st.spinner(f"Folding {len(to_fold)} sequences (~{len(to_fold) * 15}s)..."):
                pdbs = fold_batch(to_fold, output_dir=STRUCTURES_DIR, delay=1.5)
            st.session_state["pdbs"] = pdbs
            if pdbs:
                st.success(f"Folded {len(pdbs)}/{len(to_fold)} sequences.")
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
            view.setStyle({}, {"cartoon": {"colorscheme": {
                "prop": "b", "gradient": "roygb", "min": 50, "max": 90,
            }}})
            view.addSurface("VDW", {"opacity": 0.25, "colorscheme": {
                "prop": "b", "gradient": "roygb", "min": 50, "max": 90,
            }})
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

    # Overall metrics
    y_true = compare_df["Detected (paper)"]
    y_prob = compare_df["Our Probability"]
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("AUROC vs. paper labels", f"{roc_auc_score(y_true, y_prob):.3f}")
    col_b.metric("Avg Precision vs. paper labels", f"{average_precision_score(y_true, y_prob):.3f}")
    col_c.metric("Sequences compared", f"{len(compare_df):,}")

    st.divider()

    # Mean probability per tier
    st.markdown("**Mean predicted probability by paper tier**")
    tier_means = (
        compare_df.groupby("Paper Tier")["Our Probability"]
        .agg(["mean", "median", "count"])
        .reindex(TIER_COLORS.keys())
        .dropna()
        .rename(columns={"mean": "Mean Prob", "median": "Median Prob", "count": "Count"})
    )
    st.dataframe(
        tier_means.style
        .background_gradient(subset=["Mean Prob"], cmap="RdYlGn", vmin=0, vmax=1)
        .format({"Mean Prob": "{:.3f}", "Median Prob": "{:.3f}"}),
        width="stretch",
    )

    # Sorted score distribution per tier (one line per tier)
    st.divider()
    st.markdown("**Score distribution per tier** (sorted, up to 500 per tier)")
    chart_data = {
        tier: compare_df.loc[compare_df["Paper Tier"] == tier, "Our Probability"]
        .sort_values()
        .reset_index(drop=True)
        .iloc[:500]
        for tier in TIER_COLORS
        if tier in compare_df["Paper Tier"].values
    }
    st.line_chart(pd.DataFrame(dict(chart_data)))
