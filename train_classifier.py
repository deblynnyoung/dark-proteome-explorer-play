#!/usr/bin/env python3
"""
Train the ncORF detectability classifier.

Usage:
    # Real mode — MOESM9 from the Nature paper (recommended)
    python train_classifier.py --moesm9 path/to/41586_2026_10459_MOESM9_ESM.xlsx

    # Demo mode (tiny dataset, just to verify the pipeline works)
    python train_classifier.py

    # Custom FASTA + label CSV
    python train_classifier.py --fasta sequences.fasta --labels labels.csv
"""

import argparse

import pandas as pd

from src.classifier import train
from src.data_loader import (
    DEMO_LABELS,
    DEMO_SEQUENCES,
    load_fasta,
    load_moesm9,
    load_transccode_table,
)
from src.features import combine_features, sequences_to_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ncORF classifier")
    parser.add_argument("--moesm9", help="Path to 41586_2026_10459_MOESM9_ESM.xlsx (recommended)")
    parser.add_argument("--data", help="Generic TransCODE .xlsx/.csv with sequences + labels")
    parser.add_argument("--fasta", help="FASTA file with sequences")
    parser.add_argument("--labels", help="CSV with columns 'id' and 'detected' (used with --fasta)")
    args = parser.parse_args()

    demo_mode = False
    paper_features = None

    # ── Load data ────────────────────────────────────────────────────────────
    if args.moesm9:
        print(f"Loading MOESM9 from: {args.moesm9}")
        sequences, labels, paper_features = load_moesm9(args.moesm9)
        print(f"  {len(sequences)} sequences | positive rate: {labels.mean():.1%}")
        print(f"  Paper features: {paper_features.shape[1]} columns")

    elif args.data:
        print(f"Loading data from: {args.data}")
        sequences, labels = load_transccode_table(args.data)
        print(f"  {len(sequences)} sequences | positive rate: {labels.mean():.1%}")

    elif args.fasta and args.labels:
        print(f"Loading FASTA: {args.fasta}")
        sequences = load_fasta(args.fasta)
        label_df = pd.read_csv(args.labels).set_index("id")
        labels = label_df["detected"].astype(int)

    else:
        print("No data file provided -- using demo sequences (15 sequences).")
        print("  WARNING: Demo data is far too small for real evaluation.")
        print("  For real training, run:")
        print("    python train_classifier.py --moesm9 41586_2026_10459_MOESM9_ESM.xlsx\n")
        sequences = DEMO_SEQUENCES
        labels = pd.Series(DEMO_LABELS)
        demo_mode = True

    # ── Feature engineering ──────────────────────────────────────────────────
    print(f"Computing BioPython features for {len(sequences)} sequences...")
    bio_X = sequences_to_features(sequences)

    if paper_features is not None:
        print("Combining with paper's structural features...")
        X = combine_features(bio_X, paper_features)
        print(f"  Combined feature matrix: {X.shape[0]} sequences x {X.shape[1]} features")
    else:
        X = bio_X
        print(f"  Feature matrix: {X.shape[0]} sequences x {X.shape[1]} features")

    y = labels.loc[X.index]
    print(f"  Positive rate: {y.mean():.1%}\n")

    # ── Train ────────────────────────────────────────────────────────────────
    print("Training classifier...")
    clf, scaler = train(X, y, save=True, demo_mode=demo_mode)
    print("\nDone. Model saved to models/classifier.joblib")
    print("Run the app with: streamlit run app.py")


if __name__ == "__main__":
    main()
