# Projet d'analyse de données: les blocs Minecraft

Réalisation:

- Raphaël Bardini
- Titouan Rhétoré
- Mathieu Le Bout

<!-- omit in toc -->
## Introduction

Ce projet vise à explorer et analyser un jeu de données issu du célèbre jeu vidéo Minecraft, en appliquant diverses techniques d'analyse de données. Nous nous concentrons sur les caractéristiques des blocs présents dans le jeu, en utilisant des méthodes statistiques et de machine learning pour extraire des informations pertinentes.

<!-- omit in toc -->
## Sommaire

- [Code source](#code-source)
- [Présentation du jeu de données "Blocks"](#présentation-du-jeu-de-données-blocks)
  - [Origine](#origine)
  - [Variables](#variables)
  - [Caractéristiques](#caractéristiques)
  - [Nettoyage](#nettoyage)
  - [Conversion en CSV: `blocklist_clean.json` → `blocklist_clean.csv`](#conversion-en-csv-blocklist_cleanjson--blocklist_cleancsv)
- [Analyse en composante principale](#analyse-en-composante-principale)
  - [Interprétations (charges/corrélations)](#interprétations-chargescorrélations)
- [Analyse factorielle des correspondances](#analyse-factorielle-des-correspondances)
  - [Cartes factorielles \& rotations](#cartes-factorielles--rotations)
- [Analyse en composants multiples](#analyse-en-composants-multiples)
  - [Lecture synthétique des axes](#lecture-synthétique-des-axes)
- [Clustering K-moyennes](#clustering-k-moyennes)
  - [Choix de $K$](#choix-de-k)
  - [Représentation](#représentation)
  - [Liste](#liste)
- [Clustering hiérarchique](#clustering-hiérarchique)
- [Conclusion](#conclusion)
  - [Structure des données révélée par les analyses](#structure-des-données-révélée-par-les-analyses)
  - [Dimensions principales identifiées](#dimensions-principales-identifiées)
  - [Taxonomie émergente des blocs](#taxonomie-émergente-des-blocs)
  - [Cohérence du game design](#cohérence-du-game-design)
  - [Méthodologie validée](#méthodologie-validée)
  - [Implications plus larges](#implications-plus-larges)
  - [Note sur l'utilisation de l'IA générative](#note-sur-lutilisation-de-lia-générative)
- [Annexe 1: Liste clusters](#annexe-1-liste-clusters)
  - [Cluster 1 (29 items, 2.69%): Énergie et illumination](#cluster-1-29-items-269-énergie-et-illumination)
  - [Cluster 2 (375 items, 34.75%): Matériaux de base et blocs pleins](#cluster-2-375-items-3475-matériaux-de-base-et-blocs-pleins)
  - [Cluster 3 (118 items, 10.94%): Transparence, clôtures et limites](#cluster-3-118-items-1094-transparence-clôtures-et-limites)
  - [Cluster 4 (120 items, 11.12%): Formes dérivées : escaliers et dalles](#cluster-4-120-items-1112-formes-dérivées--escaliers-et-dalles)
  - [Cluster 5 (235 items, 21.78%): Objets interactifs et décorations fines](#cluster-5-235-items-2178-objets-interactifs-et-décorations-fines)
  - [Cluster 6 (11 items, 1.02%): Blocs de contrôle et techniques réservées aux opérateurs](#cluster-6-11-items-102-blocs-de-contrôle-et-techniques-réservées-aux-opérateurs)
  - [Cluster 7 (191 items, 17.70%): Végétation, signaux et entités vivantes](#cluster-7-191-items-1770-végétation-signaux-et-entités-vivantes)

## Code source

Le code source de ce compte-rendu et des graphiques peut être trouvé sur le dépôt GitHub [5cover/r5.c.08-datanalyse](https://github.com/5cover/r5.c.08-datanalyse).

## Présentation du jeu de données "Blocks"

Liste des blocs dans le jeu-vidéo Minecraft.

### Origine

Source: [Minecraft Block Property Encyclopedia](https://joakimthorsen.github.io/MCPropertyEncyclopedia), consulté le 1er octobre 2025.

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
block|QN|block name (string)
conductive|QO: No, Maybe, Yes|does it conduct redstone?
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

### Nettoyage

`blocklist.json` &rarr; `blocklist_clean.json`

Script: [src/minecraft/blocks/clean_json.py](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/blocks/clean_json.py)

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

### Conversion en CSV: `blocklist_clean.json` &rarr; `blocklist_clean.csv`

Script: [src/minecraft/blocks/json_to_csv.py](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/blocks/json_to_csv.py)

```py
with open("./datasets/minecraft/blocks/blocklist_clean.json", encoding="utf-8") as inputfile:
    df = pd.read_json(inputfile)
df.to_csv("./datasets/minecraft/blocks/blocklist_clean.csv", sep=";", encoding="utf-8", index=False)
```

Note: certaines techniques utilise le format JSON, d'autres le format CSV.

## Analyse en composante principale

Script: [src/minecraft/acp/acp_blocks.py](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/acp/acp_blocks.py)

**Méthode.** Nous appliquons une ACP sur 6 variables quantitatives (`height_external`, `width_external`, `number_of_variants`, `volume`, `blast_resistance`, `luminance`). Les données sont **centrées-réduites** (z-score), puis nous ajustons une PCA et exportons : valeurs propres, barchart de variance, cercle des corrélations, biplots individus/variables.

![./img/acp_variance_barchart.png](./img/acp_variance_barchart.png)

**Choix du nombre de composantes.** Les deux premières dimensions cumulent **66,46 %** de variance expliquée et les trois premières **81,75 %**. Nous retenons **2D** pour les graphiques (lisibilité) et **3D** pour la lecture globale.

| Dimension | Valeur propre | % variance expliquée | % cumulée |
|---|---:|---:|---:|
| Dim1 | 2,705 | **45,09 %** | 45,09 % |
| Dim2 | 1,282 | **21,37 %** | 66,46 % |
| Dim3 | 0,917 | 15,29 % | 81,75 % |
| Dim4 | 0,808 | 13,46 % | 95,21 % |
| Dim5 | 0,178 | 2,97 % | 98,18 % |
| Dim6 | 0,109 | 1,82 % | 100,00 % |

### Interprétations (charges/corrélations)

- **Dim1 (≈ 45 %) — Axe « taille/"pleineur" »** : fortes charges positives pour `volume` (≈ 0,58), `height_external` (≈ 0,58) et `width_external` (≈ 0,57). Les variables de gabarit sont corrélées entre elles et tirent les blocs vers la droite du plan.  
- **Dim2 (≈ 21 %) — Axe « résistance & lumière vs diversité »** : `luminance` (≈ 0,62) et `blast_resistance` (≈ 0,49) sont positives alors que `number_of_variants` est négative (≈ −0,61). On observe donc un **trade-off** : blocs lumineux/résistants ↔ moins de variantes, et inversement.

![./img/acp_biplot_variables.png](./img/acp_biplot_variables.png)

**Projection des individus.** Sur le plan (Dim1, Dim2), les blocs **volumineux/pleins** se projettent à droite (Dim1 > 0). En colorant par `conductive`, les blocs **conducteurs** se concentrent plutôt côté **Dim1 positif**, alors que les **non-conducteurs** sont plus dispersés vers Dim1 négatif.

![./img/acp_individus.png](./img/acp_individus.png)

**Biplot combiné.** Le biplot (points + flèches) confirme : le nuage s’étire surtout selon **Dim1** ; `volume`, `height_external` et `width_external` sont alignées (corrélées), tandis que `number_of_variants` pointe à l’opposé de `luminance`/`blast_resistance` sur **Dim2**.

![./img/acp_biplot_combine.png](./img/acp_biplot_combine.png)

**À retenir.** (i) la **morphologie** des blocs (hauteur/largeur/volume) explique l’essentiel de la variabilité, (ii) **résistance/luminosité** et **nombre de variantes** évoluent en sens opposé sur Dim2, (iii) ces axes structurent des sous-groupes utiles pour la suite (ex. clustering).

## Analyse factorielle des correspondances

Script: [src/minecraft/afc/afc_blocks.py](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/afc/afc_blocks.py)

**Méthode.** Nous réalisons une **AFC** sur la table de contingence entre `conductive` (lignes) et `full_cube` (colonnes). Le script (`afc_blocks.py`) :

1. construit la table de contingence
2. effectue un **test du χ²** d’indépendance
3. **standardise** les colonnes (z-score)
4. extrait les **valeurs propres** et **facteurs** (critère de Kaiser)
5. puis génère une **carte factorielle** sans rotation et avec **Varimax**/**Quartimax**. Tout est exécuté en **headless** et exporté (table, scree plot, cartes).

**Sélection des variables et pertinence.** La sélection automatique retient `x="conductive"` et `y="full_cube"` avec **p-value = 0** (χ²), ce qui rejette l’indépendance : **l’AFC est pertinente**.
![./img/afc_scree_plot.png](./img/afc_scree_plot.png)

**Nombre de facteurs.** Avec trois modalités côté colonnes, au plus **2 facteurs** sont interprétables. Le **scree plot** montre deux valeurs propres ≥ 1 (Kaiser) et une troisième ≈ 0 ; on **retient 2 dimensions**, suffisantes pour résumer l’association `conductive` × `full_cube`.

### Cartes factorielles & rotations

- *Sans rotation* : on observe des **proximité́s lignes↔colonnes homogènes** :  
  `Yes` (conductive) est proche de `Yes` (full_cube) ; `No` (conductive) est proche de `No` (full_cube) ; `Maybe` s’aligne avec `Maybe`. Ces voisinages traduisent une **corrélation positive forte** entre modalités de même nom.

  ![./img/factor_map_pca_aucune_rotation.png](./img/factor_map_pca_aucune_rotation.png)
- *Varimax / Quartimax* : les rotations **simplifient la lecture** (charges concentrées par facteur) sans changer l’histoire : l’axe 1 ordonne plutôt **No ↔ Maybe**, l’axe 2 oppose **Yes** aux autres, et les duos (ligne/colonne) restent groupés.
  ![./img/factor_map_pca_varimax.png](./img/factor_map_pca_varimax.png)
  ![./img/factor_map_pca_quartimax.png](./img/factor_map_pca_quartimax.png)

**Interprétation substantielle (à partir de la table de contingence).** Les blocs **conducteurs** sont **très majoritairement pleins** (`full_cube=Yes`), tandis que les **non-conducteurs** sont surtout **non pleins** (`full_cube=No`) ; `Maybe` forme un petit groupe intermédiaire. Cette structure explique l’alignement des modalités homonymes sur la carte.

**À retenir.** (i) Le test du χ² confirme une **dépendance nette** entre `conductive` et `full_cube`. (ii) **Deux facteurs** suffisent (Kaiser + scree plot). (iii) Les **proximité́s** `Yes↔Yes`, `No↔No`, `Maybe↔Maybe` valident une **association forte** et facilement interprétable, stable avec ou sans rotation.

## Analyse en composants multiples

Script: [src/minecraft/acm/acm_blocks.py](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/acm/acm_blocks.py)

**Jeu de données & variables retenues.**  
Analyse réalisée sur **1079 blocs** du JSON Minecraft. Quatre variables qualitatives ont été utilisées : `conductive`, `full_cube`, `spawnable`, `movable`. Après transformation en tableau disjonctif, on obtient une matrice **1079 × 16** (toutes modalités).

**Transformation.**  
Les variables qualitatives ont été converties en indicatrices (0/1) sans suppression de modalités rares, conformément à l’item « AMC → Transformation des variables en tableau disjonctif ».

**Entraînement du modèle ACM.**  
L’ACM a été effectuée (backend : `mca` si disponible, sinon `prince`) en mode headless ; les figures et CSV sont exportés dans `acm_outputs/`.

**Choix du nombre de dimensions (Scree plot / inertie).**  
Les deux premières dimensions expliquent **≈ 26,1 %** et **≈ 20,6 %** de l’inertie, soit **≈ 46,7 % cumulé**. La courbe des valeurs propres présente un net « coude » après l’axe 2, ce qui justifie l’analyse principale dans le plan (Dim1, Dim2).
![Scree plot](./img/acm_scree.png)

**Plan factoriel des individus.**  
Le nuage des blocs est dense autour de l’origine (profil « moyen ») avec quelques **individus atypiques** (règles de spawn particulières, combinaisons rares) qui s’éloignent surtout sur Dim2. Globalement :  

- **Dim1** ordonne les blocs du pôle « **Non** (peu conductifs, non pleins, non déplaçables / non spawnables) » vers le pôle « **Oui** » (conductifs, pleins, etc.).  
- **Dim2** isole surtout les **modalités ambiguës / rares** (p. ex. *Maybe* ou règles de spawn exceptionnelles), indiquant une hétérogénéité secondaire.  
![ACM — individus](./img/acm_individuals.png)

**Plan factoriel des modalités.**  
La carte des modalités confirme cette lecture :  

- Les modalités **`*_Yes`** de `conductive` et `full_cube` se **projettent du même côté de Dim1**, opposées aux **`*_No`** groupées de l’autre côté → **co-occurrence** de la « solidité/"pleineur" » et de la conductivité.  
- Les modalités **`*_Maybe`** (p. ex. `conductive_Maybe`, `full_cube_Maybe`, `spawnable_Maybe`) portent des coordonnées **fortes sur Dim2**, marquant leur rôle discriminant pour le second axe (cas particuliers / incertains).  
- Certaines modalités spécifiques de `spawnable` (règles restreintes) se placent près du pôle **Yes** de Dim1 mais avec une position distincte sur Dim2, suggérant qu’**être spawnable** ne signifie pas **spawnable pour tout** (nuances par type de mob).  
![ACM — modalités](./img/acm_modalities.png)

### Lecture synthétique des axes

- **Dim1 (≈ 26 %)** : gradient **« non → oui »** de propriétés structurelles (conductivité, plein, mobilité/spawn).  
- **Dim2 (≈ 20 %)** : **spécificités/ambiguïtés** (modalités *Maybe* et règles de spawn exceptionnelles).

## Clustering K-moyennes

Scripts: [src/minecraft/clustering/](https://github.com/5cover/r5.c.08-datanalyse/tree/main/src/minecraft/clustering)

### Choix de $K$

Nous choisissons $K$ en utilisant la méthode du coude:

![./img/clustering-elbow.png](./img/clustering-elbow.png)
*Inertie (WCSS) par nombre de clusters*

Nous choisissons $K=7$, ce qui veux dire que nous aurons 7 clusters.

### Représentation

Nous affichons les résultats du clustering sur deux dimensions intéressantes. Ici, nous choisissons à partir des variables corrélées identifiées par l'ACP.

Du fait de la répétition de valeurs dans le jeu de données, de nombreux points sont superposés. Cela est représenté par de plus gros points. La mise à l'échelle est linéaire (5 * nombre de points superposés). Un point a une taille de 5, deux points superposé forment un point de taille 10, etc.

![./img/clustering-scatter-of-blast_resistance-by-luminance.png](./img/clustering-scatter-of-blast_resistance-by-luminance.png)
*Blast resistance par luminance*
![./img/clustering-scatter-of-blast_resistance-by-number_of_variants.png](./img/clustering-scatter-of-blast_resistance-by-number_of_variants.png)
*Blast resistance par nombre de variantes*
![./img/clustering-scatter-of-luminance-by-number_of_variants.png](./img/clustering-scatter-of-luminance-by-number_of_variants.png)
*Luminance par nombre de variantes*
![./img/clustering-scatter-of-volume-by-height_external.png](./img/clustering-scatter-of-volume-by-height_external.png)
*Volume par hauteur*  
![./img/clustering-scatter-of-volume-by-width_external.png](./img/clustering-scatter-of-volume-by-width_external.png)
*Volume par largeur*
![./img/clustering-scatter-of-height_external-by-width_external.png](./img/clustering-scatter-of-height_external-by-width_external.png)
*Hauteur par largeur*

### Liste

Une regroupement des clusters et une interprétation peut être trouvée dans l'[Annexe 1: Liste clusters](#annexe-1-liste-clusters).

## Clustering hiérarchique

![./img/dendogram.png](./img/dendogram.png)
*Dendogramme avec p=4*

Ce dendogramme permet de visualiser les regroupements hiérarchiques des blocs, en utilisant la méthode de Ward. Nous avons choisi de couper l'arbre à p=4.

## Conclusion

En analysant l'ensemble des travaux menés sur le dataset des blocs Minecraft, plusieurs conclusions majeures émergent.

### Structure des données révélée par les analyses

Les analyses ont révélé une **organisation cohérente et hiérarchique** des blocs Minecraft selon plusieurs dimensions complémentaires.

### Dimensions principales identifiées

1. **Dimension morphologique** (ACP - Dim1, 45% de variance) : Les blocs se structurent principalement autour de leur **taille et volume** (`height_external`, `width_external`, `volume`), révélant l'importance des propriétés géométriques dans la conception du jeu.

2. **Dimension fonctionnelle** (ACP - Dim2, 21% de variance) : Un trade-off intéressant entre **spécialisation et diversité** : les blocs lumineux/résistants tendent à avoir moins de variantes, tandis que les blocs communs se déclinent en de nombreuses variantes.

3. **Dimension qualitative** (ACM, 47% d'inertie cumulée) : Les propriétés catégorielles (`conductive`, `full_cube`, `spawnable`, `movable`) suivent des **patterns de co-occurrence** logiques - les blocs conducteurs sont majoritairement pleins, confirmant la cohérence du design du jeu.

### Taxonomie émergente des blocs

Le clustering K-moyennes (K=7) a révélé une **taxonomie naturelle** reflétant l'usage et la logique du jeu :

1. **Énergie/Magie** (2.69%) : Blocs lumineux et rituels
2. **Matériaux de base** (34.75%) : Fondations constructives
3. **Délimitation** (10.94%) : Transparence et clôtures
4. **Architecture** (11.12%) : Variantes géométriques (dalles, escaliers)
5. **Habitat/Interaction** (21.78%) : Mobilier et redstone
6. **Technique** (1.02%) : Blocs administratifs
7. **Vivant/Réactif** (17.70%) : Végétation et signalisation

### Cohérence du game design

Les analyses confirment la **remarquable cohérence** du système de blocs Minecraft :

- **Corrélations logiques** : Les propriétés physiques (conductivité ↔ solidité) s'alignent avec les mécaniques de jeu
- **Diversité contrôlée** : Les blocs spécialisés (lumineux) sont uniques, les blocs communs (matériaux) sont déclinés
- **Hiérarchie fonctionnelle** : Chaque cluster correspond à un rôle gameplay distinct

### Méthodologie validée

La convergence des résultats entre les différentes techniques (ACP, ACM, AFC, clustering) **valide la robustesse** de l'analyse :

- L'AFC confirme les associations qualitatives identifiées par l'ACM
- Le clustering reproduit naturellement les dimensions de l'ACP
- Les clusters émergents correspondent aux catégories intuitives du jeu

### Implications plus larges

Cette analyse démontre que les systèmes de jeu vidéo, même apparemment simples, possèdent une **structure sous-jacente sophistiquée** pouvant être révélée par l'analyse de données. Les 1079 blocs ne sont pas distribués aléatoirement mais suivent une logique de design cohérente, optimisant à la fois la **diversité créative** et la **simplicité conceptuelle**.

L'approche méthodologique mixte (quantitative + qualitative, supervisée + non-supervisée) s'avère particulièrement efficace pour révéler ces structures complexes dans des domaines d'application non-traditionnels comme le game design, en particulier vis-à-vis du caractère discret du jeu de données.

Nous ne sommes pas sur des mesures continues comme avec le jeu de données Iris par exemple; nous travaillons avec des données bien plus discrètes, souvent catégorielles et délibérément choisies par les développeurs de Minecraft.

### Note sur l'utilisation de l'IA générative

Nous avons utilisé l'IA générative (avec review) pour:

- Interprétation intuitive des clusters déduits
- Génération de code boilerplate

## Annexe 1: Liste clusters

Cet annexe contient l'interprétation des clusters générés par l'algorithme des K-moyennes.

La liste complète avec les blocs groupés par cluster peut être trouvée à [deliverables/Annexe 1 Liste clusters.md](<https://github.com/5cover/r5.c.08-datanalyse/blob/main/deliverables/Annexe%201%20Liste%20clusters.md>).

### Cluster 1 (29 items, 2.69%): Énergie et illumination

Ce groupe rassemble presque exclusivement des blocs lumineux ou liés à la magie : torches, lanternes, portails, beacon, ancrages du Nether, etc. On y trouve aussi des éléments rares et rituels (Conduit, Enchanting Table, Respawn Anchor).

**Description :** ce cluster regroupe les objets qui produisent de la lumière, symbolisent le pouvoir ou la dimension magique du jeu. La luminosité étant une propriété peu commune, il n'est pas surprenant que l'algorithme des K-moyennes en ait réuni la plupart des blocs lumineux dans le même cluster.

### Cluster 2 (375 items, 34.75%): Matériaux de base et blocs pleins

C’est de loin le plus massif : pierres, minerais, bois, métaux, verres teintés, bétons, terres, et blocs utilitaires de construction. Il réunit la quasi-totalité des **blocs de structure ou de décoration compacts** du jeu.

**Description :** il s’agit clairement du **socle matériel** : tout ce qu’on mine, cuit ou polit pour construire. Un inventaire des ressources solides et "pleines" du monde.

### Cluster 3 (118 items, 10.94%): Transparence, clôtures et limites

Ce groupe combine les vitres, les glaces, les feuilles, les grilles et les clôtures, mais aussi les murs et barrières décoratives.

**Description :** un ensemble orienté sur la **délimitation visuelle et la transparence**. Les blocs y sont semi-perméables, décoratifs ou protecteurs, souvent employés pour séparer sans enfermer. Il n'est pas étonant que les blocs non-pleins (Fences, Walls...) et transparents (Glass) se retrouvent dans le même cluster: ils sont tous les deux non conducteurs (`conductive`=0).

### Cluster 4 (120 items, 11.12%): Formes dérivées : escaliers et dalles

Tous les blocs ici sont des variantes "géométriques" de matériaux du cluster 2 : dalles, escaliers, et leurs versions oxydées ou cirées.

**Description :** le **volet architectural**, centré sur les déclinaisons fonctionnelles des matériaux de base pour sculpter et affiner les constructions.

### Cluster 5 (235 items, 21.78%): Objets interactifs et décorations fines

Mélange de blocs fonctionnels (portes, trappes, pistons, comparateurs) et d’éléments esthétiques (bougies, têtes, fleurs en pot, lits, tapis, chandeliers).

**Description :** le **registre de l’habitat** : tout ce qui anime ou personnalise un intérieur, entre technologie redstone simple, mobilier et végétation d’ornement.

### Cluster 6 (11 items, 1.02%): Blocs de contrôle et techniques réservées aux opérateurs

On n’y trouve que des blocs inaccessibles en survie : Command Blocks, Structure Block, End Portal Frame, Light Block, Bedrock, etc.

**Description :** le **noyau administratif et technique**, regroupant les outils de commande, de génération ou de structure du moteur du jeu.

### Cluster 7 (191 items, 17.70%): Végétation, signaux et entités vivantes

Riche en plantes, pousses, champignons, coraux, bannières et plaques de pression, ce cluster mêle éléments naturels et blocs sensibles (rails, redstone wire, tripwire).

**Description :** le **monde vivant et réactif** : tout ce qui pousse, capte ou signale. Il combine flore, éléments organiques et dispositifs légers du gameplay.
