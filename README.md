# oc-p8-fruits-aws-emr

TP Traitement Big Data sur AWS EMR

démarré le 13 juin 2026

## Installation

Se positionner dans le répertoire du projet :

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
