#!/usr/bin/env python3
"""
Minecraft Blocks Clustering (K-means)
------------------------------------

Reads a semicolon-delimited CSV (e.g. blocklist_clean.csv), performs
ordinal encoding for qualitative-ordinal variables, converts `spawnable`
to a quantitative scale, scales features, and runs k-means clustering.

Outputs:
- <input>_with_clusters.csv  (original data + cluster label)
- <input>_cluster_profiles.csv (cluster-wise feature averages)
- <input>_kdiag.png (optional: inertia/silhouette plots if --plots)

Usage:
  python mc_blocks_kmeans.py --csv blocklist_clean.csv --k auto --plots
  python mc_blocks_kmeans.py --csv blocklist_clean.csv --k 6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# sklearn (required)
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="K-means clustering for Minecraft blocks.")
    p.add_argument("--csv", required=True, help="Path to semicolon-delimited CSV (e.g. blocklist_clean.csv)")
    p.add_argument("--k", default="auto", help="Number of clusters (int) or 'auto' to search (default: auto)")
    p.add_argument("--kmin", type=int, default=2, help="Min k when --k=auto (default: 2)")
    p.add_argument("--kmax", type=int, default=12, help="Max k when --k=auto (default: 12)")
    p.add_argument("--plots", action="store_true", help="Save inertia/silhouette plots to <input>_kdiag.png")
    p.add_argument("--random_state", type=int, default=42, help="Random seed (default: 42)")
    return p.parse_args()


def casefold_map(d: dict[str, int]) -> dict[str, int]:
    return {k.casefold(): v for k, v in d.items()}


# Encodings
SPAWNABLE_MAP = casefold_map({
    "No": 0,
    "Fire-Immune Mobs Only": 1,
    "Ocelots and Parrots Only": 2,
    "Polar Bear Only": 3,
    "Maybe": 4,
    "Yes": 5,
})

CONDUCTIVE_MAP = casefold_map({
    "No": 0,
    "Maybe": 1,
    "Yes": 2,
})

FULL_CUBE_MAP = casefold_map({
    "No": 0,
    "Maybe": 1,
    "Yes": 2,
})

MOVABLE_MAP = casefold_map({
    "No": 0,
    "Breaks": 1,
    "Maybe": 2,
    "Yes": 3,
})


NUMERIC_FEATURES = [
    "number_of_variants",
    "height_external",
    "width_external",
    "volume",
    "blast_resistance",
    "luminance",
]

ORDINAL_FEATURES = [
    ("conductive", CONDUCTIVE_MAP),
    ("full_cube", FULL_CUBE_MAP),
    ("movable", MOVABLE_MAP),
]

QUANT_SPAWNABLE = "spawnable"  # to be transformed via SPAWNABLE_MAP


def load_data(csv_path: Path) -> pd.DataFrame:
    # Expect semicolon delimiter based on provided snippet
    df = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False)
    # Strip whitespace from column names and values
    df.columns = [c.strip() for c in df.columns]
    return df.map(lambda x: x.strip() if isinstance(x, str) else x)


def map_ordinal(series: pd.Series, mapping: dict[str, int], colname: str) -> pd.Series:
    # Casefold + strip for resilient matching
    norm = series.astype(str).str.strip().str.casefold()
    mapped = norm.map(mapping)
    # Report unknowns (excluding blanks/NA)
    mask_unknown = (~mapped.notna()) & (series.astype(str).str.len() > 0)
    if mask_unknown.any():
        unknown_vals = sorted(set(series[mask_unknown]))
        print(f"[WARN] Column '{colname}': unknown categories encountered -> {unknown_vals}", file=sys.stderr)
    return mapped.astype("float")  # float for imputation if needed


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            print(f"[WARN] Missing numeric column '{c}', filling with NaN", file=sys.stderr)
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    work = df.copy()

    # Drop the nominal name column if present
    if "block" in work.columns:
        work = work.drop(columns=["block"])

    # Numeric casts
    work = coerce_numeric(work, NUMERIC_FEATURES)

    # Ordinal encodings
    for col, mapping in ORDINAL_FEATURES:
        if col not in work.columns:
            print(f"[WARN] Missing ordinal column '{col}', creating NaNs", file=sys.stderr)
            work[col] = np.nan
        else:
            work[col] = map_ordinal(work[col], mapping, col)

    # Quantitative transformation of spawnable
    if QUANT_SPAWNABLE in work.columns:
        work[QUANT_SPAWNABLE] = map_ordinal(work[QUANT_SPAWNABLE], SPAWNABLE_MAP, QUANT_SPAWNABLE)
    else:
        print(f"[WARN] Missing column '{QUANT_SPAWNABLE}', creating NaNs", file=sys.stderr)
        work[QUANT_SPAWNABLE] = np.nan

    # Feature list in final order
    features = NUMERIC_FEATURES + [c for c, _ in ORDINAL_FEATURES] + [QUANT_SPAWNABLE]

    # Impute missing with median
    for c in features:
        if work[c].isna().any():
            med = work[c].median()
            work[c] = work[c].fillna(med)

    X = work[features].astype(float)
    return X, features


def choose_k_auto(X: np.ndarray, kmin: int, kmax: int, random_state: int) -> tuple[int, pd.DataFrame]:
    rows = []
    for k in range(kmin, min(kmax, len(X) - 1) + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = model.fit_predict(X)
        inertia = model.inertia_
        sil = np.nan
        if k > 1 and len(set(labels)) > 1:
            sil = silhouette_score(X, labels)
        rows.append({"k": k, "inertia": inertia, "silhouette": sil})
    diag = pd.DataFrame(rows)
    # Pick k with best silhouette; fallback to lowest inertia elbow-ish (min inertia)
    diag_nonan = diag.dropna(subset=["silhouette"])
    if not diag_nonan.empty:
        best_row = diag_nonan.sort_values("silhouette", ascending=False).iloc[0]
    else:
        best_row = diag.sort_values("inertia", ascending=True).iloc[0]
    return int(best_row["k"]), diag


def plot_diagnostics(diag: pd.DataFrame, out_png: Path) -> None:
    plt.figure()
    if "inertia" in diag:
        plt.plot(diag["k"], diag["inertia"], marker="o", label="Inertia")
    if "silhouette" in diag:
        plt.plot(diag["k"], diag["silhouette"], marker="o", label="Silhouette")
    plt.xlabel("k")
    plt.legend()
    plt.title("K diagnostics")
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()
    print(f"[INFO] Saved diagnostics plot to {out_png}")


def run():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    df = load_data(csv_path)

    X, features = prepare_features(df)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X.values)

    # Decide k
    if args.k == "auto":
        best_k, diag = choose_k_auto(Xs, args.kmin, args.kmax, args.random_state)
        print(f"[INFO] Auto-selected k = {best_k}")
    else:
        try:
            best_k = int(args.k)
            diag = None
        except ValueError:
            print("[ERROR] --k must be an integer or 'auto'", file=sys.stderr)
            sys.exit(2)

    # Fit final model
    model = KMeans(n_clusters=best_k, n_init=10, random_state=args.random_state)
    labels = model.fit_predict(Xs)

    # Attach labels to original dataframe (keep original order)
    out_df = df.copy()
    out_df["cluster"] = labels

    out_base = csv_path.with_suffix("")
    out_csv = out_base.with_name(out_base.name + "_with_clusters.csv")
    out_df.to_csv(out_csv, index=False, sep=";")
    print(f"[INFO] Wrote {out_csv}")

    # Profiles per cluster (means in original scale)
    centers_scaled = model.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)
    centers_df = pd.DataFrame(centers, columns=features)
    centers_df.insert(0, "cluster", range(best_k))

    # Aggregate means from data as well
    agg = (
        out_df.join(pd.DataFrame(X, columns=features))
        .groupby("cluster")[features]
        .mean()
        .reset_index()
    )
    profiles = centers_df.merge(agg, on="cluster", suffixes=("_center", "_mean"))

    out_prof = out_base.with_name(out_base.name + "_cluster_profiles.csv")
    profiles.to_csv(out_prof, index=False, sep=";")
    print(f"[INFO] Wrote {out_prof}")

    # Optionally plot diagnostics
    if args.k == "auto" and args.plots and diag is not None:
        out_png = out_base.with_name(out_base.name + "_kdiag.png")
        plot_diagnostics(diag, out_png)


if __name__ == "__main__":
    run()
