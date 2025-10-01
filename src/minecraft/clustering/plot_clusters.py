#!/usr/bin/env python3
"""
Plot clusters of Minecraft blocks
---------------------------------

Reads the clustered data CSV and plots a 2D scatter of two chosen features,
colored by cluster.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt

import kmeans

from const import PathCsvWithClusters, PathPngScatter


def parse_args(columns):
    p = argparse.ArgumentParser(description="Scatter plot of clustered Minecraft blocks")
    p.add_argument("x", help="Feature for X axis", choices=columns)
    p.add_argument("y", help="Feature for Y axis", choices=columns)
    return p.parse_args()


def main():
    if not PathCsvWithClusters.exists():
        kmeans.kmeans(kmeans.Config())

    df = pd.read_csv(PathCsvWithClusters, sep=";")
    args = parse_args(df.columns)

    fig, ax = plt.subplots()
    clusters = df["cluster"].unique()
    for cl in sorted(clusters):
        sub = df[df["cluster"] == cl]
        ax.scatter(
            sub[args.x],
            sub[args.y],
            label=f"Cluster {cl}",
        )

    ax.set_xlabel(args.x)
    ax.set_ylabel(args.y)
    ax.set_title(f"Clusters by {args.x} vs {args.y}")
    fig.legend()
    fig.savefig(PathPngScatter)
    print(f"[INFO] Saved scatter plot to {PathPngScatter}")


if __name__ == "__main__":
    main()
