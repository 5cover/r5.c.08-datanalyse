#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scipy.stats import chi2_contingency

DEFAULT_INPUT = Path("../../../datasets/minecraft/blocks/blocklist_clean.json")
CATEGORICAL_CANDIDATES = ("conductive", "full_cube", "spawnable", "movable")

def read_any(input_path: Path, sep: Optional[str] = None) -> pd.DataFrame:
    ext = input_path.suffix.lower()
    if ext == ".json":
        return pd.read_json(input_path)
    if ext in {".csv", ".tsv", ".txt"}:
        if sep is not None:
            return pd.read_csv(input_path, sep=sep)
        for candidate in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(input_path, sep=candidate)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                pass
        return pd.read_csv(input_path)
    return pd.read_table(input_path)

def candidate_categoricals(df: pd.DataFrame) -> List[str]:
    return [c for c in CATEGORICAL_CANDIDATES if c in df.columns]

def build_contingency_table(df: pd.DataFrame, col_x: str, col_y: str) -> pd.DataFrame:
    x = df[col_x].astype(str)
    y = df[col_y].astype(str)
    ct = pd.crosstab(x, y)
    ct = ct.loc[(ct.sum(axis=1) > 0), (ct.sum(axis=0) > 0)]
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        raise ValueError("Degenerate contingency table (need ≥2 rows and ≥2 columns).")
    return ct

