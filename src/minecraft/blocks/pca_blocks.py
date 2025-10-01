#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

DEFAULT_PATHS = [
    Path("../../../datasets/minecraft/blocks/blocklist_clean.json"),    # your project tree
]

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
    """
    Normalize 'movable' which can be a string or an object (older data).
    Examples -> "Yes", "No", "Breaks", "Maybe", "ConditionalYes", etc.
    """
    if isinstance(value, dict):
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
    return str(value).strip().title()


def resolve_path(cli_arg: str | None) -> Path:
    if cli_arg:
        p = Path(cli_arg)
        if p.exists():
            return p
        print(f"WARNING: {p} not found; trying fallbacks...", file=sys.stderr)
    for cand in DEFAULT_PATHS:
        if cand.exists():
            return cand
    raise FileNotFoundError("blocklist_clean.json not found in known locations.")


def load_dataset(path: Path) -> tuple[pd.DataFrame, str]:
    df = pd.read_json(path)

    for c in QUANT_COLS + ["block"] + CATEGORICAL_CANDIDATES:
        if c not in df.columns:
            df[c] = np.nan

    df["movable_cat"] = df["movable"].apply(normalize_movable)

    for c in QUANT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=QUANT_COLS, how="all").copy()
    for c in QUANT_COLS:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].median())

    for cat_col in ["conductive", "movable_cat", "full_cube", "spawnable"]:
        if cat_col in df.columns and not df[cat_col].isna().all():
            df[cat_col] = df[cat_col].astype(str).str.strip().str.title()
            return df, cat_col

    df["category"] = "Unknown"
    return df, "category"


def biplot(scores: np.ndarray, coeff: np.ndarray, labels: list[str] | None = None):
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(scores[:, 0], scores[:, 1], s=10, alpha=0.6)
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
    path = resolve_path(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Loading dataset: {path}")

    df, cat_col = load_dataset(path)
    X = df[QUANT_COLS].copy()
    feature_names = QUANT_COLS

    # Standardization (zero mean, unit variance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # PCA
    n_components = min(len(QUANT_COLS), X_scaled.shape[1], 6)
    pca = PCA(n_components=n_components, random_state=42)
    scores = pca.fit_transform(X_scaled)

    # Eigenvalues summary table
    explained_var = pca.explained_variance_
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
    fig, _ = biplot(scores[:, :2], coeff, labels=feature_names)
    biplot_path = out_dir / "pca_biplot.png"
    fig.savefig(biplot_path, dpi=160)
    print(f"Saved biplot -> {biplot_path}")

    # Individuals scatter colored by categorical column
    pca_df = pd.DataFrame({
        "Dim1": scores[:, 0],
        "Dim2": scores[:, 1],
        cat_col: df[cat_col].values,
        "block": df.get("block", pd.Series([None]*len(df))).values,
    })

    plt.figure(figsize=(7, 6))
    unique_cats = sorted(pca_df[cat_col].dropna().unique().tolist())
    cat_to_idx = {c: i for i, c in enumerate(unique_cats)}
    colors = [cat_to_idx.get(c, 0) for c in pca_df[cat_col]]
    plt.scatter(pca_df["Dim1"], pca_df["Dim2"], s=16, c=colors, alpha=0.8)
    plt.xlabel("Dimension 1 (PC1)")
    plt.ylabel("Dimension 2 (PC2)")
    plt.title(f"ACP — Graphique des individus (couleur: {cat_col})")
    for c in unique_cats:
        plt.scatter([], [], label=c, marker="o")
    plt.legend(title=cat_col, frameon=False, loc="best", fontsize=8)
    plt.tight_layout()
    ind_path = out_dir / "pca_individuals.png"
    plt.savefig(ind_path, dpi=160)
    print(f"Saved individuals plot -> {ind_path}")

    pca_scores_path = out_dir / "pca_scores.csv"
    pca_loadings_path = out_dir / "pca_loadings.csv"
    pd.DataFrame(scores, columns=[f"Dim{i+1}" for i in range(n_components)]).assign(block=df["block"]).to_csv(pca_scores_path, index=False)
    pd.DataFrame(pca.components_.T, index=feature_names, columns=[f"Dim{i+1}" for i in range(n_components)]).to_csv(pca_loadings_path)
    print(f"Saved PCA scores -> {pca_scores_path}")
    print(f"Saved PCA loadings -> {pca_loadings_path}")

    print("\nDone.")
    print(f"Outputs in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
