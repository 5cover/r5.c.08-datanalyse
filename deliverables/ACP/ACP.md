### ACP

**Méthode.** Nous appliquons une ACP sur 6 variables quantitatives (`height_external`, `width_external`, `number_of_variants`, `volume`, `blast_resistance`, `luminance`). Les données sont **centrées-réduites** (z-score), puis nous ajustons une PCA et exportons : valeurs propres, barchart de variance, cercle des corrélations, biplots individus/variables. *[insérer l’image : `acp_variance_barchart.png`]*

**Choix du nombre de composantes.** Les deux premières dimensions cumulent **66,46 %** de variance expliquée et les trois premières **81,75 %**. Nous retenons **2D** pour les graphiques (lisibilité) et **3D** pour la lecture globale.

| Dimension | Valeur propre | % variance expliquée | % cumulée |
|---|---:|---:|---:|
| Dim1 | 2,705 | **45,09 %** | 45,09 % |
| Dim2 | 1,282 | **21,37 %** | 66,46 % |
| Dim3 | 0,917 | 15,29 % | 81,75 % |
| Dim4 | 0,808 | 13,46 % | 95,21 % |
| Dim5 | 0,178 | 2,97 % | 98,18 % |
| Dim6 | 0,109 | 1,82 % | 100,00 % |

**Interprétations (charges/corrélations).**  
- **Dim1 (≈ 45 %) — Axe « taille/pleineur »** : fortes charges positives pour `volume` (≈ 0,58), `height_external` (≈ 0,58) et `width_external` (≈ 0,57). Les variables de gabarit sont corrélées entre elles et tirent les blocs vers la droite du plan.  
- **Dim2 (≈ 21 %) — Axe « résistance & lumière vs diversité »** : `luminance` (≈ 0,62) et `blast_resistance` (≈ 0,49) sont positives alors que `number_of_variants` est négative (≈ −0,61). On observe donc un **trade-off** : blocs lumineux/résistants ↔ moins de variantes, et inversement. *[insérer l’image : `acp_biplot_variables.png`]*

**Projection des individus.** Sur le plan (Dim1, Dim2), les blocs **volumineux/pleins** se projettent à droite (Dim1 > 0). En colorant par `conductive`, les blocs **conducteurs** se concentrent plutôt côté **Dim1 positif**, alors que les **non-conducteurs** sont plus dispersés vers Dim1 négatif. *[insérer l’image : `acp_individus.png`]*

**Biplot combiné.** Le biplot (points + flèches) confirme : le nuage s’étire surtout selon **Dim1** ; `volume`, `height_external` et `width_external` sont alignées (corrélées), tandis que `number_of_variants` pointe à l’opposé de `luminance`/`blast_resistance` sur **Dim2**. *[insérer l’image : `acp_biplot_combine.png`]*

**À retenir.** (i) la **morphologie** des blocs (hauteur/largeur/volume) explique l’essentiel de la variabilité, (ii) **résistance/luminosité** et **nombre de variantes** évoluent en sens opposé sur Dim2, (iii) ces axes structurent des sous-groupes utiles pour la suite (ex. clustering).
