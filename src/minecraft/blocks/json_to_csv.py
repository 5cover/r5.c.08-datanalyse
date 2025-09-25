#!/usr/bin/python3

# Run from project root

import pandas as pd

with open("./datasets/minecraft/blocks/blocklist_clean.json", encoding="utf-8") as inputfile:
    df = pd.read_json(inputfile)

df.to_csv("./datasets/minecraft/blocks/blocklist_clean.csv", sep=";", encoding="utf-8", index=False)
