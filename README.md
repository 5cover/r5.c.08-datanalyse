# Projet jeu de données

Groupe : trinôme : Titouan + Matthieu

Idées jeu de données "maison"

- Raphaël : dépôts github
- Titouan : blocs Minecraft

## Structure du dépôt

./
├── datasets/minecraft/blocks/ : jeu de données
├── deliverables/
│   ├── Compte Rendu.md
│   └── img/ : images du compte rendu
├── README.md
└── src/minecraft
    └── acm/ : ACM
    └── acp/ : ACP
    └── afc/ : AFC
    └── clustering/ : K-means and hierarchical clustering

6 directories, 2 files

## Instructions

1. Cloner le dépôt
2. (Optionnel) Créer un environnement virtuel pour isoler les dépendances
3. `pip install requirements.txt -r`
4. Exécuter les scripts (la plupart on un `--help` en ligne de commande) pour générer outputs/graphiques

## Todo

- [x] FIX CLUSTERING showing all dots
- [ ] unified data transformation layer
- [x] recover unstded data to plot (standard scaler inverse)
