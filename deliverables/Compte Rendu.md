# Projet d'analyse de données: les blocs Minecraft

Réalisation:

- Raphaël Bardini
- Titouan Rhétoré
- Mathieu

## Présentation du jeu de données

Liste des blocs dans le jeu-vidéo Minecraft.

### Origine

Source: [Minecraft Block Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia), consulté le 1er octobre 2025

Format: JSON

Nombre de lignes: 1079

### Variables

- QN: qualitative nominale
- QO: qualitative ordinale
- TC: quantitative continue
- TD: quantitative discrete

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

### Caractéristiques

- Valeur manquantes : `No Translation Key: *` &rarr; remplacées par l'ID du block
- Variance élevée : la standardisation sera vitale
- Valeurs très discrètes : beaucoup de superpositions

### Étapes de prétraitement

#### 1. Nettoyage: `blocklist.json` &rarr; `blocklist_clean.json`

[clean_json.py](./src/minecraft/blocks/clean_json.py)

1. **Aplatissement des variantes** :
    - Chaque bloc est décomposé en plusieurs lignes, une pour chaque variante.
    - Si un bloc n'a pas de variantes, il est traité comme une seule ligne.
    - Un champ `number_of_variants` est ajouté pour indiquer le nombre total de variantes du bloc d'origine.

2. **Extraction des dimensions et calcul du volume** :
    - Pour `height_external` et `width_external`, le script recherche une valeur numérique spécifique à la variante.
    - En l'absence de valeur spécifique, il calcule la moyenne de toutes les valeurs numériques trouvées.
    - Les dimensions sont converties en entiers (0 par défaut).
    - Un champ `volume` est calculé en utilisant la formule : `width * width * height`.

3. **Normalisation des champs numériques** :
    - Pour `blast_resistance` et `luminance`, le script extrait une valeur flottante, en priorisant celle de la variante.
    - Si aucune valeur spécifique à la variante n'est trouvée, la moyenne des valeurs disponibles est utilisée.

4. **Standardisation des champs qualitatifs** :
    - Les champs `conductive`, `full_cube`, et `spawnable` sont normalisés en "Yes", "No", ou "Maybe".
    - "Maybe" est assigné si des valeurs contradictoires ("Yes" et "No") sont présentes dans les données brutes du bloc.
    - Le champ `movable` est également normalisé en "Yes", "No", "Maybe", mais conserve sa valeur textuelle (ex: "Breaks") si elle ne correspond pas.

5. **Sauvegarde** :
    - La liste des blocs nettoyés est sauvegardée dans `blocklist_clean.json` avec une structure claire et formatée.

#### 2. Conversion en CSV: `blocklist_clean.json` &rarr; `blocklist_clean.csv`

[json_to_csv.py](./src/minecraft/blocks/json_to_csv.py)

## Analyse de données quantitatives

### K-means clustering

### 1. Choix de $K$

Nous choisissons $K$ en utilisant la méthode du coude:

[img/clustering-elbow.png](img/clustering-elbow.png)

Nous choisissons $K=7$.

## Analyse de données qualitatives

## Conclusion
