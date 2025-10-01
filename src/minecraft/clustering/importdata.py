#!/usr/bin/env python3
"""
importdata.py
-------------

Lit un CSV de blocs Minecraft (CSV distant ou local),
encode les variables qualitatives, centre-réduit les variables numériques,
et écrit un fichier normalisé dans results/.
"""

from pathlib import Path
import pandas as pd
from sklearn.preprocessing import StandardScaler

from const import PathCsvClean

# Constantes
path_csv_raw = Path(__file__).parent.parent.parent.parent / "datasets" / "minecraft" / "blocks" / "blocklist_clean.csv"

# Encodages
MAP_CONDUCTIVE = {"No": 0, "Maybe": 1, "Yes": 2}
MAP_FULL_CUBE = {"No": 0, "Maybe": 1, "Yes": 2}
MAP_MOVABLE = {"No": 0, "Breaks": 1, "Maybe": 2, "Yes": 3}
MAP_SPAWNABLE = {
    "No": 0,
    "Fire-Immune Mobs Only": 1,
    "Ocelots and Parrots Only": 2,
    "Polar Bear Only": 3,
    "Maybe": 4,
    "Yes": 5,
}

NUMERIC_COLS = [
    "number_of_variants",
    "height_external",
    "width_external",
    "volume",
    "blast_resistance",
    "luminance",
]

QUALI_COLS = ["conductive", "full_cube", "movable", "spawnable"]

ALL_FEATURES = NUMERIC_COLS + QUALI_COLS


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    return df


def encode(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["conductive"] = df["conductive"].map(MAP_CONDUCTIVE)
    df["full_cube"] = df["full_cube"].map(MAP_FULL_CUBE)
    df["movable"] = df["movable"].map(MAP_MOVABLE)
    df["spawnable"] = df["spawnable"].map(MAP_SPAWNABLE)
    return df

if __name__ == "__main__":
    df = load_data(path_csv_raw)
    df_enc = encode(df)
    df_enc.to_csv(PathCsvClean, sep=";", index=False)
    print(f"[INFO] Fichier propre écrit dans {PathCsvClean}")
