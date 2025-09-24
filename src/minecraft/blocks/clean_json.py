import json
from pathlib import Path

blocklist_path = "../../../datasets/minecraft/blocks/blocklist.json"

with open(blocklist_path, "r", encoding="utf-8") as f:
    blocks = json.load(f)

cleaned_blocks = []

for block in blocks:
    variants = block.get("variants", [])
    if isinstance(variants, str):
        variants = [variants]
    number_of_variants = len(variants)

    def safe_int(val):
        if isinstance(val, (int, float)):
            return int(val)
        try:
            return int(str(val).split()[0])
        except Exception:
            return None

    height = safe_int(block.get("height_external"))
    width = safe_int(block.get("width_external"))
    blast_resistance = safe_int(block.get("blast_resistance"))
    luminance = safe_int(block.get("luminance"))

    volume = height * width if isinstance(height, int) and isinstance(width, int) else None

    cleaned_blocks.append({
        "block": block.get("block"),
        "height_external": height,
        "width_external": width,
        "blast_resistance": blast_resistance,
        "luminance": luminance,
        "number_of_variants": number_of_variants,
        "volume": volume,
        "conductive": block.get("conductive"),
        "movable": block.get("movable"),
        "full_cube": block.get("full_cube"),
        "spawnable": block.get("spawnable"),
    })

# Save new JSON
with open("blocklist_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_blocks, f, indent=2, ensure_ascii=False)

print(cleaned_blocks)

print("blocklist_clean.json generated with selected variables.")
