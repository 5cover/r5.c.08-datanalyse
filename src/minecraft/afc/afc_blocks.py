#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFC (TD-style) — builds a contingency table from two categorical columns,
standardizes it (z-score), runs Bartlett’s sphericity test, chooses the
# of factors by eigenvalue≥1, and plots factor maps with 3 rotations.

Usage:
  python afc_td.py --file data.csv --x ColA --y ColB
  # Or let it auto-pick two categorical columns:
  python afc_td.py --file data.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity


# ------------------------------ I/O ------------------------------

def read_any(path: Path, sep: Optional[str] = None) -> pd.DataFrame:
    """Read CSV/JSON by extension; CSV tries provided sep then common fallbacks."""
    ext = path.suffix.lower()
    if ext == ".json":
        return pd.read_json(path)
    if ext in {".csv", ".tsv", ".txt"}:
        if sep is not None:
            return pd.read_csv(path, sep=sep)
        for candidate in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(path, sep=candidate)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                pass
        return pd.read_csv(path)
    return pd.read_table(path)


def detect_two_categoricals(df: pd.DataFrame) -> Tuple[str, str]:
    """Pick two likely categorical columns (object/category or small cardinality)."""
    candidates = []
    for c in df.columns:
        ser = df[c]
        nunique = ser.nunique(dropna=True)
        if ser.dtype == "object" or str(ser.dtype) == "category" or nunique <= 30:
            candidates.append((c, nunique))
    # Prefer the lowest-but-usable cardinalities
    candidates.sort(key=lambda x: (x[1], x[0]))
    if len(candidates) >= 2:
        return candidates[0][0], candidates[1][0]
    # If not enough, just take first two columns
    cols = list(df.columns)
    if len(cols) < 2:
        raise ValueError("Need at least two columns to build a contingency table.")
    return cols[0], cols[1]


# ------------------------------ Prep ------------------------------

