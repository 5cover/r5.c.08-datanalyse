import json
import re
from math import isfinite

# ---- CONFIG ----
blocklist_path = "../../../datasets/minecraft/blocks/blocklist.json"
out_path = "blocklist_clean.json"

# ---- HELPERS (float-preserving) ----

def safe_float(val):
    """Parse numbers (including strings like '0.75', '16', '9.5'); ignore booleans and 'Not Applicable'."""
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)) and isfinite(val):
        return float(val)
    try:
        s = str(val).strip()
        if s.lower().startswith("not applicable"):
            return None
        m = re.match(r"^[+-]?(\d+(\.\d+)?)", s)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None

def extract_numeric_floats(x):
    """Collect all numeric leaves as floats from arbitrarily nested dict/list/scalars."""
    vals = []
    if isinstance(x, dict):
        for v in x.values():
            vals.extend(extract_numeric_floats(v))
    elif isinstance(x, (list, tuple)):
        for v in x:
            vals.extend(extract_numeric_floats(v))
    else:
        n = safe_float(x)
        if n is not None:
            vals.append(n)
    return vals

def averagef_or_none(x):
    vals = extract_numeric_floats(x)
    if not vals:
        return None
    return sum(vals) / len(vals)

def listify_variants(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def normalize_names_key(key):
    """Split a mapping key like 'A<br>B' or 'A, B' or 'A|B' into clean names."""
    if key is None:
        return []
    parts = re.split(r"<br>|,|\|", str(key))
    return [p.strip() for p in parts if p and p.strip()]

def any_name_matches(key, target):
    """Does the key mention the target variant name exactly among its split parts?"""
    names = normalize_names_key(key)
    return any(n == target for n in names)

def numeric_for_variant(field_value, variant_name):
    """
    Try to find a numeric value in field_value specifically for variant_name.
    Works with:
      - scalar numbers
      - dicts where keys list variants (with <br>) and values are numbers or dicts of numbers
      - nested dicts of numbers (averaged)
    Returns a float or None.
    """
    # Direct scalar: applies to all variants
    if safe_float(field_value) is not None:
        return averagef_or_none(field_value)

    # Dict: try to match a branch that references this specific variant
    if isinstance(field_value, dict):
        matched_vals = []
        for k, v in field_value.items():
            if any_name_matches(k, variant_name):
                nums = extract_numeric_floats(v)
                matched_vals.extend(nums)
        if matched_vals:
            return sum(matched_vals) / len(matched_vals)

    # No clean per-variant mapping
    return None

def yes_no_maybe_from_states(v):
    """
    For 'conductive', 'full_cube', 'spawnable':
      - If scalar 'Yes'/'No' -> return as-is
      - If dict/list: collect leaves; if both Yes and No appear -> 'Maybe'
    """
    def collect_yn(x, bag):
        if isinstance(x, dict):
            for vv in x.values():
                collect_yn(vv, bag)
        elif isinstance(x, (list, tuple)):
            for vv in x:
                collect_yn(vv, bag)
        else:
            s = str(x).strip().lower()
            if s == "yes":
                bag.add("Yes")
            elif s == "no":
                bag.add("No")

    if isinstance(v, (dict, list, tuple)):
        bag = set()
        collect_yn(v, bag)
        if "Yes" in bag and "No" in bag:
            return "Maybe"
        elif "Yes" in bag:
            return "Yes"
        elif "No" in bag:
            return "No"
        else:
            return None
    else:
        s = str(v).strip()
        if s in ("Yes", "No"):
            return s
        return s if s else None

def per_variant_dimension(field_value, variant_name):
    """
    Dimension per-variant (height/width). Try variant-specific first, else overall average.
    Returns float (we'll cast to int at write time).
    """
    nv = numeric_for_variant(field_value, variant_name)
    if nv is not None:
        return nv
    return averagef_or_none(field_value)

def per_variant_numeric(field_value, variant_name):
    """
    Generic per-variant numeric extractor (e.g., blast_resistance, luminance).
    Preserves float precision (e.g., 0.75; (100+5)/2 = 52.5).
    """
    nv = numeric_for_variant(field_value, variant_name)
    if nv is not None:
        return nv
    return averagef_or_none(field_value)

# ---- LOAD ----

with open(blocklist_path, "r", encoding="utf-8") as f:
    blocks = json.load(f)

# ---- TRANSFORM ----

cleaned_blocks = []

for block in blocks:
    base_block_name = block.get("block")
    variants = listify_variants(block.get("variants"))
    if not variants:
        variants = [base_block_name] if base_block_name else []

    for variant in variants:
        row = {
            "block": variant,
            "number_of_variants": len(variants),
        }

        # Height/Width: compute, then cast to int
        h = per_variant_dimension(block.get("height_external"), variant)
        w = per_variant_dimension(block.get("width_external"), variant)
        h_i = int(h) if h is not None else 0
        w_i = int(w) if w is not None else 0
        row["height_external"] = h_i
        row["width_external"]  = w_i
        row["volume"] = w_i * w_i * h_i  # your definition

        # Per-variant numeric fields (float-preserving)
        br = per_variant_numeric(block.get("blast_resistance"), variant)
        if br is not None:
            row["blast_resistance"] = br  # keep float (e.g., 0.75 or 52.5)

        lum = per_variant_numeric(block.get("luminance"), variant)
        if lum is not None:
            # luminance is an integer domain, but we won't coerce if source is float-safe; cast to int if you prefer:
            row["luminance"] = lum

        # Qualitative -> Yes/No/Maybe
        for k in ("conductive", "full_cube", "spawnable"):
            v = block.get(k)
            ynm = yes_no_maybe_from_states(v)
            if ynm is not None:
                row[k] = ynm

        # Movable: keep as is unless it cleanly reduces to Yes/No; (enable Maybe here if you want)
        mv = block.get("movable")
        if mv is not None:
            ynm = yes_no_maybe_from_states(mv)
            row["movable"] = ynm if ynm is not None else (mv if isinstance(mv, str) and mv else None)

        cleaned_blocks.append(row)

# ---- SAVE ----

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_blocks, f, indent=2, ensure_ascii=False)

print(f"{out_path} generated with per-variant rows, float blast_resistance, and Yes/No/Maybe states.")
