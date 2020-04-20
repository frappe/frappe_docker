## Prerequisites

- Access to Kubernetes cluster.
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [helm 3](https://helm.sh/)

## Install Ingress Controller

You can use Ingress Controller of your choice.
During Creation of new ingress, cert-manager annotations are used.

```shell
kubectl create namespace nginx-ingress
helm repo add nginx-stable https://helm.nginx.com/stable
helm repo update
helm install --namespace nginx-ingress nginx-controller nginx-stable/nginx-ingress
```

Notes:

- If apps from cluster need to access other apps hosted on same cluster by domain name, set `service.spec.externalTrafficPolicy` to `Cluster`. [Read More](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip)
- Once LoadBalancer Service is up, set Wildcard entry in your DNS Configuration

## Install Cert Manager

Cert Manager can be used to automate Letsencrypt certificate management.
During Creation of new ingress, cert-manager annotations are used.

- [Installation](https://cert-manager.io/docs/installation/kubernetes/)
- [Configure Issuer](https://cert-manager.io/docs/installation/kubernetes/#configuring-your-first-issuer)

## Prepare MariaDB

MariaDB options :
- Host separately (access by Private IP)
- Use managed service (e.g. AWS RDS)
- Install mariadb on kubernetes cluster

### Install MariaDB Helm chart

Download and edit values.yaml for frappe related mariadb config.

```
wget -c https://raw.githubusercontent.com/bitnami/charts/master/bitnami/mariadb/values-production.yaml

# Use editor of choice
code values-production.yaml
```

Set `rootUser.password` and `replication.password`.

```yaml
rootUser:
  password: super_secret_password

replication:
  password: super_secret_password
```

Change `master.config` as follows:

```yaml
  config: |-
    [mysqld]
    character-set-client-handshake=FALSE
    skip-name-resolve
    explicit_defaults_for_timestamp
    basedir=/opt/bitnami/mariadb
    plugin_dir=/opt/bitnami/mariadb/plugin
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    tmpdir=/opt/bitnami/mariadb/tmp
    max_allowed_packet=16M
    bind-address=0.0.0.0
    pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
    log-error=/opt/bitnami/mariadb/logs/mysqld.log
    character-set-server=utf8mb4
    collation-server=utf8mb4_unicode_ci

    [client]
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    default-character-set=utf8mb4
    plugin_dir=/opt/bitnami/mariadb/plugin

    [manager]
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
```

Change `slave.config` as follows:

```yaml
  config: |-
    [mysqld]
    character-set-client-handshake=FALSE
    skip-name-resolve
    explicit_defaults_for_timestamp
    basedir=/opt/bitnami/mariadb
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    tmpdir=/opt/bitnami/mariadb/tmp
    max_allowed_packet=16M
    bind-address=0.0.0.0
    pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
    log-error=/opt/bitnami/mariadb/logs/mysqld.log
    character-set-server=utf8mb4
    collation-server=utf8mb4_unicode_ci

    [client]
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    default-character-set=utf8mb4

    [manager]
    port=3306
    socket=/opt/bitnami/mariadb/tmp/mysql.sock
    pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
```

Create namespace and Install Helm Chart

```shell
kubectl create namespace mariadb

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install -n mariadb bitnami/mariadb -f values-production.yaml
```

## Prepare Shared Filesystem

Options are:

- [NFS](https://github.com/helm/charts/tree/master/stable/nfs-server-provisioner), recommended for small cluster
- Rook/Ceph, [Hyper-converged infrastructure](https://en.wikipedia.org/wiki/Hyper-converged_infrastructure)
    - [Quickstart](https://rook.io/docs/rook/v1.3/ceph-quickstart.html)
    - [Shared Filesystem](https://rook.io/docs/rook/v1.3/ceph-filesystem.html)

Note: After preparing storage, we get a `storageClass` which has `ReadWriteMany` `accessMode` available. e.g. `nfs` or `rook-cephfs`

## Install Frappe/ERPNext Helm Chart

```shell
kubectl create namespace erpnext
helm repo add erpnext https://helm.erpnext.com/repo
helm repo update

helm install frappe-bench-0001 --namespace erpnext erpnext-v12 \
    --set mariadbHost=mariadb.mariadb.svc.cluster.local \
    --set persistence.storageClass=rook-cephfs
```

## Site Operations

Following scripts take environment variables and generate a YAML file.
Generated YAML file can be modified as per need.

### Create MariaDB Root Password Secret

Generate Root Password. Export environment variable `BASE64_PASSWORD` and set it to base64 encoded mariadb root password.

```shell
# In case mariadb helm chart is installed
export BASE64_PASSWORD=$(kubectl get secret --namespace mariadb mariadb -o jsonpath="{.data.mariadb-root-password}")

./create-mariadb-root-password-secret.sh

kubectl -n erpnext apply -f mariadbrootpasswordsecret.yaml
```

### Create New Site

```
export SITE_NAME=mysite.example.com
export DB_ROOT_USER=root
export ADMIN_PASSWORD=$(cat /tmp/site_admin_password)
export SITES_PVC=erpnext-v12
export VERSION=v12

./create-new-site-job.sh

kubectl -n erpnext apply -f newsitejob-mysite.example.com-1587301207.yaml
```

Note: Site admin password is set in `/tmp/site_admin_password` file.

### Create New Ingress

```shell
export SITE_NAME=mysite.example.com
export INGRESS_NAME=$SITE_NAME
export FRAPPE_SERVICE=erpnext-v12
export TLS_SECRET_NAME=mysite-example-com-tls

./create-new-site-ingress.sh

kubectl -n erpnext apply -f newsiteingress_mysite.example.com.yaml
```

### Backup New Site

```shell
export SITES_PVC=erpnext-v12
export VERSION=v12

./create-backup-sites-job.sh

kubectl -n erpnext apply -f backupsitesjob-1587303964.yaml
```

### Migrate Sites

```shell
export SITES_PVC=erpnext-v12
export VERSION=v12

./create-migrate-sites-job.sh

kubectl -n erpnext apply -f migratesitesjob-1587306818.yaml
```
