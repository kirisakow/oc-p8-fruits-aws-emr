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

## IAM User Management

### 1. Create IAM User (Required)

Create a dedicated IAM user for this project:

```bash
# Create IAM user
aws iam create-user --user-name oc-p8-user --region eu-west-3

# Verify user was created
aws iam list-users --region eu-west-3
```

### 2. Ensure IAM User Permissions

Your IAM user needs at minimum:

- `AmazonElasticMapReduceFullAccess`
- `AmazonS3FullAccess`
- `IAMReadOnlyAccess`

```bash
# List user policies (should be empty initially)
aws iam list-attached-user-policies --user-name oc-p8-user --region eu-west-3

# Attach required policies
aws iam attach-user-policy --user-name oc-p8-user --policy-arn arn:aws:iam::aws:policy/AmazonElasticMapReduceFullAccess --region eu-west-3
aws iam attach-user-policy --user-name oc-p8-user --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess --region eu-west-3
aws iam attach-user-policy --user-name oc-p8-user --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess --region eu-west-3
aws iam attach-user-policy --user-name oc-p8-user --policy-arn arn:aws:iam::aws:policy/IAMReadOnlyAccess --region eu-west-3

# List user policies: You should see the three policies have been attached
aws iam list-attached-user-policies --user-name oc-p8-user --region eu-west-3
```

## Log in as IAM User: AWS Credentials Setup

**Note:** Requires `jq` binary. Install it with `sudo apt install jq`

