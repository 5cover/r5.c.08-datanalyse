### AMC

**Jeu de données & variables retenues.**  
Analyse réalisée sur **1079 blocs** du JSON Minecraft. Quatre variables qualitatives ont été utilisées : `conductive`, `full_cube`, `spawnable`, `movable`. Après transformation en tableau disjonctif, on obtient une matrice **1079 × 16** (toutes modalités).

**Transformation.**  
Les variables qualitatives ont été converties en indicatrices (0/1) sans suppression de modalités rares, conformément à l’item « AMC → Transformation des variables en tableau disjonctif ».

**Entraînement du modèle MCA.**  
L’ACM a été effectuée (backend : `mca` si dispo, sinon `prince`) en mode headless ; les figures et CSV sont exportés dans `acm_outputs/`.

**Choix du nombre de dimensions (Scree plot / inertie).**  
Les deux premières dimensions expliquent **≈ 26,1 %** et **≈ 20,6 %** de l’inertie, soit **≈ 46,7 % cumulé**. La courbe des valeurs propres présente un net « coude » après l’axe 2, ce qui justifie l’analyse principale dans le plan (Dim1, Dim2).
*Figure – Scree plot :* `![Scree plot](<lien_scree>)`

**Plan factoriel des individus.**  
Le nuage des blocs est dense autour de l’origine (profil « moyen ») avec quelques **individus atypiques** (règles de spawn particulières, combinaisons rares) qui s’éloignent surtout sur Dim2. Globalement :  
- **Dim1** ordonne les blocs du pôle « **Non** (peu conductifs, non pleins, non déplaçables / non spawnables) » vers le pôle « **Oui** » (conductifs, pleins, etc.).  
- **Dim2** isole surtout les **modalités ambiguës / rares** (p. ex. *Maybe* ou règles de spawn exceptionnelles), indiquant une hétérogénéité secondaire.  
*Figure – Individus :* `![ACM — individus](<lien_individus>)`

**Plan factoriel des modalités.**  
La carte des modalités confirme cette lecture :  
- Les modalités **`*_Yes`** de `conductive` et `full_cube` se **projettent du même côté de Dim1**, opposées aux **`*_No`** groupées de l’autre côté → **co-occurrence** de la « solidité/pleineur » et de la conductivité.  
- Les modalités **`*_Maybe`** (p. ex. `conductive_Maybe`, `full_cube_Maybe`, `spawnable_Maybe`) portent des coordonnées **fortes sur Dim2**, marquant leur rôle discriminant pour le second axe (cas particuliers / incertains).  
- Certaines modalités spécifiques de `spawnable` (règles restreintes) se placent près du pôle **Yes** de Dim1 mais avec une position distincte sur Dim2, suggérant qu’**être spawnable** ne signifie pas **spawnable pour tout** (nuances par type de mob).  
*Figure – Modalités :* `![ACM — modalités](<lien_modalites>)`

**Lecture synthétique des axes.**  
- **Dim1 (≈ 26 %)** : gradient **« non → oui »** de propriétés structurelles (conductivité, plein, mobilité/spawn).  
- **Dim2 (≈ 20 %)** : **spécificités/ambiguïtés** (modalités *Maybe* et règles de spawn exceptionnelles). 

