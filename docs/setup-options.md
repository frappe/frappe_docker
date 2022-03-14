# Containerized Production Setup

Make sure you've cloned this repository and switch to the directory before executing following commands.

Commands will generate YAML as per the environment for setup.

## Setup Environment Variables

Copy the example docker environment file to `.env`:

```sh
cp example.env .env
```

Note: To know more about environment variable [read here](./images-and-compose-files#configuration). Set the necessary variables in the `.env` file.

## Generate docker-compose.yml for variety of setups

### Setup Frappe without proxy and external MariaDB and Redis

```sh
# Generate YAML
docker-compose -f compose.yaml -f overrides/compose.noproxy.yaml config > ~/gitops/docker-compose.yml

# Start containers
docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

### Setup ERPNext with proxy and external MariaDB and Redis

```sh
# Generate YAML
docker-compose -f compose.yaml \
  -f overrides/compose.proxy.yaml \
  -f overrides/compose.erpnext.yaml \
  config > ~/gitops/docker-compose.yml

# Start containers
docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

### Setup Frappe using containerized MariaDB and Redis with Letsencrypt certificates.

```sh
# Generate YAML
docker-compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yml

# Start containers
docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

### Setup ERPNext using containerized MariaDB and Redis with Letsencrypt certificates.

```sh
# Generate YAML
docker-compose -f compose.yaml \
  -f overrides/compose.erpnext.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yml

# Start containers
docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

Notes:

- Make sure to replace `<project-name>` with the desired name you wish to set for the project.
- This setup is not to be used for development. A complete development environment is available [here](../development)

## Updating Images

Switch to the root of the `frappe_docker` directory before running the following commands:

```sh
# Update environment variables ERPNEXT_VERSION and FRAPPE_VERSION
nano .env

# Pull new images
docker-compose -f compose.yaml \
  -f overrides/erpnext.yaml \
  # ... your other overrides
  config > ~/gitops/docker-compose.yml

docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml pull

# Restart containers
docker-compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

To migrate sites refer [site operations](./site-operations.md#migrate-site)