Run the below command which creates access key and saves the returned `AccessKeyId` and `SecretAccessKey` values (you'll need them for AWS CLI configuration):

```bash
# Create access keys for the user
aws iam create-access-key --user-name oc-p8-user --region eu-west-3 | tee /tmp/oc-p8-keys.json

# Configure Credentials
aws configure set aws_access_key_id $(jq -r '.AccessKey.AccessKeyId' /tmp/oc-p8-keys.json)
aws configure set aws_secret_access_key $(jq -r '.AccessKey.SecretAccessKey' /tmp/oc-p8-keys.json)

# Verify the keys were saved correctly
cat ~/.aws/credentials
```

**Optional:** A few other useful commands:

```bash
# List access keys
aws iam list-access-keys --user-name oc-p8-user --region eu-west-3

# Should you need to delete an access key, run
aws iam delete-access-key --user-name oc-p8-user --access-key-id YOUR_OLD_KEY_ID --region eu-west-3

# Should you need to delete ALL the access keys, run
aws iam list-access-keys --user-name oc-p8-user --region eu-west-3 \
| jq -r '.AccessKeyMetadata[].AccessKeyId' \
| xargs -I {} aws iam delete-access-key --user-name oc-p8-user --access-key-id {} --region eu-west-3
```

### Log out of the root session and switch to IAM user

```bash
# Verify you're now using the IAM user
aws sts get-caller-identity

# If you're still logged in as root, log out of root session
aws logout

# Verify you're now using the IAM user
aws sts get-caller-identity
```

### Log back in as root (optional)

```bash
# Should you need to log back in as root, run
aws logout && rm -f ~/.aws/credentials && aws login
```

## EC2 Key Pair Management

```bash
# Verify existing key pairs:
aws ec2 describe-key-pairs --region eu-west-3

# If none exist, create a new ed25519 key pair. The `--output text` options converts the `--query 'KeyMaterial'` JSON output (with quotes and escaped newlines) to plain text, raw private key material (with actual newlines, no quotes), which is required for a valid PEM file.
aws ec2 create-key-pair --key-name oc-p8-fruits-aws-ec2-key --region eu-west-3 --key-type ed25519 --query 'KeyMaterial' --output text \
| tee ~/.ssh/oc-p8-fruits-aws-ec2-key.pem

# Set permissions as SSH requires private keys to strictly be read-only for owner
chmod 400 ~/.ssh/oc-p8-fruits-aws-ec2-key.pem

# Should you need to delete a key pair, run
aws ec2 delete-key-pair --key-name KEY_PAIR_NAME --region eu-west-3
rm /path/to/KEY_PAIR_NAME.pem
```

### Notes

- `--key-name` option value will be used later in `aws emr create-cluster` command as `--ec2-attributes` option value.

- Should you choose to store your private key file `KEY_PAIR_NAME.pem` inside your local git repository, there are several things you need to know:
  1. Ensure private key is untracked by running `git status`. Otherwise you'll need to untrack it with `git rm --cached KEY_PAIR_NAME.pem`.
  2. Update `.gitignore` with a `*.pem` entry.
  3. Prevent accidental commits with git-secrets:

     ```bash
     git secrets --install
     git secrets --add 'KEY_PAIR_NAME'
     git secrets --add '\.pem$'
     ```

## Upload files in an S3 bucket

```bash
# 1. Create an S3 bucket with a unique name 'kirisakow-oc-p8-fruits-aws-emr'
aws s3 mb s3://kirisakow-oc-p8-fruits-aws-emr --region eu-west-3

# 2. Verify that the bucket has been successfully created
aws s3 ls

# 3. Various commands to upload contents of a local file or directory to the bucket
aws s3 cp    bootstrap-emr.sh  s3://kirisakow-oc-p8-fruits-aws-emr/
aws s3 cp    data/Test1        s3://kirisakow-oc-p8-fruits-aws-emr/data/Test1 --recursive
# To resume an interrupted copying, use sync
aws s3 sync  data/Test1        s3://kirisakow-oc-p8-fruits-aws-emr/data/Test1
```

## Data assessment & AWS EMR cluster sizing analysis

### Data assessment

| Relative path | N images | Size on disk |
| - | - | - |
| `data/Test1`                           | 472    | 3.6MB |
| `data/fruits/fruits-360-original-size` | 12,455 | ~583MB |
| `data/fruits/fruits-360_dataset`       | 90,483 | ~1.6GB |

### Cluster sizing analysis

Here are a few conservative options for AWS EMR cluster located in eu-west-3 region and purported for TensorFlow + PySpark image processing (MobileNetV2 feature extraction via pandas UDF):

| Use Case                   | Master    | Core Nodes        | Estimated Cost     | Processing Time |
| - | - | - | - | - |
| Test1 (472 images)         | m5.xlarge | 1 × m5.xlarge     | ~$0.36/hour        | < 10 min    |
| Medium scale (~10K images) | r5.xlarge | 2 × r5.xlarge     | ~$1.00/hour        | 20 – 30 min |
| Full dataset (90K+ images) | r5.xlarge | 3 – 4 × r5.xlarge | ~$1.50 – 2.00/hour | 40 – 60 min |

**Assumptions:** r5.xlarge (4 vCPU, 32GB RAM), spot pricing, MobileNetV2 needs ~1-2GB per executor for batch processing

**Recommendation:** Start with 1 master (m5.xlarge) + 2 core nodes (r5.xlarge) for testing. Scale core nodes to 3 – 4 for full dataset.

### Cost Control Tips

- Use **spot instances** for non-critical workloads (add `Market=SPOT` to instance groups)
- Always use **auto-terminate** for test clusters
- Monitor costs via AWS Cost Explorer
- For Test1, the cluster should complete in <30 minutes

## Create transient EMR cluster for processing dummy script `test_pyspark.py`

### 0. Upload `test_pyspark.py` in an S3 bucket

```bash
aws s3 cp test_pyspark.py s3://kirisakow-oc-p8-fruits-aws-emr/
```

### 1. Create EMR Cluster

Here's recommended frugal EMR cluster configuration for processing `data/Test1` sample (472 images, 3 apple classes):

- Master: 1 × r5.xlarge (4 vCPU, 32GB RAM)
- Core: 1 × r5.xlarge (4 vCPU, 32GB RAM)
- Region: eu-west-3 (Paris) for RGPD compliance
- Estimated cost: ~$0.40-0.60/hour (spot pricing) or ~$1.00/hour (on-demand)

This gives 8 vCPUs / 64GB total—more than sufficient for MobileNetV2 feature extraction on 472 images.

```bash
aws emr create-cluster \
--name "OC-P8-Fruits-Test1" \
--release-label emr-6.15.0 \
--applications Name=Spark Name=Hadoop \
--ec2-attributes KeyName=oc-p8-fruits-aws-ec2-key \
--instance-groups \
InstanceGroupType=MASTER,InstanceType=r5.xlarge,InstanceCount=1 \
InstanceGroupType=CORE,InstanceType=r5.xlarge,InstanceCount=1 \
--bootstrap-actions Path=s3://kirisakow-oc-p8-fruits-aws-emr/bootstrap-emr.sh,Name="Install Python packages" \
--steps Type=Spark,Name="RunTestPySpark",ActionOnFailure=CONTINUE,Args=[s3://kirisakow-oc-p8-fruits-aws-emr/test_pyspark.py] \
--log-uri s3://kirisakow-oc-p8-fruits-aws-emr/elasticmapreduce/logs/ \
--region eu-west-3 \
--auto-terminate \
--use-default-roles
```

### 2. Monitor Cluster

```bash
# List clusters
aws emr list-clusters --region eu-west-3

# Get cluster details (returns a big JSON)
aws emr describe-cluster --cluster-id j-XXXXXXXXXXXX --region eu-west-3

# List steps
aws emr list-steps --cluster-id j-XXXXXXXXXXXX --region eu-west-3

# Get step details
aws emr describe-step --cluster-id j-XXXXXXXXXXXX --step-id s-XXXXXXXXXXXXXXXXXXXX --region eu-west-3
```

### 3. Inspect logs

You'll be given access to various gzipped logs (typically: `controller.gz`, `stderr.gz`, and `stdout.gz`) that you can read with the following command:

```bash
aws s3 cp s3://kirisakow-oc-p8-fruits-aws-emr/elasticmapreduce/logs/j-XXXXXXXXXXXX/steps/s-XXXXXXXXXXXXXXXXXXXX/stdout.gz - | gunzip

aws s3 cp s3://kirisakow-oc-p8-fruits-aws-emr/elasticmapreduce/logs/j-XXXXXXXXXXXX/steps/s-XXXXXXXXXXXXXXXXXXXX/stderr.gz - | gunzip
#         └───────────────────────────┬────────────────────────────┘                                                     └┬┘
#                                     │                                                                                   │
#                       --log-uri value                                                    copy to stdout instead of saving
```

## Create a persistent EMR cluster for processing `data/Test1` sample in JupyterHub

### 0. Upload files in an S3 bucket

```bash
# Upload JupyterHub S3 persistence configuration file
aws s3 cp jupyter-s3-conf.json s3://kirisakow-oc-p8-fruits-aws-emr/

# Upload data sample
aws s3 cp data/Test1 s3://kirisakow-oc-p8-fruits-aws-emr/data/Test1 --recursive
```

### 1. Create EMR Cluster

Here's recommended frugal EMR cluster configuration for processing `data/Test1` sample (472 images, 3 apple classes):

- Master: 1 × r5.xlarge (4 vCPU, 32GB RAM)
- Core: 2 × r5.xlarge (8 vCPU, 64GB RAM)
- Region: eu-west-3 (Paris) for RGPD compliance
- Estimated cost: ~$0.40-0.60/hour (spot pricing) or ~$1.00/hour (on-demand)

This gives 12 vCPUs and 96GB RAM total — more than sufficient for MobileNetV2 feature extraction on 472 images.

```bash
aws emr create-cluster \
--name "OC-P8-Fruits-Test1-Jupyter" \
--release-label emr-6.15.0 \
--applications Name=Spark Name=Hadoop Name=JupyterHub \
--ec2-attributes KeyName=oc-p8-fruits-aws-ec2-key \
--instance-groups \
InstanceGroupType=MASTER,InstanceType=r5.xlarge,InstanceCount=1 \
InstanceGroupType=CORE,InstanceType=r5.xlarge,InstanceCount=2 \
--bootstrap-actions Path=s3://kirisakow-oc-p8-fruits-aws-emr/bootstrap-emr.sh,Name="Install Python packages" \
--configurations file://jupyter-s3-conf.json \
--log-uri s3://kirisakow-oc-p8-fruits-aws-emr/elasticmapreduce/logs/ \
--region eu-west-3 \
--no-auto-terminate \
--use-default-roles
```

### 2. Monitor Cluster

```bash
# List clusters
aws emr list-clusters --region eu-west-3

# Get cluster details (returns a big JSON)
aws emr describe-cluster --cluster-id j-H8PK3O2MTK5W --region eu-west-3

# Check cluster status
aws emr describe-cluster --cluster-id j-H8PK3O2MTK5W --region eu-west-3 --query "Cluster.Status.State"

# Check cluster status continuously
watch -n 30 "aws emr describe-cluster --cluster-id j-H8PK3O2MTK5W --region eu-west-3 --query 'Cluster.Status.State'"

# List steps
aws emr list-steps --cluster-id j-H8PK3O2MTK5W --region eu-west-3

# Get step details
aws emr describe-step --cluster-id j-H8PK3O2MTK5W --step-id s-XXXXXXXXXXXXXXXXXXXX --region eu-west-3
```

### 3. Set up the SSH tunnel to access JupyterHub

**Prerequisites:** Wait till the cluster status state has switched to WAITING.

#### 1. Configure the security group (One-Time per IP Address)

```bash
# Find the security group ID for the master node
aws emr describe-cluster \
--cluster-id j-H8PK3O2MTK5W \
--query "Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup" \
--region eu-west-3

# Get your public IPv4 address
curl -4 ifconfig.me

# Authorize SSH access for your IP address
aws ec2 authorize-security-group-ingress \
--group-id sg-0730998104e415519 \
--protocol tcp \
--port 22 \
--cidr $(curl -4 ifconfig.me)/32 \
--region eu-west-3
```

#### 2. FoxyProxy configuration (One-Time)

1. Install FoxyProxy extension for Firefox/Chrome if not already installed

2. Add new proxy:
   - Name: AWS EMR Cluster (or anything)
   - Proxy Type: SOCKS5
   - Proxy Host: 127.0.0.1 (or localhost)
   - Proxy Port: 5555

3. Save.

With the proxy active, all traffic routes through your SSH tunnel to the EMR master node, giving you access to JupyterHub and other web applications.

#### 3. Get your master node's public DNS

```bash
# Get master node public DNS name (ec2-XXX-XXX-XXX-XXX.eu-west-3.compute.amazonaws.com)
aws emr describe-cluster --cluster-id j-H8PK3O2MTK5W --region eu-west-3 --query "Cluster.MasterPublicDnsName" --output text

# Create SSH tunnel
ssh -i ~/.ssh/oc-p8-fruits-aws-ec2-key.pem -ND 5555 hadoop@ec2-XXX-XXX-XXX-XXX.eu-west-3.compute.amazonaws.com
#                                                          └────────────────────────┬────────────────────────┘
#                                                                                   │
#                                                         master node public DNS name

# Same command, as a oneliner:
ssh -i ~/.ssh/oc-p8-fruits-aws-ec2-key.pem -ND 5555 hadoop@$(aws emr describe-cluster --cluster-id j-H8PK3O2MTK5W --region eu-west-3 --query "Cluster.MasterPublicDnsName" --output text)
```

- `-N` : Do not execute a remote command. This is useful for just forwarding ports.
- `-D 5555` : Dynamic port forwarding. Creates SOCKS proxy on local port 5555.

#### 4. Log in to JupyterHub

- Find the URL in AWS EMR Web GUI. Should be `https://<master node public DNS>:9443` ie `https://ec2-XXX-XXX-XXX-XXX.eu-west-3.compute.amazonaws.com:9443`
- Enable FoxyProxy for that tab.
- Username: `jovyan`
- Password: `jupyter`

#### 5. Move or copy S3 `data/` directory into S3 `jupyter/jovyan/` directory

```bash
aws s3 cp s3://kirisakow-oc-p8-fruits-aws-emr/data/ \
s3://kirisakow-oc-p8-fruits-aws-emr/jupyter/jovyan/data/ \
--recursive
```

#### 6. Select PySpark as a kernel for your Jupyter notebook

### 4. Terminate a cluster

```bash
aws emr terminate-clusters --cluster-ids j-H8PK3O2MTK5W --region eu-west-3
```

### 5. Inspect logs

See above.

## Create a persistent EMR cluster for processing the full dataset `data/fruits/fruits-360_dataset/fruits-360/Test` in JupyterHub

### 0. Upload files in an S3 bucket

```bash
# Upload JupyterHub S3 persistence configuration file
aws s3 cp jupyter-s3-conf.json s3://kirisakow-oc-p8-fruits-aws-emr/

# Upload data sample
aws s3 cp \
data/fruits/fruits-360_dataset/fruits-360/Test \
s3://kirisakow-oc-p8-fruits-aws-emr/jupyter/jovyan/data/Test --recursive

# To resume an interrupted copying, use sync
aws s3 sync \
data/fruits/fruits-360_dataset/fruits-360/Test \
s3://kirisakow-oc-p8-fruits-aws-emr/jupyter/jovyan/data/Test
```

### 1. Create EMR Cluster

Here's recommended frugal EMR cluster configuration for processing `data/fruits/fruits-360_dataset/fruits-360/Test` sample (22.6k images, full dataset):

- Master: 1 × r5.xlarge (4 vCPU, 32GB RAM)
- Core: 3 × r5.xlarge (12 vCPU, 96GB RAM)
- Region: eu-west-3 (Paris) for RGPD compliance
- Estimated cost: ~$0.40-0.60/hour (spot pricing) or ~$1.00/hour (on-demand)

This gives 16 vCPUs and 128GB RAM total — more than sufficient for MobileNetV2 feature extraction on 22.6k images.

```bash
aws emr create-cluster \
--name "OC-P8-Fruits-Full-Jupyter" \
--release-label emr-6.15.0 \
--applications Name=Spark Name=Hadoop Name=JupyterHub \
--ec2-attributes KeyName=oc-p8-fruits-aws-ec2-key \
--instance-groups \
InstanceGroupType=MASTER,InstanceType=r5.xlarge,InstanceCount=1 \
InstanceGroupType=CORE,InstanceType=r5.xlarge,InstanceCount=3 \
--bootstrap-actions Path=s3://kirisakow-oc-p8-fruits-aws-emr/bootstrap-emr.sh,Name="Install Python packages" \
--configurations file://jupyter-s3-conf.json \
--log-uri s3://kirisakow-oc-p8-fruits-aws-emr/elasticmapreduce/logs/ \
--region eu-west-3 \
--no-auto-terminate \
--use-default-roles
```
