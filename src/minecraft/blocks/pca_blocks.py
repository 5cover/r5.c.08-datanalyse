#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


DEFAULT_PATH = Path("../../../datasets/minecraft/blocks/blocklist_clean.json")

# Quantitative and categorical fields expected in the dataset
QUANT_COLS = [
    "height_external",
    "width_external",
    "number_of_variants",
    "volume",
    "blast_resistance",
    "luminance",
]
CATEGORICAL_CANDIDATES = ["conductive", "movable", "full_cube", "spawnable"]


def normalize_movable(value: Any) -> str:
    """Normalize the 'movable' field which can be a string or an object.
    Returns a compact categorical label suitable for plotting.
    """
    if isinstance(value, dict):
        # If any case is 'Yes', mark as 'ConditionalYes'; else if all 'No', 'No'; else generic 'Conditional'
        vals = {str(v).strip().title() for v in value.values()}
        if "Yes" in vals:
            return "ConditionalYes"
        if vals == {"No"}:
            return "No"
        if "Breaks" in vals:
            return "ConditionalBreaks"
        return "Conditional"
    if value is None:
        return "Unknown"
    return str(value).strip().title()  # e.g., "Yes", "No", "Breaks"


def load_dataset(path: Path) -> pd.DataFrame:
    # pandas can read a JSON array of objects directly
    df = pd.read_json(path)
    # Ensure expected columns exist
    for c in QUANT_COLS + ["block"] + CATEGORICAL_CANDIDATES:
        if c not in df.columns:
            df[c] = np.nan

    # Normalize 'movable' to a categorical string column
    df["movable_cat"] = df["movable"].apply(normalize_movable)

    # Coerce quantitative columns to numeric (errors -> NaN)
    for c in QUANT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Basic cleaning: drop rows that have all NaNs in QUANT_COLS
    df = df.dropna(subset=QUANT_COLS, how="all").copy()

    # Optional: fill remaining NaNs with column medians (safer than 0 for PCA)
    for c in QUANT_COLS:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].median())

    # Prepare a single categorical column to color points (choose 'conductive' by default, fallback to others)
    cat_col = "conductive"
    if df[cat_col].isna().all():
        for alt in ["movable_cat", "full_cube", "spawnable"]:
            if alt in df.columns and not df[alt].isna().all():
                cat_col = alt
                break
    # Normalize chosen categorical to strings
    df[cat_col] = df[cat_col].astype(str).str.strip().str.title()
    return df, cat_col


def biplot(scores: np.ndarray, coeff: np.ndarray, labels: list[str] | None = None):
    """Variables biplot for the first two principal components.
    - scores: (n_samples, 2) projected data
    - coeff:  (n_features, 2) loadings
    - labels: feature names
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    # Scatter of individuals (light markers)
    ax.scatter(scores[:, 0], scores[:, 1], s=10, alpha=0.6)

    # Draw arrows for variables
    for i in range(coeff.shape[0]):
        ax.arrow(0, 0, coeff[i, 0], coeff[i, 1], head_width=0.02, length_includes_head=True)
        if labels is not None:
            ax.text(coeff[i, 0] * 1.08, coeff[i, 1] * 1.08, labels[i], ha="center", va="center")

    lim = 1.1 * np.max(np.abs(coeff[:, :2]))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Biplot (variables & individuals, first 2 PCs)")
    ax.axhline(0, linewidth=0.5)
    ax.axvline(0, linewidth=0.5)
    fig.tight_layout()
    return fig, ax


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    if not path.exists():
        print(f"ERROR: dataset not found at: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading dataset: {path}")
    df, cat_col = load_dataset(path)

    X = df[QUANT_COLS].copy()
    feature_names = QUANT_COLS

    # Standardization (zero mean, unit variance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # PCA (keep all components up to number of features)
    n_components = min(6, X_scaled.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    scores = pca.fit_transform(X_scaled)  # (n_samples, n_components)

    # Eigenvalues summary table
    explained_var = pca.explained_variance_  # eigenvalues (lambda)
    explained_ratio = pca.explained_variance_ratio_
    cum_ratio = np.cumsum(explained_ratio)

    eig = pd.DataFrame({
        "Dimension": [f"Dim{x+1}" for x in range(n_components)],
        "Valeur propre": explained_var,
        "% valeur propre": np.round(explained_ratio * 100, 2),
        "% cum. val. prop.": np.round(cum_ratio * 100, 2),
    })
    print("\n=== Tableau des valeurs propres ===")
    print(eig.to_string(index=False))

    out_dir = Path("pca_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    eig_path = out_dir / "pca_eigenvalues.csv"
    eig.to_csv(eig_path, index=False)
    print(f"\nSaved eigenvalues table -> {eig_path}")

    # Bar chart of explained variance ratio
    plt.figure(figsize=(7, 4))
    x_idx = np.arange(n_components)
    plt.bar(x_idx, explained_ratio)
    plt.xticks(x_idx, [f"Dim{x+1}" for x in x_idx])
    plt.ylabel("Explained variance ratio")
    plt.title("Explained variance by component")
    plt.tight_layout()
    bar_path = out_dir / "pca_variance_bar.png"
    plt.savefig(bar_path, dpi=160)
    print(f"Saved variance bar chart -> {bar_path}")

    # Variables biplot using first two PCs
    coeff = pca.components_.T[:, :2]  # (n_features, 2)
    fig, ax = biplot(scores[:, :2], coeff, labels=feature_names)
    biplot_path = out_dir / "pca_biplot.png"
    fig.savefig(biplot_path, dpi=160)
    print(f"Saved biplot -> {biplot_path}")

    # Individuals scatter colored by a categorical column
    pca_df = pd.DataFrame({
        "Dim1": scores[:, 0],
        "Dim2": scores[:, 1],
        cat_col: df[cat_col].values,
        "block": df.get("block", pd.Series([None]*len(df))).values,
    })

    cmap = plt.get_cmap("Dark2")
    unique_cats = sorted(pca_df[cat_col].dropna().unique().tolist())
    cat_to_idx = {c: i for i, c in enumerate(unique_cats)}
    colors = [cmap(cat_to_idx.get(c, 0) % 8) for c in pca_df[cat_col]]

    plt.figure(figsize=(7, 6))
    plt.scatter(pca_df["Dim1"], pca_df["Dim2"], s=16, c=colors, alpha=0.8)
    plt.xlabel("Dimension 1 (PC1)")
    plt.ylabel("Dimension 2 (PC2)")
    plt.title(f"ACP — Graphique des individus (couleur: {cat_col})")
    # Simple legend
    for c, idx in cat_to_idx.items():
        plt.scatter([], [], label=c, marker="o")
    plt.legend(title=cat_col, frameon=False, loc="best", fontsize=8)
    plt.tight_layout()
    ind_path = out_dir / "pca_individuals.png"
    plt.savefig(ind_path, dpi=160)
    print(f"Saved individuals plot -> {ind_path}")

    print("\nDone.")
    print(f"Outputs in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
