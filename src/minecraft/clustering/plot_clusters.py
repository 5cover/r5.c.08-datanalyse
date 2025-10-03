#!/usr/bin/env python3
"""
Plot clusters of Minecraft blocks
---------------------------------

Reads the clustered data CSV and plots a 2D scatter of two chosen features,
colored by cluster.
"""

import argparse
import itertools
from matplotlib.pylab import f
import pandas as pd
import matplotlib.pyplot as plt

import kmeans

from const import PathCsvWithClusters, PathPngScatter


def parse_args(columns):
    p = argparse.ArgumentParser(description="Scatter plot of clustered Minecraft blocks")
    p.add_argument("x", help="Feature for X axis", choices=columns)
    p.add_argument("y", help="Feature for Y axis", choices=columns)
    return p.parse_args()


def main(df: pd.DataFrame, feature_x: str, feature_y: str):
    fig, ax = plt.subplots()
    clusters = df["cluster"].unique()
    for cl in sorted(clusters):
        sub = df[df["cluster"] == cl]
        counts = sub.groupby([feature_x, feature_y]).size().reset_index(name="count")
        ax.scatter(
            counts[feature_x],
            counts[feature_y],
            s=counts["count"] * 5,  # scale factor
            alpha=0.5,
            label=f"Cluster {cl}",
        )

    ax.set_xlabel(feature_x)
    ax.set_ylabel(feature_y)
    ax.set_title(f"Clusters in {feature_y} by {feature_x} (K = {len(clusters)})")
    path = PathPngScatter(feature_x, feature_y)
    fig.savefig(path)
    print(f"[INFO] Saved scatter plot to {path}")

def generate_all(df: pd.DataFrame):
    features=[col for col in df.columns if col != 'cluster']
    perms=list(itertools.permutations(features, 2))
    print(perms, len(perms))

if __name__ == "__main__":
    if not PathCsvWithClusters.exists():
        kmeans.kmeans(kmeans.Config())
    df = pd.read_csv(PathCsvWithClusters, sep=";")
    generate_all(df)
    #args = parse_args(df.columns)
    #main(df, args.x, args.y)
