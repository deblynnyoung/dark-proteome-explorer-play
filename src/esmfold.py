"""
ESMFold API client for microprotein structure prediction.

Uses Meta's public ESMFold endpoint (no API key required).
Max sequence length: ~400 AA. Microproteins are typically <100 AA so this is fine.
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

ESMFOLD_URL = "https://api.esmatlas.com/foldSequence/v1/pdb/"
MAX_LENGTH = 400


def fold_sequence(sequence: str, max_retries: int = 3) -> str | None:
    """
    Fold a single amino acid sequence via ESMFold API.
    Returns the PDB string, or None on failure.
    """
    sequence = sequence.upper().replace("*", "").replace("-", "")
    if len(sequence) > MAX_LENGTH:
        print(f"  Skipping: sequence length {len(sequence)} > {MAX_LENGTH} AA limit.")
        return None
    if len(sequence) < 6:
        print(f"  Skipping: sequence too short ({len(sequence)} AA).")
        return None

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                ESMFOLD_URL,
                data=sequence,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=120,
            )
            if resp.status_code == 200:
                return resp.text
            print(f"  ESMFold returned {resp.status_code} (attempt {attempt + 1})")
        except requests.RequestException as e:
            print(f"  Request error (attempt {attempt + 1}): {e}")
        time.sleep(2 ** attempt)

    return None


def fold_batch(
    sequences: dict[str, str],
    output_dir: Path,
    delay: float = 1.5,
    force: bool = False,
) -> dict[str, str]:
    """
    Fold multiple sequences, caching results as .pdb files.

    Args:
        sequences  : {id: amino_acid_sequence}
        output_dir : directory to cache PDB files
        delay      : seconds between API calls (be polite to the free endpoint)
        force      : re-fold even if cached PDB exists

    Returns:
        {id: pdb_string} for successfully folded sequences
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

    for i, (seq_id, seq) in enumerate(sequences.items(), 1):
        pdb_path = output_dir / f"{seq_id}.pdb"
        print(f"  [{i}/{len(sequences)}] {seq_id} ({len(seq)} AA)", end=" ")

        if pdb_path.exists() and not force:
            print("(cached)")
            results[seq_id] = pdb_path.read_text()
            continue

        pdb = fold_sequence(seq)
        if pdb:
            pdb_path.write_text(pdb)
            results[seq_id] = pdb
            print("OK")
        else:
            print("FAILED")

        if i < len(sequences):
            time.sleep(delay)

    return results


def extract_plddt(pdb_str: str) -> list[float]:
    """
    Extract per-residue pLDDT scores from ESMFold PDB output.
    ESMFold stores pLDDT in the B-factor column of CA atoms.
    """
    scores = []
    for line in pdb_str.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                scores.append(float(line[60:66].strip()))
            except ValueError:
                pass
    return scores


def mean_plddt(pdb_str: str) -> float | None:
    scores = extract_plddt(pdb_str)
    return sum(scores) / len(scores) if scores else None
