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

import argparse
from dataclasses import dataclass
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram

import importdata

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from const import PathCsvClusterProfiles, PathCsvClean, PathCsvWithClusters, PathPlotDendogram, PathPlotKdiag

type MatrixLike = np.ndarray | pd.DataFrame

@dataclass
class Config:
    k: int = 7
    random_state: int = 42

def parse_args():
    p = argparse.ArgumentParser(description="K-means clustering for Minecraft blocks.")
    p.add_argument("--k", default=7, type=int, help="Number of clusters (int) or 'auto' to search (default: auto)")
    p.add_argument("--random_state", type=int, default=42, help="Random seed (default: 42)")
    return Config(**vars(p.parse_args()))

def to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="raise")
    return df

def load_data(csv_path: Path):
    # Expect semicolon delimiter based on provided snippet
    df = pd.read_csv(csv_path, sep=";", dtype=str, keep_default_na=False)
    # Strip whitespace from column names and values
    df.columns = [c.strip() for c in df.columns]
    return df.block, to_numeric(df.drop(columns=["block"]))

def plot_elbow(Xstd: MatrixLike, cfg: Config):
    """
    Plots the elbow method for k-means clustering.
    """
    wcss = []  # within-cluster sum of squares
    kmin = 2
    kmax = 12
    for k in range(kmin, kmax + 1):
        model = KMeans(n_clusters=k, random_state=cfg.random_state, n_init="auto")
        model.fit(Xstd)
        wcss.append(model.inertia_)  # inertia_ is just WCSS

    plt.figure(figsize=(7, 5))
    plt.plot(range(kmin, kmax + 1), wcss, marker='o')
    plt.xticks(range(kmin, kmax + 1))
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Within-Cluster Sum of Squares (WCSS)")
    plt.title("Elbow Method for Optimal k")
    plt.grid(True)
    plt.show()

def create_model(Xstd: MatrixLike, cfg: Config):
    if not PathCsvClean.exists():
        print(f"[ERROR] CSV not found: {PathCsvClean}", file=sys.stderr)
        sys.exit(2)

    # Fit final model
    model = KMeans(n_clusters=cfg.k, n_init=10, random_state=cfg.random_state)
    model.fit(Xstd)
    return model
    
def gen_csv_with_cluster_profiles(X: pd.DataFrame, model: KMeans, labels, scaler: StandardScaler):
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

def kmeans(cfg: Config):
    print('Executing kmeans...')
    if not PathCsvClean.exists():
        importdata.importdata()
    blocks_names, X = load_data(PathCsvClean)

    scaler = StandardScaler()
    Xstd = scaler.fit_transform(X.values)

    model = create_model(Xstd, cfg)

    labels = model.predict(Xstd)

    XwithCluters = X.copy()
    XwithCluters['cluster'] = labels
    XwithCluters['block'] = blocks_names
    XwithCluters.to_csv(PathCsvWithClusters, index=False, sep=";")
    print(f"[INFO] Wrote {PathCsvWithClusters}")

    profiles = gen_csv_with_cluster_profiles(X, model, labels, scaler)
    profiles.to_csv(PathCsvClusterProfiles, index=False, sep=";")
    print(f"[INFO] Wrote {PathCsvClusterProfiles}")

    hierarchical_clustering(Xstd, cfg)


def hierarchical_clustering(X: MatrixLike, cfg: Config):
    model = AgglomerativeClustering(distance_threshold=0, n_clusters=None)
    model.fit(X)
    plot_dendrogram(model, truncate_mode="level", p=4)
    plt.xlabel("Nombre de points dans la classe (ou index sans parenthèses).")
    plt.savefig(PathPlotDendogram)
    print(f"[INFO] Wrote {PathPlotDendogram}")
    
def plot_dendrogram(model, **kwargs):
    counts = np.zeros(model. children_ .shape[0])
    n_samples = len(model. labels_)
    for i, merge in enumerate(model. children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1
            else:
                current_count += counts[child_idx-n_samples]
        counts[i] = current_count
    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)
    dendrogram(linkage_matrix, **kwargs)

if __name__=='__main__':
    kmeans(parse_args())
