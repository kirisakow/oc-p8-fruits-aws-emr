# oc-p8-fruits-aws-emr

TP Traitement Big Data sur AWS EMR

démarré le 13 juin 2026

## Les données

Le [jeu de données][1] constitué des images de fruits et des labels associés (en téléchargement direct à [ce lien][2], environ 1,4 Go).

[1]: https://www.kaggle.com/moltean/fruits
[2]: https://s3.eu-west-1.amazonaws.com/course.oc-static.com/projects/Data_Scientist_P8/fruits.zip

Sauvegardez-le en local de sorte à obtenir l'arborescence suivante :

```bash
$ tree -L 2 data/
data/
├── fruits
│   ├── fruits-360_dataset
│   └── fruits-360-original-size
├── Results
└── Test1
    ├── Apple Crimson Snow
    ├── Apple Golden 1
    └── Apple Golden 2
```

Copiez un petit échantillon de quelques classes (par exemple, trois) dans le répertoire `Test1`.

## Le notebook

Voir `P8_Notebook_Linux_EMR_PySpark_V1.0.ipynb`

## Installation

0. Cloner ce repo.
1. Se positionner dans le répertoire du projet :

```bash
cd project/dir/
```

### Installer les dépendances renseignées dans `pyproject.toml`

```bash
uv sync
```

### Mettre à jour la variable d'environnement `LD_LIBRARY_PATH`

Une fois que la dépendance `"tensorflow[and-cuda]>=2.21.0"` a été correctement installée, il faut s'assurer que les chemins vers les bibliothèques Nvidia CUDA installées sont bien insérés au début de la variable d'environnement `LD_LIBRARY_PATH`.

Pour cela, modifier le fichier `~/.bashrc` pour y inclure la commande suivante :

```bash
export LD_LIBRARY_PATH="$(realpath $abs_path_to_my_venv/lib/python3.12/site-packages/nvidia/*/lib | paste -sd:):${LD_LIBRARY_PATH:-}"
```

### Installer le kernel Jupyter

```bash
uv run python -m ipykernel install --user --name='oc-fruits' --display-name='Python 3.12 (oc-fruits)'
```
