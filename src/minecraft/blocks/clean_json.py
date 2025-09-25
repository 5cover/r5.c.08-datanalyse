import json
from math import isfinite

blocklist_path = "../../../datasets/minecraft/blocks/blocklist.json"

with open(blocklist_path, "r", encoding="utf-8") as f:
    blocks = json.load(f)

def safe_int(val):
    if isinstance(val, bool):  # avoid True -> 1
        return None
    if isinstance(val, (int, float)) and isfinite(val):
        return int(val)
    try:
        return int(str(val).strip().split()[0])
    except Exception:
        return None

def extract_numeric_values(x):
    vals = []
    if isinstance(x, dict):
        for v in x.values():
            vals.extend(extract_numeric_values(v))
    elif isinstance(x, (list, tuple)):
        for v in x:
            vals.extend(extract_numeric_values(v))
    else:
        n = safe_int(x)
        if n is not None:
            vals.append(n)
    return vals

def average_or_none(x):
    vals = extract_numeric_values(x)
    if not vals:
        return None
    return round(sum(vals) / len(vals))

def average_or_default(x, default):
    vals = extract_numeric_values(x)
    if not vals:
        return default
    return round(sum(vals) / len(vals))

def listify_variants(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def set_if_not_none(d, key, value):
    if value is not None:
        d[key] = value

cleaned_blocks = []

for block in blocks:
    variants = listify_variants(block.get("variants"))
    number_of_variants = len(variants)

    height = average_or_default(block.get("height_external"), default=0)
    width = average_or_default(block.get("width_external"), default=0)

    blast_resistance = average_or_none(block.get("blast_resistance"))
    luminance = average_or_none(block.get("luminance"))

    volume = int(width) * int(width) * int(height)

    result = {}
    set_if_not_none(result, "block", block.get("block"))

    result["height_external"] = int(height)
    result["width_external"] = int(width)
    result["number_of_variants"] = int(number_of_variants)
    result["volume"] = int(volume)

    set_if_not_none(result, "blast_resistance", blast_resistance)
    set_if_not_none(result, "luminance", luminance)

    for k in ("conductive", "movable", "full_cube", "spawnable"):
        v = block.get(k)
        if v is not None:
            result[k] = v

    cleaned_blocks.append(result)

with open("blocklist_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_blocks, f, indent=2, ensure_ascii=False)

print("blocklist_clean.json generated with selected variables.")
