# oc-p8-fruits-aws-emr

TP Traitement Big Data sur AWS EMR

démarré le 13 juin 2026

## Les données

Le [jeu de données][1] constitué des images de fruits et des labels associés (en téléchargement direct à [ce lien][2], environ 1,4 Go).

[1]: https://www.kaggle.com/moltean/fruits
[2]: https://s3.eu-west-1.amazonaws.com/course.oc-static.com/projects/Data_Scientist_P8/fruits.zip

Sauvegardez-le en local de sorte à obtenir l'arborescence suivante :

```bash
$ tree -L 2 data/
data/
├── fruits
│   ├── fruits-360_dataset
│   └── fruits-360-original-size
├── Results
└── Test1
    ├── Apple Crimson Snow
    ├── Apple Golden 1
    └── Apple Golden 2
```

Copiez un petit échantillon de quelques classes (par exemple, trois) dans le répertoire `Test1`.

## Le notebook

Le notebook fourni `P8_Notebook_Linux_EMR_PySpark_V1.0.ipynb` a été séparé en deux :

- `P8_Notebook_Parts_1-3_Local.ipynb`
- `P8_Notebook_Parts_4-5_EMR.ipynb`

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

## AWS CLI: Installation Instructions [(source)][3]

[3]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-instructions

1. Select `Linux` > `Snap package`.

2. Run `sudo snap install aws-cli --classic`

3. Verify that the AWS CLI installed correctly by running `aws --version` which should return a string similar to

   ```plaintext
   aws-cli/2.35.21 Python/3.14.6 Linux/7.0.0-29-generic exe/x86_64.ubuntu.24
   ```

4. To update AWS CLI, run `sudo snap refresh aws-cli`

## AWS CLI: Setting up [(source)][4]

[4]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html

1. Sign in to AWS in your browser with your root user.

2. Run `aws login` (or `aws login --remote` [option][5] to provide a URL for you to open on a browser-enabled device in case the device using the AWS CLI does not have a browser)

3. Set AWS Region by typing in `eu-west-3` (which is Paris).

4. A new browser window or tab should open. Select your root user. (You can close that tab soon)

5. AWS CLI should return a string similar to

   ```plaintext
   Updated profile default to use arn:aws:iam::719640534499:root credentials.
   ```

   Which you can check by several means, either with

   ```bash
   tree ~/.aws
   .
   ├── cli
   │   └── cache
   │       └── session.db
   ├── config
   └── login
      └── cache
         └── 501e180d8d16300799e53cdbb147ba7a8f8b0c5f129ace7485a80a529421c38e.json
   ```

   or with

   ```bash
   cat ~/.aws/config

   [default]
   login_session = arn:aws:iam::719640534499:root
   region = eu-west-3
   ```

6. Complete `~/.aws/config` with a property `output = json` to the `[default]` section by running

   ```bash
   aws configure set output json
   ```

[5]: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html

## Create IAM Roles (One-Time)

In order for EMR to function and be allowed to launch clusters and access your S3 bucket, two essential IAM roles need to be created **once for a given region**:

- EMR service role (`EMR_DefaultRole`) which allows the EMR service to manage AWS resources (EC2 instances, security groups, etc.) on your behalf.

- EC2 instance profile (`EMR_EC2_DefaultRole`) which grants your cluster's EC2 instances permission to access other AWS services (especially S3 for reading your data and writing results)

To achieve that,

```bash
# 1. Verify you're logged in as root
aws sts get-caller-identity

# If not, Log out and log in as root
aws logout && rm -f ~/.aws/credentials && aws login

# 2. Create IAM default roles for the region
aws emr create-default-roles --region eu-west-3

# 3. Verify that both "EMR_DefaultRole" and "EMR_EC2_DefaultRole" roles have been created for the region
aws iam list-roles --region eu-west-3 | jq '.Roles[].RoleName'
```
