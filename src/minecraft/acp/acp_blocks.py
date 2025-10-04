#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

DEFAULT_RELATIVE_DATASET = Path("../../../datasets/minecraft/blocks/blocklist_clean.json")
QUANTITATIVE_COLUMNS = [
    "height_external",
    "width_external",
    "number_of_variants",
    "volume",
    "blast_resistance",
    "luminance",
]
CATEGORICAL_COLUMNS_CANDIDATES = ["conductive", "movable", "full_cube", "spawnable"]

def normalize_movable(value: Any) -> str:
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

def resolve_dataset_path(user_path: str | None, script_dir: Path) -> Path:
    candidates: list[Path] = []
    if user_path:
        up = Path(user_path)
        if up.is_absolute():
            candidates.append(up)
        else:
            candidates.extend([up, Path.cwd() / up, script_dir / up])
    candidates.extend([DEFAULT_RELATIVE_DATASET, Path.cwd() / DEFAULT_RELATIVE_DATASET, script_dir / DEFAULT_RELATIVE_DATASET])
    for path in candidates:
        try:
            if path.exists() and path.is_file():
                return path.resolve()
        except Exception:
            pass
    raise FileNotFoundError("blocklist_clean.json introuvable via --file ou chemin par défaut.")

def load_dataset(dataset_path: Path) -> tuple[pd.DataFrame, str]:
    df = pd.read_json(dataset_path)
    for col in QUANTITATIVE_COLUMNS + ["block"] + CATEGORICAL_COLUMNS_CANDIDATES:
        if col not in df.columns:
            df[col] = np.nan
    df["movable_cat"] = df["movable"].apply(normalize_movable)
    for col in QUANTITATIVE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=QUANTITATIVE_COLUMNS, how="all").copy()
    for col in QUANTITATIVE_COLUMNS:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    for cat_col in ["conductive", "movable_cat", "full_cube", "spawnable"]:
        if cat_col in df.columns and not df[cat_col].isna().all():
            df[cat_col] = df[cat_col].astype(str).str.strip().str.title()
            return df, cat_col
    df["category"] = "Unknown"
    return df, "category"

def zscore_standardize(df_numeric: pd.DataFrame) -> pd.DataFrame:
    centered = df_numeric.sub(df_numeric.mean())
    scaled = centered.div(df_numeric.std(ddof=1))
    return scaled.replace([np.inf, -np.inf], np.nan).fillna(0.0)

