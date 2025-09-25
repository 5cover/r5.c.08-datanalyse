# Blocks

- QN: qualitative nominale
- QO: qualitative ordinale
- TC: quantitative continue
- TD: quantitative discrete

## blocklist_clean.json

variable|type|signification
-|-|-
blast_resistance|TD|blast resistance
block|QN|block name (string).  use levenshtein diff
conductive|QO: No, Yes|conducts redstone?
full_cube|QO: No, yes
height_external|TD $[0;24]$|
luminance|TD $[0;15]$|light emission level
movable|QO: No, Breaks, Yes|can this block be moved
number_of_variants|TD|
spawnable|QN: No, Fire-Immune Mobs Only, Ocelots and Parrots Only, Polar Bear Only, Yes
volume|TD|
width external|TD|
