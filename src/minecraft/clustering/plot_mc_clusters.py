#!/usr/bin/env python3
"""
Plot clusters of Minecraft blocks
---------------------------------

Reads the clustered data CSV and plots a 2D scatter of two chosen features,
colored by cluster.

Usage:
  python plot_clusters.py --x blast_resistance --y luminance
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt

from const import PathCsvWithClusters, PathPngScatter


def parse_args():
    p = argparse.ArgumentParser(description="Scatter plot of clustered Minecraft blocks")
    p.add_argument("x", help="Feature for X axis")
    p.add_argument("y", help="Feature for Y axis")
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(PathCsvWithClusters, sep=";")

    if args.x not in df.columns or args.y not in df.columns:
        raise ValueError(f"Columns {args.x} and/or {args.y} not found in {PathCsvWithClusters}")

    plt.figure(figsize=(8, 6))
    clusters = df["cluster"].unique()
    for cl in sorted(clusters):
        sub = df[df["cluster"] == cl]
        plt.scatter(
            sub[args.x],
            sub[args.y],
            label=f"Cluster {cl}",
            alpha=0.7
        )

    plt.xlabel(args.x)
    plt.ylabel(args.y)
    plt.title(f"Clusters by {args.x} vs {args.y}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PathPngScatter, dpi=150)
    print(f"[INFO] Saved scatter plot to {PathPngScatter}")


if __name__ == "__main__":
    main()