def save_variables_correlation_plot(pca_model: PCA, feature_names: list[str], output_path: Path):
    loadings = pca_model.components_.T[:, [0, 1]]
    fig, ax = plt.subplots(figsize=(7, 6))
    circle = plt.Circle((0, 0), 1.0, fill=False, linestyle="--", alpha=0.6)
    ax.add_patch(circle)
    for i, name in enumerate(feature_names):
        ax.arrow(0, 0, loadings[i, 0], loadings[i, 1], head_width=0.03, length_includes_head=True, alpha=0.9)
        ax.text(loadings[i, 0] * 1.08, loadings[i, 1] * 1.08, name, ha="center", va="center", fontsize=9)
    lim = max(1.05, 1.1 * float(np.max(np.abs(loadings))))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axhline(0, linewidth=0.6)
    ax.axvline(0, linewidth=0.6)
    ax.set_xlabel("Dim1")
    ax.set_ylabel("Dim2")
    ax.set_title("ACP — Graphique des variables (cercle des corrélations)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)

def save_combined_biplot(pca_model: PCA, pc_scores: np.ndarray, feature_names: list[str], output_path: Path, alpha: float = 0.5):
    s = pca_model.singular_values_[:2]
    row_coords = pc_scores[:, :2] @ np.diag(s**(alpha - 1.0))
    col_coords = pca_model.components_.T[:, :2] @ np.diag(s**(1.0 - alpha))
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(row_coords[:, 0], row_coords[:, 1], s=10, alpha=0.6)
    for i, name in enumerate(feature_names):
        ax.arrow(0, 0, col_coords[i, 0], col_coords[i, 1], head_width=0.03, length_includes_head=True, alpha=0.9)
        ax.text(col_coords[i, 0] * 1.07, col_coords[i, 1] * 1.07, name, ha="center", va="center", fontsize=9)
    lim = 1.1 * float(np.max(np.abs(np.vstack([row_coords, col_coords]))))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axhline(0, linewidth=0.6)
    ax.axvline(0, linewidth=0.6)
    ax.set_xlabel("Dim1")
    ax.set_ylabel("Dim2")
    ax.set_title("ACP — Biplot combiné (individus + variables)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)

def main():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="ACP sur le jeu de données Minecraft (centrée-réduite).")
    parser.add_argument("--file", "-f", dest="file", type=str, default=None, help="Chemin vers blocklist_clean.json")
    args = parser.parse_args()

    dataset_path = resolve_dataset_path(args.file, script_dir)
    print(f"Chargement du jeu de données: {dataset_path}")

    dataset_frame, category_column = load_dataset(dataset_path)
    numeric_matrix = dataset_frame[QUANTITATIVE_COLUMNS].copy()
    standardized_matrix = zscore_standardize(numeric_matrix)
    print("Standardisation z-score appliquée.")

    n_components = min(len(QUANTITATIVE_COLUMNS), standardized_matrix.shape[1])
    pca_model = PCA(n_components=n_components)
    principal_component_scores = pca_model.fit_transform(standardized_matrix)

    explained_variance = pca_model.explained_variance_
    explained_ratio = pca_model.explained_variance_ratio_
    cumulative_ratio = np.cumsum(explained_ratio)

    eigen_table = pd.DataFrame({
        "Dimension": [f"Dim{i+1}" for i in range(n_components)],
        "Valeur propre": explained_variance,
        "% variance expliquée": np.round(explained_ratio * 100, 2),
        "% variance expliquée cumulée": np.round(cumulative_ratio * 100, 2),
    })
    print("\n=== Tableau des valeurs propres ===")
    print(eigen_table.to_string(index=False))

    out_dir = script_dir / "acp_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    eigen_csv_path = out_dir / "acp_valeurs_propres.csv"
    eigen_table.to_csv(eigen_csv_path, index=False)

    plt.figure(figsize=(7, 4))
    labels = [f"Dim{i+1}" for i in range(n_components)]
    plt.bar(labels, explained_ratio)
    plt.ylabel("% variance expliquée")
    plt.xlabel("Dimensions ACP")
    plt.title("Variance expliquée par composante")
    plt.tight_layout()
    variance_chart_path = out_dir / "acp_variance_barchart.png"
    plt.savefig(variance_chart_path, dpi=160)

    variables_circle_path = out_dir / "acp_biplot_variables.png"
    save_variables_correlation_plot(pca_model, QUANTITATIVE_COLUMNS, variables_circle_path)

    combined_biplot_path = out_dir / "acp_biplot_combine.png"
    save_combined_biplot(pca_model, principal_component_scores, QUANTITATIVE_COLUMNS, combined_biplot_path, alpha=0.5)

    individuals_plot_frame = pd.DataFrame({
        "Dim1": principal_component_scores[:, 0],
        "Dim2": principal_component_scores[:, 1],
        category_column: dataset_frame[category_column].values,
        "block": dataset_frame.get("block", pd.Series([None] * len(dataset_frame))).values,
    })
    plt.figure(figsize=(7, 6))
    categories = individuals_plot_frame[category_column].dropna().astype(str).unique().tolist()
    categories.sort()
    cmap = plt.get_cmap("Dark2")
    color_map = {c: cmap(i % cmap.N) for i, c in enumerate(categories)}
    for c in categories:
        subset = individuals_plot_frame[individuals_plot_frame[category_column] == c]
        plt.scatter(subset["Dim1"], subset["Dim2"], s=16, alpha=0.85, label=c, c=[color_map[c]])
    plt.xlabel("Dim1 (PC1)")
    plt.ylabel("Dim2 (PC2)")
    plt.title(f"ACP — Graphique des individus (couleur: {category_column})")
    plt.legend(title=category_column, frameon=False, loc="best", fontsize=8)
    plt.tight_layout()
    individuals_path = out_dir / "acp_individus.png"
    plt.savefig(individuals_path, dpi=160)

    scores_csv_path = out_dir / "acp_scores.csv"
    loadings_csv_path = out_dir / "acp_loadings.csv"
    pd.DataFrame(
        principal_component_scores, columns=[f"Dim{i+1}" for i in range(n_components)]
    ).assign(block=dataset_frame["block"]).to_csv(scores_csv_path, index=False)
    pd.DataFrame(
        pca_model.components_.T, index=QUANTITATIVE_COLUMNS, columns=[f"Dim{i+1}" for i in range(n_components)]
    ).to_csv(loadings_csv_path)

    print("\nTerminé.")
    print(f"Sorties dans: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
