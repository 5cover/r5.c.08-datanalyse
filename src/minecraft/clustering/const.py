# Encodings
from pathlib import Path


def casefold_map(d: dict[str, int]) -> dict[str, int]:
    return {k.casefold(): v for k, v in d.items()}


outdir = Path(__file__).parent / 'results'
outdir.mkdir(exist_ok=True)
PathCsvClean = outdir / 'clean.csv'
PathCsvClusterProfiles = outdir / 'cluster_profiles.csv'
PathPlotKdiag = outdir / 'kdiag.png'
PathCsvWithClusters = outdir / 'data_with_clusters.csv'
PathPlotCustersPca = outdir / "clusters_pca.png"
PathClusterSizes = outdir / "clusters_sizes.png"
PathPngScatter = outdir / "scatter.png"
