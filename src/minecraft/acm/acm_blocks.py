#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from mca import MCA as MCA_mca
    HAS_MCA = True
except Exception:
    MCA_mca = None
    HAS_MCA = False

try:
    import prince
    HAS_PRINCE = True
except Exception:
    prince = None
    HAS_PRINCE = False

CATEGORICAL_CANDIDATES = ("conductive", "full_cube", "spawnable", "movable")

def _resolve_json_path(user_path: Path) -> Path:
    tried: list[Path] = []
    if user_path.is_absolute() and user_path.is_file():
        return user_path
    if user_path.is_file():
        return user_path.resolve()
    tried.append((Path.cwd() / user_path).resolve())
    here = Path(__file__).resolve().parent
    candidate = (here / user_path).resolve()
    if candidate.is_file():
        return candidate
    tried.append(candidate)
    for up in [here, *here.parents[:4]]:
        cand = (up / user_path).resolve()
        if cand.is_file():
            return cand
        tried.append(cand)
    repo_root = os.environ.get("PROJECT_ROOT")
    if repo_root:
        cand = (Path(repo_root).resolve() / user_path).resolve()
        if cand.is_file():
            return cand
        tried.append(cand)
    msg = ["Fichier JSON introuvable. Chemins testés :"] + [f" - {p}" for p in tried]
    raise FileNotFoundError("\n".join(msg))

def load_blocks_json(path: Path) -> pd.DataFrame:
    path = _resolve_json_path(path)
    df = pd.read_json(path)
    df.columns = [c.strip() for c in df.columns]
    return df

def choose_categorical(df: pd.DataFrame) -> list[str]:
    chosen = [c for c in CATEGORICAL_CANDIDATES if c in df.columns]
    if not chosen:
        chosen = [c for c in df.columns if (df[c].dtype == "object" or str(df[c].dtype) == "category") and c.lower() not in {"block", "id", "name"}]
    return chosen

def to_disjunctive(df_cat: pd.DataFrame) -> pd.DataFrame:
    for c in df_cat.columns:
        if df_cat[c].dtype == bool:
            df_cat[c] = df_cat[c].map({True: "Yes", False: "No"})
    return pd.get_dummies(df_cat, drop_first=False)

def fit_mca_with_mca(dc: pd.DataFrame, n_components: int = 2):
    model = MCA_mca(dc, benzecri=False)
    def _to_df(arr, index, prefix):
        arr = np.asarray(arr)
        cols = [f"{prefix}1", f"{prefix}2"] if arr.shape[1] >= 2 else [f"{prefix}1"]
        return pd.DataFrame(arr[:, :2], index=index, columns=cols)
    eigenvalues = getattr(model, "L", None)
    explained = None
    if eigenvalues is not None:
        lam = np.asarray(eigenvalues, dtype=float).ravel()
        if lam.sum() > 0:
            explained = lam / lam.sum()
    if hasattr(model, "fs_r"):
        row_coords = _to_df(model.fs_r(), index=dc.index, prefix="Dim")
    else:
        row_coords = pd.DataFrame(index=dc.index, columns=["Dim1", "Dim2"])
    if hasattr(model, "fs_c"):
        col_coords = _to_df(model.fs_c(), index=dc.columns, prefix="Dim")
    else:
        col_coords = pd.DataFrame(index=dc.columns, columns=["Dim1", "Dim2"])
    return model, eigenvalues, explained, row_coords, col_coords

def fit_mca_with_prince(dc: pd.DataFrame, n_components: int = 2):
    model = prince.MCA(n_components=max(2, n_components), random_state=42).fit(dc)
    explained = np.array(model.explained_inertia_)
    total_inertia = getattr(model, "total_inertia_", None)
    eigenvalues = explained * total_inertia if total_inertia is not None else explained
    row_coords = model.row_coordinates(dc).iloc[:, :2].rename(columns={0: "Dim1", 1: "Dim2"})
    col_coords = model.column_coordinates(dc).iloc[:, :2].rename(columns={0: "Dim1", 1: "Dim2"})
    return model, eigenvalues, explained, row_coords, col_coords

def _make_outdir() -> Path:
    here = Path(__file__).resolve().parent
    out = here / "acm_outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out

