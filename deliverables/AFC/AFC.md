### AFC

**Méthode.** Nous réalisons une **AFC** sur la table de contingence entre `conductive` (lignes) et `full_cube` (colonnes). Le script (`afc_blocks.py`) : (i) construit la table de contingence, (ii) effectue un **test du χ²** d’indépendance, (iii) **standardise** les colonnes (z-score), (iv) extrait les **valeurs propres** et **facteurs** (critère de Kaiser), puis (v) génère une **carte factorielle** sans rotation et avec **Varimax**/**Quartimax**. Tout est exécuté en **headless** et exporté (table, scree plot, cartes). :contentReference[oaicite:0]{index=0}

**Sélection des variables et pertinence.** La sélection automatique retient `x="conductive"` et `y="full_cube"` avec **p-value = 0** (χ²), ce qui rejette l’indépendance : **l’AFC est pertinente**. :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}  
*[insérer l’image : `scree_plot.png`]*

**Nombre de facteurs.** Avec trois modalités côté colonnes, au plus **2 facteurs** sont interprétables. Le **scree plot** montre deux valeurs propres ≥ 1 (Kaiser) et une troisième ≈ 0 ; on **retient 2 dimensions**, suffisantes pour résumer l’association `conductive` × `full_cube`.

**Cartes factorielles & rotations.**  
- *Sans rotation* : on observe des **proximité́s lignes↔colonnes homogènes** :  
  `Yes` (conductive) est proche de `Yes` (full_cube) ; `No` (conductive) est proche de `No` (full_cube) ; `Maybe` s’aligne avec `Maybe`. Ces voisinages traduisent une **corrélation positive forte** entre modalités de même nom. *[insérer l’image : `factor_map_pca_aucune_rotation.png`]*  
- *Varimax / Quartimax* : les rotations **simplifient la lecture** (charges concentrées par facteur) sans changer l’histoire : l’axe 1 ordonne plutôt **No ↔ Maybe**, l’axe 2 oppose **Yes** aux autres, et les duos (ligne/colonne) restent groupés. *[insérer les images : `factor_map_pca_varimax.png`, `factor_map_pca_quartimax.png`]*

**Interprétation substantielle (à partir de la table de contingence).** Les blocs **conducteurs** sont **très majoritairement pleins** (`full_cube=Yes`), tandis que les **non-conducteurs** sont surtout **non pleins** (`full_cube=No`) ; `Maybe` forme un petit groupe intermédiaire. Cette structure explique l’alignement des modalités homonymes sur la carte.

**À retenir.** (i) Le test du χ² confirme une **dépendance nette** entre `conductive` et `full_cube`. (ii) **Deux facteurs** suffisent (Kaiser + scree plot). (iii) Les **proximité́s** `Yes↔Yes`, `No↔No`, `Maybe↔Maybe` valident une **association forte** et facilement interprétable, stable avec ou sans rotation.