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
conductive|QO: No, Maybe, Yes|conducts redstone?
full_cube|QO: No, Maybe, yes
height_external|TD $[0;24]$|
luminance|TD $[0;15]$|light emission level
movable|QO: No, Breaks, Maybe, Yes|can this block be moved
number_of_variants|TD|
spawnable|QN: No, Fire-Immune Mobs Only, Ocelots and Parrots Only, Polar Bear Only, Maybe, Yes
volume|TD|Numbers of voxels (1/16 block³) the block occupies in average
width_external|TD|Average voxel width (1/16 blocks)
height_external|TD|Average voxel height (1/16 blocks)
