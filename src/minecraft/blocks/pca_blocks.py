#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# ---------- Config ----------
DEFAULT_PATHS = [
    Path(sys.argv[1]) if len(sys.argv) > 1 else None,
    Path("/mnt/data/blocklist_clean.json"),  # uploaded file
    Path("../../../datasets/minecraft/blocks/blocklist_clean.json"),
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

# ---------- Helpers ----------
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

def resolve_existing_path(candidates: list[Path | None]) -> Path:
    for p in candidates:
        if p and p.exists():
            return p
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

def standardize_zscore(X: pd.DataFrame) -> pd.DataFrame:
    """
    TD standardisation: subtract mean, divide by std (z-score). (X - mean) / std
    This mirrors the TD cell exactly.  :contentReference[oaicite:6]{index=6}
    """
    X = X.copy()
    temp = X.sub(X.mean())
    X_scaled = temp.div(X.std(ddof=1))
    X_scaled = X_scaled.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return X_scaled

def biplot_from_pca(pca: PCA, feature_names: list[str], components: tuple[int, int]=(0,1),
                    circle: bool=True, title="Biplot (variables & individus, 2 premières composantes)"):
    """
    Plot variable directions (loadings) in the PC1-PC2 plane.
    We use pca.components_.T (unit-length in standardized PCA), which fits the TD approach.
    Optional: draw correlation circle of radius 1. :contentReference[oaicite:7]{index=7}
    """
    loadings = pca.components_.T[:, [components[0], components[1]]]
    fig, ax = plt.subplots(figsize=(7, 6))

    if circle:
        unit_circle = plt.Circle((0, 0), 1.0, color="grey", fill=False, linestyle="--", alpha=0.6)
        ax.add_patch(unit_circle)

    for i, name in enumerate(feature_names):
        ax.arrow(0, 0, loadings[i, 0], loadings[i, 1],
                 head_width=0.03, length_includes_head=True, alpha=0.9)
        ax.text(loadings[i, 0]*1.08, loadings[i, 1]*1.08, name,
                ha="center", va="center", fontsize=9)

    lim = 1.1 * float(np.max(np.abs(loadings)))
    lim = max(lim, 1.05)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    ax.axhline(0, linewidth=0.6)
    ax.axvline(0, linewidth=0.6)
    ax.set_xlabel("Dim1")
    ax.set_ylabel("Dim2")
    ax.set_title(title)
    fig.tight_layout()
    return fig, ax

# ---------- Main ----------
def main():
    path = resolve_existing_path(DEFAULT_PATHS)
    print(f"Loading dataset: {path}")

    df, cat_col = load_dataset(path)
    X = df[QUANT_COLS].copy()
    feature_names = QUANT_COLS

    X_scaled = standardize_zscore(X)

    n_components = min(len(feature_names), X_scaled.shape[1])
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X_scaled)

    explained_var = pca.explained_variance_
    explained_ratio = pca.explained_variance_ratio_
    cum_ratio = np.cumsum(explained_ratio)

    eig = pd.DataFrame({
        "Dimension": [f"Dim{x+1}" for x in range(n_components)],
        "Valeur propre": explained_var,
        "% variance expliquée": np.round(explained_ratio * 100, 2),
        "% variance expliquée cumulée": np.round(cum_ratio * 100, 2),
    })
    print("\n=== Tableau des valeurs propres ===")
    print(eig.to_string(index=False))

    out_dir = Path("pca_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    eig_path = out_dir / "pca_valeurs_propres.csv"
    eig.to_csv(eig_path, index=False)
    print(f"\nSaved eigenvalues table -> {eig_path}")

    plt.figure(figsize=(7, 4))
    x_idx = np.arange(n_components)
    labels = [f"Dim{x+1}" for x in x_idx]
    plt.bar(labels, explained_ratio)
    plt.ylabel("% variance expliquée")
    plt.xlabel("Dimensions ACP")
    plt.title("Variance expliquée par composante")
    plt.tight_layout()
    bar_path = out_dir / "pca_variance_barchart.png"
    plt.savefig(bar_path, dpi=160)
    print(f"Saved variance bar chart -> {bar_path}")

    fig_vars, _ = biplot_from_pca(pca, feature_names, components=(0,1), circle=True,
                                  title="ACP — Graphique des variables (cercle des corrélations)")
    biplot_path = out_dir / "pca_biplot_variables.png"
    fig_vars.savefig(biplot_path, dpi=160)
    print(f"Saved variables biplot -> {biplot_path}")

    pca_df = pd.DataFrame({
        "Dim1": scores[:, 0],
        "Dim2": scores[:, 1],
        cat_col: df[cat_col].values,
        "block": df.get("block", pd.Series([None]*len(df))).values,
    })

    plt.figure(figsize=(7, 6))
    unique_cats = pca_df[cat_col].dropna().astype(str).unique().tolist()
    unique_cats.sort()
    cmap = plt.get_cmap("Dark2")
    colors_map = {c: cmap(i % cmap.N) for i, c in enumerate(unique_cats)}

    for c in unique_cats:
        sub = pca_df[pca_df[cat_col] == c]
        plt.scatter(sub["Dim1"], sub["Dim2"], s=16, alpha=0.85, label=c, c=[colors_map[c]])

    plt.xlabel("Dim1 (PC1)")
    plt.ylabel("Dim2 (PC2)")
    plt.title(f"ACP — Graphique des individus (couleur: {cat_col})")
    plt.legend(title=cat_col, frameon=False, loc="best", fontsize=8)
    plt.tight_layout()
    ind_path = out_dir / "pca_individus.png"
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
