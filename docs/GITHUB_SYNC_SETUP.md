# 🔄 GitHub DAG Sync Setup Guide

This guide explains how to set up automatic DAG synchronization from GitHub to Airflow.

## 📋 Overview

The Airflow deployment uses **git-sync** sidecar containers to automatically pull DAGs from a GitHub repository. This enables:

- **Version Control**: All DAGs are tracked in Git
- **Collaboration**: Team members can contribute DAGs via Pull Requests
- **Automation**: Changes are automatically deployed within 60 seconds
- **Rollback**: Easy to revert to previous versions

## 🚀 Quick Setup

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it something like `mlops-workshop-dags`
3. Make it **Public** (or Private with SSH key setup)

### Step 2: Push DAGs to GitHub

```powershell
# Navigate to the DAGs template folder
cd F:\MLOPS-Fundamentals\mlops-lab-workshop\github-dags-repo

# Initialize Git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: MLOps Workshop DAGs"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/mlops-workshop-dags.git

# Push to GitHub
git push -u origin main
```

### Step 3: Enable Git-Sync in Airflow

```powershell
# Run the enable script with your repo URL
.\scripts\enable-git-sync.ps1 -GitRepoUrl "https://github.com/YOUR_USERNAME/mlops-workshop-dags.git"
```

### Step 4: Verify Sync

```powershell
# Check git-sync logs
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync

# Check if DAGs appear in Airflow UI
# Open http://localhost:8080
```

---

## 📁 Repository Structure

Your GitHub repository should have this structure:

```
mlops-workshop-dags/
├── dags/                          # DAG files go here
│   ├── 01_data_ingestion.py
│   ├── 02_feature_engineering.py
│   ├── 03_model_training.py
│   ├── 04_model_evaluation.py
│   └── 05_full_pipeline.py
├── .gitignore
└── README.md
```

**Important**: The `dags/` folder name must match the `DagsFolder` parameter.

---

## 🔧 Configuration Options

### Basic Configuration (Public Repo)

```powershell
.\scripts\enable-git-sync.ps1 `
    -GitRepoUrl "https://github.com/your-org/your-dags.git" `
    -Branch "main" `
    -DagsFolder "dags"
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-GitRepoUrl` | Required | Full HTTPS URL to your GitHub repository |
| `-Branch` | `main` | Branch to sync from |
| `-DagsFolder` | `dags` | Folder containing DAG files in the repo |
| `-ClusterName` | `mlops-workshop` | Kind cluster name |

---

## 🔐 Private Repository Setup

For private repositories, you need to set up SSH authentication.

### Step 1: Generate SSH Key

```powershell
# Generate SSH key pair
ssh-keygen -t ed25519 -C "airflow-git-sync" -f ./git-sync-key -N ""

# This creates:
# - git-sync-key (private key)
# - git-sync-key.pub (public key)
```

### Step 2: Add Public Key to GitHub

1. Go to your GitHub repository → Settings → Deploy Keys
2. Click "Add deploy key"
3. Title: `Airflow Git-Sync`
4. Paste contents of `git-sync-key.pub`
5. Check "Allow write access" (optional)
6. Click "Add key"

### Step 3: Create Kubernetes Secret

```powershell
# Create secret with private key
kubectl create secret generic git-sync-ssh-key `
    --from-file=ssh=./git-sync-key `
    --namespace airflow

# Verify secret
kubectl get secret git-sync-ssh-key -n airflow
```

### Step 4: Update Git-Sync ConfigMap

Edit `k8s/airflow/airflow-git-sync-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: git-sync-config
  namespace: airflow
data:
  GIT_SYNC_REPO: "git@github.com:your-org/your-private-dags.git"
  GIT_SYNC_BRANCH: "main"
  GIT_SYNC_SSH: "true"
  GIT_SYNC_DEPTH: "1"
  GIT_SYNC_ROOT: "/git"
  GIT_SYNC_DEST: "repo"
  GIT_SYNC_WAIT: "60"
```

### Step 5: Update Deployment

The scheduler/webserver deployments need to mount the SSH secret:

```yaml
volumes:
  - name: git-sync-ssh
    secret:
      secretName: git-sync-ssh-key
      defaultMode: 0400

volumeMounts:
  - name: git-sync-ssh
    mountPath: /etc/git-secret
    readOnly: true
```

---

## 🔍 Troubleshooting

### DAGs Not Appearing

1. **Check git-sync logs**:
```powershell
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync
```

2. **Check scheduler logs for import errors**:
```powershell
kubectl logs deployment/airflow-scheduler -n airflow -c scheduler | Select-String -Pattern "error|Error|ERROR"
```

3. **Verify repository URL**:
```powershell
kubectl get configmap git-sync-config -n airflow -o yaml
```

### Sync Delay

Git-sync checks for updates every 60 seconds by default. You can reduce this:

```yaml
data:
  GIT_SYNC_WAIT: "30"  # Check every 30 seconds
```

### Permission Denied (Private Repo)

1. Verify SSH key is in the secret:
```powershell
kubectl get secret git-sync-ssh-key -n airflow -o yaml
```

2. Check deploy key is added to GitHub repository

3. Verify secret is mounted in pod:
```powershell
kubectl exec deployment/airflow-scheduler -n airflow -c git-sync -- ls -la /etc/git-secret/
```

### Branch Not Found

Make sure the branch exists and matches exactly:
```powershell
# Check remote branches
git ls-remote --heads https://github.com/your-org/your-dags.git
```

---

## 📊 Monitoring Sync Status

### Check Last Sync Time

```powershell
kubectl exec deployment/airflow-scheduler -n airflow -c git-sync -- cat /git/repo/.git/FETCH_HEAD
```

### Watch Sync Logs

```powershell
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync -f
```

### Verify DAGs Directory

```powershell
kubectl exec deployment/airflow-scheduler -n airflow -c scheduler -- ls -la /git/repo/dags/
```

---

## 🔄 Updating DAGs

### Making Changes

1. Edit DAG files locally
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Update DAGs"
git push
```
3. Wait 60 seconds for sync
4. Verify in Airflow UI

### Force Sync

To force an immediate sync, restart the scheduler:
```powershell
kubectl rollout restart deployment/airflow-scheduler -n airflow
```

---

## 📝 Best Practices

1. **Use branches for development**: Create feature branches, test in dev, merge to main
2. **Add CI/CD**: Use GitHub Actions to validate DAG syntax before merge
3. **Tag releases**: Use Git tags for production releases
4. **Document DAGs**: Add docstrings to all DAGs
5. **Use requirements file**: If DAGs need additional packages, add them to requirements

### Example GitHub Action for DAG Validation

```yaml
# .github/workflows/validate-dags.yml
name: Validate DAGs

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install apache-airflow pandas scikit-learn mlflow boto3
      
      - name: Validate DAG syntax
        run: |
          python -c "
          import sys
          from airflow.models import DagBag
          dagbag = DagBag(dag_folder='dags/', include_examples=False)
          if dagbag.import_errors:
              for file, error in dagbag.import_errors.items():
                  print(f'Error in {file}: {error}')
              sys.exit(1)
          print(f'Successfully validated {len(dagbag.dags)} DAGs')
          "
```

---

## 🎓 Workshop Exercise

1. Fork the template repository
2. Make a small change to a DAG (e.g., update description)
3. Commit and push
4. Watch the sync happen in real-time
5. Verify the change in Airflow UI

---

**Happy Syncing! 🔄**