def run_acm(json_path: Path, max_labels_modalities: int = 50, sample_labels: int = 0) -> None:
    outdir = _make_outdir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    df = load_blocks_json(json_path)
    cat_cols = choose_categorical(df)
    if not cat_cols:
        raise ValueError("Aucune variable qualitative détectée. Ajoute p.ex. 'conductive', 'full_cube', 'spawnable', 'movable'.")
    before = len(df)
    x = df[cat_cols].copy().dropna(axis=0, how="any")
    after = len(x)
    dc = to_disjunctive(x)
    dc = dc.loc[:, (dc != 0).any(axis=0)]
    labels = df.loc[x.index, "block"].astype(str) if "block" in df.columns else pd.Index(x.index.astype(str))
    if HAS_MCA:
        _, eigenvalues, explained, row_coords, col_coords = fit_mca_with_mca(dc)
        backend = "mca"
    elif HAS_PRINCE:
        _, eigenvalues, explained, row_coords, col_coords = fit_mca_with_prince(dc)
        backend = "prince"
    else:
        raise RuntimeError("Ni 'mca' ni 'prince' n'est installé. Installe: pip install mca prince")
    if len(row_coords) == len(labels):
        row_coords.index = labels.values
    if eigenvalues is not None and explained is not None:
        k = min(len(eigenvalues), 10)
        plt.figure()
        plt.plot(range(1, k + 1), np.asarray(eigenvalues)[:k], marker="o")
        plt.title("Scree plot (valeurs propres / inertie)")
        plt.xlabel("Dimensions")
        plt.ylabel("Valeur propre (ou inertie)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(outdir / f"{stamp}_scree.png", dpi=150, bbox_inches="tight")
        plt.close()
    plt.figure()
    plt.scatter(row_coords["Dim1"], row_coords["Dim2"], alpha=0.4, s=10)
    plt.axhline(0); plt.axvline(0)
    plt.title("ACM — Plan factoriel des individus (Dim1 × Dim2)")
    plt.xlabel("Dim1"); plt.ylabel("Dim2")
    if 0 < sample_labels < len(row_coords):
        idx = np.random.choice(len(row_coords), size=sample_labels, replace=False)
        for i in idx:
            xi, yi = row_coords.iloc[i][["Dim1", "Dim2"]]
            plt.text(xi, yi, str(row_coords.index[i]), fontsize=7)
    plt.tight_layout()
    plt.savefig(outdir / f"{stamp}_individuals.png", dpi=150, bbox_inches="tight")
    plt.close()
    plt.figure()
    plt.scatter(col_coords["Dim1"], col_coords["Dim2"])
    plt.axhline(0); plt.axvline(0)
    plt.title("ACM — Modalités (Dim1 × Dim2)")
    plt.xlabel("Dim1"); plt.ylabel("Dim2")
    to_label = min(max_labels_modalities, col_coords.shape[0])
    for name, (x_, y_) in col_coords.iloc[:to_label][["Dim1", "Dim2"]].iterrows():
        plt.text(x_, y_, name, fontsize=7)
    plt.tight_layout()
    plt.savefig(outdir / f"{stamp}_modalities.png", dpi=150, bbox_inches="tight")
    plt.close()
    row_coords.to_csv(outdir / f"{stamp}_row_coords.csv")
    col_coords.to_csv(outdir / f"{stamp}_col_coords.csv")
    dc.to_csv(outdir / f"{stamp}_disjunctive.csv")
    if eigenvalues is not None and explained is not None:
        cum = np.cumsum(explained)
        eig_df = pd.DataFrame({
            "eigenvalue": np.asarray(eigenvalues).ravel(),
            "explained_ratio": np.asarray(explained).ravel(),
            "cumulative_ratio": cum.ravel()
        })
        eig_df.to_csv(outdir / f"{stamp}_eigenvalues.csv", index=False)
    report = [
        f"Input: {json_path}",
        f"Backend: {backend}",
        f"Rows before/after NA drop: {before}/{after}",
        f"Qualitative variables: {', '.join(cat_cols)}",
        f"Disjunctive shape: {dc.shape[0]} x {dc.shape[1]}",
    ]
    if eigenvalues is not None and explained is not None:
        top = [f"Dim{i+1}: {explained[i]:.3f}" for i in range(min(5, len(explained)))]
        report.append("Explained ratios (top): " + ", ".join(top))
    (outdir / f"{stamp}_acm_report.txt").write_text("\n".join(report), encoding="utf-8")

def main() -> int:
    try:
        parser = argparse.ArgumentParser(description="ACM sur le dataset Minecraft (qualitatif).")
        default_rel = Path("../../../datasets/minecraft/blocks/blocklist_clean.json")
        parser.add_argument("--path", type=Path, default=default_rel, help="Chemin vers le JSON des blocs.")
        parser.add_argument("--labels-modalites", type=int, default=50, help="Nb max de libellés de modalités à afficher.")
        parser.add_argument("--labels-individus", type=int, default=0, help="Nb d’individus à annoter (0 = aucun).")
        args = parser.parse_args()
        run_acm(args.path, max_labels_modalities=args.labels_modalites, sample_labels=args.labels_individus)
        return 0
    except Exception as e:
        outdir = _make_outdir()
        (outdir / "acm_error.txt").write_text(str(e), encoding="utf-8")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
