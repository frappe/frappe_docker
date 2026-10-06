# Deploying Multiple Frappe Apps using Docker

This guide explains step-by-step how to spin up a fully customized Frappe environment containing **Frappe Framework**, **ERPNext**, **HRMS**, **Frappe CRM**, and **Frappe Helpdesk** inside a single Docker image. 

It explains how to transition from the default `pwd.yml` (Play-with-Docker template) to a robust custom `compose-all.yaml` setup.

---

## Step 1: Clone `frappe_docker`

The official [frappe_docker](https://github.com/frappe/frappe_docker) repository contains all the necessary boilerplate (Nginx configurations, Dockerfiles, entrypoint bash scripts) to containerize Frappe's complex architecture.

```bash
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

## Step 2: Define Apps to Install (`apps.json`)

Historically, the list of apps was passed as a Base64-encoded string (`APPS_JSON_BASE64`) to the Docker build argument. **This approach is now deprecated.** 

The new `images/custom/Containerfile` securely reads the apps list from a Docker **secret**. 

Create a file named `apps.json` in the root of the repository:

```json
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-15"},
  {"url": "https://github.com/frappe/hrms", "branch": "version-15"},
  {"url": "https://github.com/frappe/crm", "branch": "main"},
  {"url": "https://github.com/frappe/helpdesk", "branch": "main"}
]
```

> [!NOTE]
> Older apps like `erpnext` and `hrms` synchronize their versions with the Frappe Framework (`version-15`). Newer, unbundled apps like `crm` and `helpdesk` do not follow this versioning scheme and should pull from their `main` branch.

## Step 3: Create `compose-all.yaml`

Copy the default `pwd.yml` to a new file named `compose-all.yaml`. We will modify it to support building our custom image instead of pulling a pre-built one.

### 3.1. Configure the `x-custom-build` block
At the top of the file, define the build block. Notice two critical changes:
1. **`NODE_VERSION`**: It is set to `20.19.0`. The newer UI apps (CRM, Helpdesk) require Node `>=20.19.0`, but compiling older native extensions for the core Frappe app fails on Node 22. Node `20.19.0` hits the perfect sweet spot for compatibility.
2. **`secrets`**: We pass `apps_json` as a secret instead of using arguments.

```yaml
x-custom-build: &custom_build
  context: .
  dockerfile: images/custom/Containerfile
  args:
    FRAPPE_PATH: https://github.com/frappe/frappe
    FRAPPE_BRANCH: version-15
    PYTHON_VERSION: 3.11.9
    NODE_VERSION: 20.19.0
  secrets:
    - apps_json
```

### 3.2. Apply dynamic image tags and the build block
For **every** frappe-related service (`backend`, `configurator`, `create-site`, `frontend`, `queue-long`, `queue-short`, `scheduler`, `websocket`), update the image block to allow dynamic version tagging, and attach the `build` block.

```yaml
  backend:
    build: *custom_build
    image: agency-erp-image:${IMAGE_TAG:-latest}
    # ... rest of the service
```

### 3.3. Update the `create-site` command
Modify the `create-site` service's command to explicitly install all the apps into your site upon creation:

```yaml
  create-site:
    # ...
    command:
      - >
        # ... wait scripts ...
        if [ -d "sites/frontend" ]; then
          echo "Site frontend already exists, checking for missing apps...";
          for app in `cat sites/apps.txt | grep -v frappe`; do
            bench --site frontend list-apps | grep -q $$app || bench --site frontend install-app $$app;
          done
        else
          INSTALL_ARGS="";
          for app in `cat sites/apps.txt | grep -v frappe`; do INSTALL_ARGS="$$INSTALL_ARGS --install-app $$app"; done;
          bench new-site --mariadb-user-host-login-scope='%' \
            --admin-password=admin \
            --db-root-username=root \
            --db-root-password=admin \
            $$INSTALL_ARGS \
            --set-default frontend;
        fi;
```

### 3.4. Define the secret
At the very bottom of the file, define where the secret file is located:

```yaml
secrets:
  apps_json:
    file: ./apps.json
```

---

## Step 4: Build the Custom Image

Now you are ready to compile the apps into the Docker image. You can specify a custom tag (e.g., `v1`) using the `IMAGE_TAG` environment variable. Passing `COMPOSE_BAKE=true` significantly speeds up the build by building layers concurrently.

```bash
IMAGE_TAG=v1 COMPOSE_BAKE=true docker compose -f compose-all.yaml build --no-cache
```

> [!WARNING]
> This step will take 15-30 minutes as it downloads the apps, compiles Node.js assets (Vue frontend), and installs Python dependencies.

---

## Step 5: Start the Cluster & Create the Site

Once the build finishes successfully, start the cluster in the background:

```bash
IMAGE_TAG=v1 docker compose -f compose-all.yaml up -d
```

Finally, execute the site creation script. This sets up the MariaDB database tables and triggers the `--install-app` flags we configured earlier.

```bash
IMAGE_TAG=v1 docker compose -f compose-all.yaml up create-site
```

Congratulations! You now have a unified cluster running the classic Frappe ERP backend alongside the modern, unbundled frontend apps.