def zscore_and_prune(M: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    std = M.std(axis=0, ddof=1)
    keep = std > 0
    if keep.sum() < 1:
        raise ValueError("All columns are constant.")
    M2 = M.loc[:, keep]
    if M2.shape[1] == 1:
        Z = (M2 - M2.mean(axis=0)) / M2.std(axis=0, ddof=1)
        Z = Z.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return Z, list(M2.columns)
    Z = (M2 - M2.mean(axis=0)) / M2.std(axis=0, ddof=1)
    Z = Z.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return Z, list(M2.columns)

def chi2_pvalue(ct: pd.DataFrame) -> float:
    chi2, p, dof, exp = chi2_contingency(ct, correction=False)
    return float(p)

def eigenvalues_from_corr(Z: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    C = np.corrcoef(Z, rowvar=False)
    w, V = np.linalg.eigh(C)
    idx = np.argsort(w)[::-1]
    return w[idx], V[:, idx]

def choose_num_factors(ev: np.ndarray, n_rows: int, n_cols: int) -> int:
    n_max = max(1, min(n_cols - 1, n_rows - 1))
    n_keep = int(np.sum(ev >= 1.0))
    if n_keep <= 0:
        n_keep = 1
    return min(n_keep, n_max)

def pca_scores_and_loadings(Z: pd.DataFrame, V: np.ndarray, ev: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    V_k = V[:, :k]
    ev_k = ev[:k]
    L = V_k * np.sqrt(ev_k)
    S = Z.values @ V_k
    return L, S

def varimax(Phi: np.ndarray, gamma: float = 1.0, q: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, np.ndarray]:
    p, k = Phi.shape
    if k < 2:
        return Phi, np.eye(k)
    R = np.eye(k)
    d = 0.0
    for _ in range(q):
        Lambda = Phi @ R
        term = Lambda**3 - (gamma / p) * Lambda @ np.diag(np.sum(Lambda**2, axis=0))
        u, s, vt = np.linalg.svd(Phi.T @ term, full_matrices=False)
        R_new = u @ vt
        Lambda = Phi @ R_new
        d_new = s.sum()
        if d_new - d < tol:
            R = R_new
            break
        d = d_new
        R = R_new
    return Phi @ R, R

def quartimax(Phi: np.ndarray, q: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, np.ndarray]:
    return varimax(Phi, gamma=0.0, q=q, tol=tol)

def plot_scree(ev: np.ndarray, out_path: Path) -> None:
    plt.figure(figsize=(7, 4))
    xs = np.arange(1, len(ev) + 1)
    plt.scatter(xs, ev)
    plt.plot(xs, ev)
    plt.title("Scree Plot (valeurs propres)")
    plt.xlabel("Facteurs")
    plt.ylabel("Valeur propre")
    plt.grid(True, linewidth=0.5)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()

def plot_factor_map(loadings: np.ndarray, scores: np.ndarray, ct_cols: List[str], ct_rows: List[str], title: str, out_path: Path) -> None:
    x_idx = 0
    y_idx = 1 if loadings.shape[1] > 1 else 0
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(loadings[:, x_idx], loadings[:, y_idx], s=40, alpha=0.9, label="Variables (colonnes)")
    for xv, yv, name in zip(loadings[:, x_idx], loadings[:, y_idx], ct_cols):
        ax.text(xv + 0.02, yv + 0.02, str(name), ha="center", va="center", fontsize=8)
    ax.scatter(scores[:, x_idx], scores[:, y_idx], s=24, marker="^", alpha=0.8, label="Modalités (lignes)")
    for xr, yr, name in zip(scores[:, x_idx], scores[:, y_idx], ct_rows):
        ax.text(xr + 0.02, yr + 0.02, str(name), ha="center", va="center", fontsize=8)
    ax.axhline(0, linewidth=0.6, color="k")
    ax.axvline(0, linewidth=0.6, color="k")
    ax.set_xlabel("Facteur 1")
    ax.set_ylabel("Facteur 2")
    ax.set_title(title)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)

def auto_select_best_pair(df: pd.DataFrame) -> Tuple[str, str, float]:
    cands = candidate_categoricals(df)
    if len(cands) < 2:
        raise ValueError("Need at least two of the required categorical columns.")
    tested: List[Tuple[str, str, float]] = []
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            x, y = cands[i], cands[j]
            try:
                ct = build_contingency_table(df, x, y)
                p = chi2_pvalue(ct)
                if np.isfinite(p):
                    tested.append((x, y, p))
            except Exception:
                continue
    if not tested:
        raise ValueError("No valid categorical pair found.")
    tested.sort(key=lambda t: t[2])
    best_sig = [t for t in tested if t[2] < 0.05]
    if not best_sig:
        raise ValueError("No column pair yields chi-square p < 0.05. Aborting as requested.")
    return best_sig[0]

def main() -> None:
    ap = argparse.ArgumentParser(description="AFC (TD-style) headless on categorical pair with p<0.05.")
    ap.add_argument("--file", default=None, help="CSV/JSON path (default: ../../../datasets/minecraft/blocks/blocklist_clean.json)")
    ap.add_argument("--sep", default=None, help="CSV separator")
    ap.add_argument("--x", default=None, help="Column for rows (categorical)")
    ap.add_argument("--y", default=None, help="Column for cols (categorical)")
    ap.add_argument("--out", default="afc_outputs", help="Output directory")
    args = ap.parse_args()

    input_path = Path(args.file) if args.file else DEFAULT_INPUT
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_any(input_path, sep=args.sep)

    if args.x is None or args.y is None:
        col_x, col_y, p_auto = auto_select_best_pair(df)
        print(f"[auto] colonnes sélectionnées: x='{col_x}', y='{col_y}' (p={p_auto:.6g})")
        with open(output_dir / "auto_selection.txt", "w", encoding="utf-8") as f:
            f.write(f"x={col_x}\ny={col_y}\np_value={p_auto:.6g}\n")
    else:
        col_x, col_y = args.x, args.y

    ct = build_contingency_table(df, col_x, col_y)
    print(f"Table de contingence: {ct.shape[0]}x{ct.shape[1]}")
    ct.to_csv(output_dir / "contingency_table.csv", encoding="utf-8")

    Z, kept_cols = zscore_and_prune(ct)
    pd.DataFrame(Z, index=ct.index, columns=kept_cols).to_csv(output_dir / "standardized_table.csv", encoding="utf-8")

    p_chi2 = chi2_pvalue(ct)
    decision = "Variables dépendantes (AFC pertinente)" if p_chi2 < 0.05 else "Variables plutôt indépendantes"
    with open(output_dir / "independence_test.txt", "w", encoding="utf-8") as f:
        f.write(f"Chi-square p-value: {p_chi2:.6g}\nConclusion: {decision}\n")
    print(f"Chi-square p-value: {p_chi2:.6g} — {decision}")

    ev, V = eigenvalues_from_corr(Z)
    np.savetxt(output_dir / "eigenvalues.csv", ev, delimiter=",")
    plot_scree(ev, output_dir / "scree_plot.png")

    n_keep = choose_num_factors(ev, ct.shape[0], len(kept_cols))
    print(f"Facteurs retenus: {n_keep} (règle λ≥1, borné par min(lignes-1, colonnes-1)).")
    L, S = pca_scores_and_loadings(Z, V, ev, n_keep)

    L_none = L
    S_none = S
    L_var, R_var = varimax(L)
    L_qua, R_qua = quartimax(L)
    S_var = S @ R_var
    S_qua = S @ R_qua

    plot_factor_map(L_none, S_none, kept_cols, list(ct.index), "AFC — PCA (aucune rotation)", output_dir / "factor_map_pca_aucune_rotation.png")
    plot_factor_map(L_var, S_var, kept_cols, list(ct.index), "AFC — PCA (varimax)", output_dir / "factor_map_pca_varimax.png")
    plot_factor_map(L_qua, S_qua, kept_cols, list(ct.index), "AFC — PCA (quartimax)", output_dir / "factor_map_pca_quartimax.png")

    print(f"Terminé. Dossier des sorties: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
