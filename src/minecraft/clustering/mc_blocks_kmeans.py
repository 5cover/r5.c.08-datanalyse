#!/usr/bin/env python3
"""
Minecraft Blocks Clustering (K-means)
------------------------------------

Reads a semicolon-delimited CSV (e.g. blocklist_clean.csv), performs
ordinal encoding for qualitative-ordinal variables, converts `spawnable`
to a quantitative scale, scales features, and runs k-means clustering.

Outputs:
- with_clusters.csv  (original data + cluster label)
- cluster_profiles.csv (cluster-wise feature averages)
- kdiag.png (optional: inertia/silhouette plots if --plots)

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

from const import PathCsvClusterProfiles, PathCsvClean, PathCsvWithClusters, PathPlotKdiag


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="K-means clustering for Minecraft blocks.")
    p.add_argument("--k", default="auto", help="Number of clusters (int) or 'auto' to search (default: auto)")
    p.add_argument("--kmin", type=int, default=2, help="Min k when --k=auto (default: 2)")
    p.add_argument("--kmax", type=int, default=12, help="Max k when --k=auto (default: 12)")
    p.add_argument("--plots", action="store_true", help="Save inertia/silhouette plots to <input>_kdiag.png")
    p.add_argument("--random_state", type=int, default=42, help="Random seed (default: 42)")
    return p.parse_args()

def to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="raise")
    return df

def load_data(csv_path: Path) -> pd.DataFrame:
    # Expect semicolon delimiter based on provided snippet
    df = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False)
    # Strip whitespace from column names and values
    df.columns = [c.strip() for c in df.columns]
    df = df.drop(columns=["block"])
    return to_numeric(df)

def choose_k_auto(Xs: pd.DataFrame, kmin: int, kmax: int, random_state: int) -> tuple[int, pd.DataFrame]:
    rows = []
    for k in range(kmin, min(kmax, len(Xs) - 1) + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = model.fit_predict(Xs)
        inertia = model.inertia_
        sil = np.nan
        if k > 1 and len(set(labels)) > 1:
            sil = silhouette_score(Xs, labels)
        rows.append({"k": k, "inertia": inertia, "silhouette": sil})
    diag = pd.DataFrame(rows)
    # Pick k with best silhouette; fallback to lowest inertia elbow-ish (min inertia)
    diag_nonan = diag.dropna(subset=["silhouette"])
    if not diag_nonan.empty:
        best_row = diag_nonan.sort_values("silhouette", ascending=False).iloc[0]
    else:
        best_row = diag.sort_values("inertia", ascending=True).iloc[0]
    return int(best_row["k"]), diag

def decide_k(Xs, args):
    # Decide k
    if args.k == "auto":
        best_k, diag = choose_k_auto(Xs, args.kmin, args.kmax, args.random_state)
        print(f"[INFO] Auto-selected k = {best_k}")
    else:
        try:
            best_k = int(args.k)
        except ValueError:
            print("[ERROR] --k must be an integer or 'auto'", file=sys.stderr)
            sys.exit(2)
    return best_k

def create_model(X: pd.DataFrame, k: int):
    if not PathCsvClean.exists():
        print(f"[ERROR] CSV not found: {PathCsvClean}", file=sys.stderr)
        sys.exit(2)

    # Fit final model
    model = KMeans(n_clusters=k, n_init=10, random_state=args.random_state)
    model.fit(X)
    return model

def gen_csv_with_clusters(X: pd.DataFrame, model: KMeans, args):
    labels = model.predict(X)

    # Attach labels to original dataframe (keep original order)
    out_df = X.copy()
    out_df["cluster"] = labels

    
    return labels, out_df
    
def gen_csv_with_cluster_profiles(X: pd.DataFrame, model: KMeans, labels):
    # Profiles per cluster (means in original scale)
    centers_scaled = model.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)
    centers_df = pd.DataFrame()
    centers_df.insert(0, "cluster", range(len(centers)))

    # Aggregate means from numeric matrix X (already float)
    Xdf = X.copy()
    Xdf["cluster"] = labels
    agg = Xdf.groupby("cluster")[X.columns].mean().reset_index()

    profiles = centers_df.merge(agg, on="cluster", suffixes=("_center", "_mean"))

    return profiles

if __name__ == "__main__":
    args = parse_args()

    X = load_data(PathCsvClean)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X.values)
    k = decide_k(Xs, args)

    model = create_model(X, k)


    labels, out_df = gen_csv_with_clusters(X, model, args)

    out_df.to_csv(PathCsvWithClusters, index=False, sep=";")
    print(f"[INFO] Wrote {PathCsvWithClusters}")

    profiles = gen_csv_with_cluster_profiles(X, model, labels)
    profiles.to_csv(PathCsvClusterProfiles, index=False, sep=";")
    print(f"[INFO] Wrote {PathCsvClusterProfiles}")