def build_crosstab(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """Cross-tabulate two categorical columns."""
    ct = pd.crosstab(df[x].astype(str), df[y].astype(str))
    # drop empty rows/cols if any
    ct = ct.loc[(ct.sum(axis=1) > 0), (ct.sum(axis=0) > 0)]
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        raise ValueError("Contingency table is degenerate (need ≥2 rows and ≥2 columns).")
    return ct


def zscore_df(M: pd.DataFrame) -> pd.DataFrame:
    """(X - mean) / std column-wise, ddof=1; replace inf/nan by 0 (TD style)."""
    temp = M.sub(M.mean(axis=0), axis=1)
    std = M.std(axis=0, ddof=1).replace(0, np.nan)
    Z = temp.div(std, axis=1)
    return Z.replace([np.inf, -np.inf], np.nan).fillna(0.0)


# ------------------------------ AFC (TD-style via FactorAnalyzer) ------------------------------

def bartlett_pvalue(Z: pd.DataFrame) -> float:
    """Bartlett’s sphericity p-value on standardized matrix."""
    chi2, p = calculate_bartlett_sphericity(Z)
    return float(p)


def eigenvalues_from_data(Z: pd.DataFrame) -> np.ndarray:
    """
    Use FactorAnalyzer to fetch eigenvalues of the correlation matrix (TD approach).
    """
    fa = FactorAnalyzer(rotation=None)
    fa.fit(Z)
    ev, _ = fa.get_eigenvalues()
    return np.asarray(ev)


def choose_n_factors(ev: np.ndarray, n_rows: int, n_cols: int) -> int:
    """Keep eigenvalues ≥ 1, limited by min(n_cols-1, n_rows-1); at least 2."""
    n_max = max(1, min(n_cols - 1, n_rows - 1))
    n_keep = int(np.sum(ev >= 1.0))
    if n_keep <= 0:
        n_keep = 2
    return min(n_keep, n_max)


def fit_factors(Z: pd.DataFrame, n_factors: int, rotation: Optional[str]) -> FactorAnalyzer:
    fa = FactorAnalyzer(n_factors=n_factors, rotation=rotation)
    fa.fit(Z)
    return fa


# ------------------------------ Plotting ------------------------------

def plot_scree(ev: np.ndarray, out_path: Path):
    plt.figure(figsize=(7, 4))
    xs = np.arange(1, len(ev) + 1)
    plt.scatter(xs, ev)
    plt.plot(xs, ev)
    plt.title("Scree Plot (valeurs propres)")
    plt.xlabel("Facteurs")
    plt.ylabel("Valeur propre")
    plt.grid(True, linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def plot_factor_maps(
    Z: pd.DataFrame,
    fa: FactorAnalyzer,
    ct_cols: List[str],
    ct_rows: List[str],
    title: str,
    out_path: Path,
):
    """
    Show variables (columns of crosstab) as loadings, and row categories as factor scores.
    - Variables: fa.loadings_ -> shape (n_features, n_factors)
    - Row scores: fa.transform(Z) -> shape (n_rows, n_factors)
    We display first two factors.
    """
    load = fa.loadings_
    scores = fa.transform(Z)

    if load.shape[1] < 2 or scores.shape[1] < 2:
        # Plot only Dim1 if necessary, but we expect ≥2
        print("Warning: fewer than 2 factors; plotting first two available.")

    x_idx, y_idx = 0, 1 if load.shape[1] > 1 else 0

    fig, ax = plt.subplots(figsize=(7, 6))

    # Variables (columns of the contingency table)
    ax.scatter(load[:, x_idx], load[:, y_idx], s=40, alpha=0.9, label="Variables (colonnes)")
    for (xv, yv, name) in zip(load[:, x_idx], load[:, y_idx], ct_cols):
        ax.text(xv + 0.02, yv + 0.02, str(name), ha="center", va="center", fontsize=8)

    # Row categories as scores
    ax.scatter(scores[:, x_idx], scores[:, y_idx], s=24, marker="^", alpha=0.8, label="Modalités (lignes)")
    for (xr, yr, name) in zip(scores[:, x_idx], scores[:, y_idx], ct_rows):
        ax.text(xr + 0.02, yr + 0.02, str(name), ha="center", va="center", fontsize=8)

    ax.axhline(0, linewidth=0.6, color="k")
    ax.axvline(0, linewidth=0.6, color="k")
    ax.set_xlabel("Facteur 1")
    ax.set_ylabel("Facteur 2")
    ax.set_title(title)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


# ------------------------------ Main ------------------------------

def main():
    ap = argparse.ArgumentParser(description="AFC (TD-style) from two categorical columns.")
    ap.add_argument("--file", required=True, help="Input CSV/JSON path")
    ap.add_argument("--sep", default=None, help="CSV separator (auto if omitted)")
    ap.add_argument("--x", default=None, help="Column for rows (categorical)")
    ap.add_argument("--y", default=None, help="Column for cols (categorical)")
    ap.add_argument("--out", default="afc_outputs", help="Output directory")
    args = ap.parse_args()

    path = Path(args.file)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_any(path, sep=args.sep)

    if args.x is None or args.y is None:
        x, y = detect_two_categoricals(df)
        print(f"[auto] selected columns: x='{x}', y='{y}'")
    else:
        x, y = args.x, args.y

    ct = build_crosstab(df, x, y)
    print(f"Contingency table shape: {ct.shape}")
    ct.to_csv(out_dir / "contingency_table.csv")

    Z = zscore_df(ct)
    Z.to_csv(out_dir / "standardized_table.csv")

    pval = bartlett_pvalue(Z)
    with open(out_dir / "bartlett.txt", "w", encoding="utf-8") as f:
        f.write(f"Bartlett p-value: {pval:.6g}\n")
    print(f"Bartlett p-value: {pval:.6g}")

    ev = eigenvalues_from_data(Z)
    np.savetxt(out_dir / "eigenvalues.csv", ev, delimiter=",")
    plot_scree(ev, out_dir / "scree_plot.png")

    n_keep = choose_n_factors(ev, ct.shape[0], ct.shape[1])
    print(f"Keeping {n_keep} factors (rule ev≥1, capped by min(cols-1, rows-1)).")

    rotations = [
        ("FA - No rotation", None),
        ("FA - Varimax", "varimax"),
        ("FA - Quartimax", "quartimax"),
    ]

    for title, rot in rotations:
        fa = fit_factors(Z, n_keep, rotation=rot)
        # Components/loadings plot + row scores in the same plane
        safe_title = title.replace(" ", "_").replace("-", "_").lower()
        plot_factor_maps(
            Z,
            fa,
            ct_cols=list(ct.columns),
            ct_rows=list(ct.index),
            title=f"AFC — {title}",
            out_path=out_dir / f"afc_map_{safe_title}.png",
        )

    print(f"Done. Outputs in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
