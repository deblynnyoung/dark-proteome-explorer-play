"""Train and run the ncORF detectability classifier."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path("models/classifier.joblib")
SCALER_PATH = Path("models/scaler.joblib")


def train(
    X: pd.DataFrame,
    y: pd.Series,
    save: bool = True,
    demo_mode: bool = False,
) -> tuple[GradientBoostingClassifier, StandardScaler]:
    """
    Train a GradientBoosting classifier on ncORF features.

    In demo_mode (tiny dataset), skips train/test split and CV
    since there isn't enough data for meaningful evaluation.
    """
    X = X.fillna(0)
    y = y.loc[X.index]

    scaler = StandardScaler()

    if demo_mode or len(X) < 30:
        print("  Demo mode: training on full dataset (too few samples for split).")
        X_s = scaler.fit_transform(X)
        clf = GradientBoostingClassifier(n_estimators=50, max_depth=2, random_state=42)
        clf.fit(X_s, y)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )

        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        # Handle class imbalance (~25% positive rate in the paper)
        smote = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum() - 1))
        X_res, y_res = smote.fit_resample(X_train_s, y_train)

        clf = GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, random_state=42,
        )
        clf.fit(X_res, y_res)

        probs = clf.predict_proba(X_test_s)[:, 1]
        print(f"  AUROC            : {roc_auc_score(y_test, probs):.3f}")
        print(f"  Avg Precision    : {average_precision_score(y_test, probs):.3f}")
        print(classification_report(y_test, clf.predict(X_test_s)))

    if save:
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump(clf, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        print(f"  Saved -> {MODEL_PATH}")

    return clf, scaler


def load_model() -> tuple[GradientBoostingClassifier, StandardScaler]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model found at {MODEL_PATH}. Run train_classifier.py first."
        )
    return joblib.load(MODEL_PATH), joblib.load(SCALER_PATH)


def predict(
    X: pd.DataFrame,
    clf: GradientBoostingClassifier,
    scaler: StandardScaler,
) -> pd.Series:
    """Return detection probability for each sequence (index = sequence ID)."""
    X_s = scaler.transform(X.fillna(0))
    probs = clf.predict_proba(X_s)[:, 1]
    return pd.Series(probs, index=X.index, name="detection_probability")


def feature_importances(
    clf: GradientBoostingClassifier,
    feature_names: list[str],
) -> pd.Series:
    return (
        pd.Series(clf.feature_importances_, index=feature_names, name="importance")
        .sort_values(ascending=False)
    )
