"""
Read data with clusters and print blocks in separate lists per cluster
"""

import pandas as pd

import kmeans
from const import PathCsvWithClusters

def main(df: pd.DataFrame):
    for cl in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == cl].block
        print('Cluster', cl + 1, f'({len(sub)} items, {len(sub)/len(df):.2%})')
        sep = '\n- '
        print(sep + sep.join(sorted(sub)) + '\n')

if __name__ == '__main__':
    if not PathCsvWithClusters.exists():
        kmeans.kmeans(kmeans.Config())
    df = pd.read_csv(PathCsvWithClusters, sep=";")
    main(df)