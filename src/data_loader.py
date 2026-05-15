"""
Data loading utilities.

Primary data source: MOESM9 (Supplementary Table 14) from
  https://www.nature.com/articles/s41586-026-10459-x
  → "41586_2026_10459_MOESM9_ESM.xlsx"

Pass the downloaded file to load_moesm9().
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Union

import pandas as pd
from Bio import SeqIO

# ── Conservation ordering (least → most conserved) ───────────────────────────
CONSERVATION_ORDER = {
    "human - young": 0,
    "old world monkeys - young": 1,
    "primatomorpha - young": 2,
    "conserved": 3,
}

# ── Demo data (15 short microprotein-like sequences) ─────────────────────────
DEMO_SEQUENCES: dict[str, str] = {
    "ncorf_001": "MRWQEMGYIFYPRKLR",
    "ncorf_002": "MAPRGFSCLLLLTSEIDLPVKRRA",
    "ncorf_003": "MPFWLLAGLVFVSLAAGVDGFCRLFEDHLSL",
    "ncorf_004": "MAASGAASGLALLCALSLALAAAPAAAPTAAA",
    "ncorf_005": "MSSAGGNATSGAGSSAGGNAGSSNAGSSNAGSSNAG",
    "ncorf_006": "MKFLILLFNILCLFPVFAHPETLVKVKDAED",
    "ncorf_007": "MRIILLGAPGAGKGTQAQFIMEKYGIPQIS",
    "ncorf_008": "MSLSQLKIICQSTLRRFRSSQLNYSQHLPS",
    "ncorf_009": "MGKMASAAKDPSQRRSHSSSPGRGNNMAASK",
    "ncorf_010": "MFVFLVLLPLVSSQCVNLTTRTQLPPAYTN",
    "ncorf_011": "MAAAPAAASAAAPAAASAAAPAAASAAAPAAAS",
    "ncorf_012": "MDEEKIEPKEDEEEESDGDKDDKDGSLEEPKK",
    "ncorf_013": "MEVQGLPGQLRFLLVTLAIAVAQSPAMRSEA",
    "ncorf_014": "MHSSSVPSPESPEPEPEPEPEPEPEPEPSSPE",
    "ncorf_015": "MASNDYTQQATQSYGAYPTQPGQGYSQQSSQ",
}

DEMO_LABELS: dict[str, int] = {
    "ncorf_001": 1, "ncorf_002": 1, "ncorf_003": 1,
    "ncorf_004": 0, "ncorf_005": 0, "ncorf_006": 1,
    "ncorf_007": 0, "ncorf_008": 0, "ncorf_009": 1,
    "ncorf_010": 0, "ncorf_011": 0, "ncorf_012": 1,
    "ncorf_013": 1, "ncorf_014": 0, "ncorf_015": 0,
}


def load_moesm9(path) -> tuple[dict[str, str], pd.Series, pd.DataFrame]:
    """
    Load MOESM9 (structural predictions table) from the TransCODE Nature paper.

    File: 41586_2026_10459_MOESM9_ESM.xlsx, sheet "Structural predictions"

    Label derivation:
        Tier 1A / 1B / 2A / 2B / 3 → detected (1)   [1,805 sequences]
        Tier 4                       → not detected (0) [5,459 sequences]

    Returns:
        sequences      : dict[orf_id -> amino_acid_sequence]
        labels         : pd.Series[orf_id -> int (0 or 1)]
        paper_features : pd.DataFrame of pre-computed structural/conservation features
    """
    df = pd.read_excel(path, sheet_name="Structural predictions", engine="openpyxl").set_index("orf_id")

    # Clean sequences
    sequences = (
        df["sequence"]
        .str.upper()
        .str.replace(r"[*\-]", "", regex=True)
        .to_dict()
    )

    # Binary label: anything that's not Tier 4 was detected
    labels = (df["tier"] != "Tier 4").astype(int).rename("detected")

    # ── Build paper feature matrix ────────────────────────────────────────────
    feats = pd.DataFrame(index=df.index)

    # Structure prediction scores (3 tools × 2 metrics)
    for col in ["plddt_esmfold", "n70_esmfold", "plddt_alphafold",
                "n70_alphafold", "plddt_omegafold", "n70_omegafold"]:
        feats[col] = pd.to_numeric(df[col], errors="coerce")

    # Length and disorder
    feats["length"] = df["length"]
    feats["disorder_average"] = df["disorder_average_alphafold_dssp"]
    feats["cov_total"] = df["cov_total"]
    feats["cov_disordered"] = df["cov_disordered"]

    # ELM motif counts
    feats["n_elm_total"] = df["n_elm_total"]
    feats["n_elm_dis"] = df["n_elm_dis"]

    # Prosite signatures
    feats["n_prosite"] = df["n_prosite"]
    feats["cov_prosite"] = df["cov_prosite"]

    # Conservation (ordinal encode)
    feats["conservation_score"] = df["Conservation.ORF"].map(CONSERVATION_ORDER).fillna(0)

    # PhyloCSF scores (stored as strings, convert to float)
    feats["phylocsf_primates"] = pd.to_numeric(df["PhyloCSF.primates"], errors="coerce").fillna(0)
    feats["phylocsf_mammals"] = pd.to_numeric(df["PhyloCSF.mammals"], errors="coerce").fillna(0)

    paper_features = feats.fillna(0)

    return sequences, labels, paper_features


def load_fasta(source: Union[str, Path]) -> dict[str, str]:
    """Parse a FASTA file or string into {id: sequence}."""
    path = Path(source)
    if path.exists():
        records = SeqIO.parse(str(path), "fasta")
    else:
        records = SeqIO.parse(StringIO(str(source)), "fasta")
    return {rec.id: str(rec.seq).upper().replace("*", "").replace("-", "") for rec in records}


def load_transccode_table(path: Union[str, Path]) -> tuple[dict[str, str], pd.Series]:
    """Generic loader for supplementary tables with auto-detected columns."""
    path = Path(path)
    df = pd.read_excel(path) if path.suffix in (".xlsx", ".xls") else pd.read_csv(path)

    cols_lower = {c.lower(): c for c in df.columns}
    id_col = next(
        (cols_lower[k] for k in ("id", "orf_id", "ncorf_id", "name") if k in cols_lower),
        df.columns[0],
    )
    seq_col = next((c for c in df.columns if "seq" in c.lower()), None)
    label_col = next(
        (c for c in df.columns if any(x in c.lower() for x in ("detect", "label", "observed", "translat"))),
        None,
    )

    if seq_col is None:
        raise ValueError("Could not find a sequence column (expected a column with 'seq' in the name).")
    if label_col is None:
        raise ValueError("Could not find a label column (expected 'detect', 'label', 'observed', or 'translat').")

    df = df.set_index(id_col)
    sequences = df[seq_col].str.upper().str.replace(r"[*\-]", "", regex=True).to_dict()
    labels = df[label_col].astype(int)
    return sequences, labels
