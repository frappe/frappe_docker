---
title: Single Server Example
---

# Single Server Example (nginx-proxy + acme-companion)

This guide demonstrates a single-server setup using nginx-proxy and acme-companion for HTTPS. It is best for a small number of hostnames and a single bench. If you need multiple benches or advanced routing, use the Traefik-based example instead.

We will setup the following:

- Install Docker and Docker Compose v2 on a Linux server.
- Use nginx-proxy + acme-companion for HTTPS (Let's Encrypt).
- Install MariaDB and Redis via containers.
- Setup one project called `erpnext` with sites `erp.your-domain.com` and `crm.your-domain.com`.

## Requirements

- A server that can run Docker Engine **v23.0+** (recommended: 2 vCPU, 4 GB RAM, 50 GB SSD). The custom-image build below uses [BuildKit secrets](https://docs.docker.com/build/building/secrets/), which require BuildKit as the default builder (Docker Engine 23.0+).
- A public domain with DNS control.
- Two subdomains pointing to your server IP (A/AAAA records):
  - `erp.your-domain.com`
  - `crm.your-domain.com`
- Ports 80 and 443 reachable from the internet (required for Let's Encrypt HTTP-01).

### Install Docker

Docker can be installed on a variety of systems. The easiest way to do this is with the convenience script.

| Platform | Convenience script                                                                          | Using repository                                                                    |
| -------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| CentOS   | [Link](https://docs.docker.com/engine/install/centos/#install-using-the-convenience-script) | [Link](https://docs.docker.com/engine/install/centos/#install-using-the-repository) |
| Debian   | [Link](https://docs.docker.com/engine/install/debian/#install-using-the-convenience-script) | [Link](https://docs.docker.com/engine/install/debian/#install-using-the-repository) |
| Ubuntu   | [Link](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script) | [Link](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) |
| Fedora   | [Link](https://docs.docker.com/engine/install/fedora/#install-using-the-convenience-script) | [Link](https://docs.docker.com/engine/install/fedora/#install-using-the-repository) |

Then do the post-installation steps. This will ensure that the permissions are easier to use and that Docker will start up with the System. [Post-Installation Steps](https://docs.docker.com/engine/install/linux-postinstall/)

### Prepare

Clone `frappe_docker` and change the current working directory to the repo.

```shell
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

Create a configuration directory:

```shell
mkdir ~/gitops
```

## Optional: Build a custom image

If you need extra apps (beyond Frappe/ERPNext), build a custom image. Otherwise, skip this section and use the default images.

Create `apps.json` (each entry is a Git repo + branch):

```shell
cat > ~/gitops/apps.json <<'EOF'
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/frappe/payments",
    "branch": "version-16"
  }
]
EOF
```

Example for CRM only:

```shell
cat > ~/gitops/apps.json <<'EOF'
[
  {
    "url": "https://github.com/frappe/crm",
    "branch": "main"
  }
]
EOF
```

Build the image, passing `apps.json` as a [BuildKit secret](https://docs.docker.com/build/building/secrets/) so that private repo tokens are never stored in image layers. This requires **Docker Engine v23.0+**, where BuildKit is the default builder:

```shell
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=$HOME/gitops/apps.json \
  --tag=my-erpnext-prod-image:16.0.0 \
  --file=images/layered/Containerfile .
```

### Configure environment

Create an environment file for the bench:

```shell
cp example.env ~/gitops/erpnext.env
sed -i 's/DB_PASSWORD=123/DB_PASSWORD=changeit/g' ~/gitops/erpnext.env
echo 'NGINX_PROXY_HOSTS=erp.your-domain.com,crm.your-domain.com' >> ~/gitops/erpnext.env
echo 'LETSENCRYPT_EMAIL=admin@your-domain.com' >> ~/gitops/erpnext.env
```

Notes:

- Replace `changeit` with a strong password.
- Replace domains and email with your production values.
- `NGINX_PROXY_HOSTS` is a comma-separated list without spaces.
- If you built a custom image, add:

```shell
echo "CUSTOM_IMAGE=my-erpnext-prod-image" >> ~/gitops/erpnext.env
echo "CUSTOM_TAG=16.0.0" >> ~/gitops/erpnext.env
```

### Generate compose config

Create the rendered compose file:

```shell
docker compose --project-name erpnext \
  --env-file ~/gitops/erpnext.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml config > ~/gitops/erpnext.yaml
```

Start the stack:

```shell
docker compose --project-name erpnext -f ~/gitops/erpnext.yaml up -d
```

This starts MariaDB and Redis containers as part of the same stack.

### Create sites

```shell
# erp.your-domain.com
docker compose --project-name erpnext exec backend \
  bench new-site --mariadb-user-host-login-scope=% --db-root-password changeit --install-app erpnext --admin-password changeit erp.your-domain.com

# crm.your-domain.com
docker compose --project-name erpnext exec backend \
  bench new-site --mariadb-user-host-login-scope=% --db-root-password changeit --install-app erpnext --admin-password changeit crm.your-domain.com
```

### Notes

- Let's Encrypt requires ports 80 and 443 to be reachable from the internet.
- If you cannot expose these ports (LAN-only), omit `compose.nginxproxy-ssl.yaml` and use HTTP or a local TLS proxy like Caddy.
- Replace `changeit` with a strong DB root password and set a strong admin password per site.

### Site operations

Refer: [site operations](../04-operations/01-site-operations.md)

### Troubleshooting (ACME / certificates)

- **No certificate issued:** Verify DNS points to the server IP and ports 80/443 are reachable from the internet.
- **ACME errors in logs:** Check `acme-companion` logs for the exact challenge error.
- **Wrong hostname:** Ensure the domain is included in `NGINX_PROXY_HOSTS` and that you restarted the stack after edits.

---

**Back:** [Single Server Example (Traefik)](07-single-server-example.md)
