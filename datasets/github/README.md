
## Dataset github

Relation Dépôt

Unique: (repo/owner)

- QN: qualitative nominale
- QO: qualitative ordinale
- TC: quantitative continue
- TD: quantitative discrete

- ID numérique (performance)
- QN: Nom
- QN: Owner
- QN: Description
- TD: Nombre stars
- TD: Nombre forks
- TD: Nombre de watchers
- TD: Nombre de commits
- TD: Date de création
- TD: Nombre issues open
- TD: Nombre issues closed
- TD: Nombre pull requests open
- TD: Nombre pull requests merged
- TD: Nombre total de fichiers
- TD: Nombre total de dossiers
- TD: Nombre de contributeurs
- TD: Nombre de branches, releases, tags...
- QN: Licence SPDX

Relation Tags

- clé repo
- QN: tag

Relation Langage

- clé repo
- QN: nom langage
- TD: nombre de lignes de code
- TD: nombre de lignes de commentaire
- TD: nombre de lignes vides (lignes vide ou contenant uniquement des espaces)
- TC: longueur de ligne moyenne

## Variante minimale

avec juste ce que reporoulette retourne: repos.json (1010 objects)

todo: ajouter deux variables

- QN name -> distance de Levenshtein
- QN owner -> distance de Levenshtein
- QN description -> QO : vide, petit, moyen, grand, nerd, TF-IDF
- TD date creation
- TD date derniere maj
- TD date dernier push
- TD nm stargazers
- QN languages

(oublier html_url, full_name et visibility)

## Organisation

### Phase 1: Fetching

Requêtes scc, faire attention au rate limits

Sortie: données brutes (csv)

Utilise

- scc: https://github.com/boyter/scc
- api github npm
- typescript

Implémenetation

- partir d'une liste de owner/nom de dépôts
- appeler l'api github pour métadonnées, countloc en parallèle
- si countloc échoue: fallback téléchargement + scc
- rassemblement et exportation CSV
  - repositories.csv
  - languages.csv

