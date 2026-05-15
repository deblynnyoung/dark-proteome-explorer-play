"""Feature engineering from amino acid sequences using BioPython."""

from __future__ import annotations

import warnings

import pandas as pd
from Bio.SeqUtils.ProtParam import ProteinAnalysis

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")
VALID_AA = set(AMINO_ACIDS)


def _clean(seq: str) -> str:
    return "".join(aa for aa in seq.upper() if aa in VALID_AA)


def compute_features(sequence: str) -> dict[str, float]:
    """Compute physicochemical and compositional features for one sequence."""
    seq = _clean(sequence)
    if len(seq) < 5:
        raise ValueError(f"Sequence too short after cleaning: '{seq}'")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pa = ProteinAnalysis(seq)

    helix, turn, sheet = pa.secondary_structure_fraction()
    aa_pct = pa.amino_acids_percent

    features: dict[str, float] = {
        "length": float(len(seq)),
        "molecular_weight": pa.molecular_weight(),
        "isoelectric_point": pa.isoelectric_point(),
        "gravy": pa.gravy(),
        "aromaticity": pa.aromaticity(),
        "instability_index": pa.instability_index(),
        "helix_fraction": helix,
        "turn_fraction": turn,
        "sheet_fraction": sheet,
        "n_positive": float(seq.count("K") + seq.count("R") + seq.count("H")),
        "n_negative": float(seq.count("D") + seq.count("E")),
        "charge_ratio": (seq.count("K") + seq.count("R")) / max(seq.count("D") + seq.count("E"), 1),
        "unique_aa_fraction": len(set(seq)) / 20.0,
    }
    for aa in AMINO_ACIDS:
        features[f"aa_{aa}"] = aa_pct.get(aa, 0.0)

    return features


def sequences_to_features(sequences: dict[str, str]) -> pd.DataFrame:
    """Convert a {id: sequence} dict into a BioPython feature DataFrame."""
    rows = []
    skipped = []
    for seq_id, seq in sequences.items():
        try:
            feat = compute_features(seq)
            feat["id"] = seq_id
            rows.append(feat)
        except Exception:
            skipped.append(seq_id)

    if skipped:
        print(f"  Skipped {len(skipped)} sequences: {skipped[:5]}{'...' if len(skipped) > 5 else ''}")

    df = pd.DataFrame(rows).set_index("id")
    return df.astype(float)


def combine_features(bio_features: pd.DataFrame, paper_features: pd.DataFrame) -> pd.DataFrame:
    """
    Merge BioPython features with the paper's pre-computed structural features.
    Paper features take precedence for 'length' (same value, but paper's is exact).
    The combined matrix is the richest possible feature set.
    """
    # Drop duplicate 'length' from bio_features since paper has it
    bio = bio_features.drop(columns=["length"], errors="ignore")
    combined = paper_features.join(bio, how="inner")
    return combined.fillna(0)
