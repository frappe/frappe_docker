This is basic configuration for building images and testing custom apps that use Frappe.

You can see that there's four files in this folder:

- `backend.Dockerfile`,
- `frontend.Dockerfile`,
- `docker-bake.hcl`,
- `compose.override.yaml`.

Python code will `backend.Dockerfile`. JS and CSS (and other fancy frontend stuff) files will be built in `frontend.Dockerfile` if required and served from there.

`docker-bake.hcl` is reference file for cool new [Buildx Bake](https://github.com/docker/buildx/blob/master/docs/reference/buildx_bake.md). It helps to build images without having to remember all build arguments.

`compose.override.yaml` is [Compose](https://docs.docker.com/compose/compose-file/) override that replaces images from [main compose file](https://github.com/frappe/frappe_docker/blob/main/compose.yaml) so it would use your own images.

To get started, install Docker and [Buildx](https://github.com/docker/buildx#installing). Then copy all content of this folder (except this README) to your app's root directory. Also copy `compose.yaml` in the root of this repository.

Before the next step—to build images—replace "custom_app" with your app's name in `docker-bake.hcl`. After that, let's try to build:

```bash
FRAPPE_VERSION=... ERPNEXT_VERSION=... docker buildx bake
```

> 💡 We assume that majority of our users use ERPNext, that's why images in this tutorial are based on ERPNext images. If don't want ERPNext, change base image in Dockerfiles and remove ERPNEXT_VERSION from bake file.

If something goes wrong feel free to leave an issue.

To test if site works, setup `.env` file (check [example](<(https://github.com/frappe/frappe_docker/blob/main/example.env)>)) and run:

```bash
docker-compose -f compose.yaml -f overrides/compose.noproxy.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f custom_app/compose.override.yaml up -d
docker-compose exec backend \
  bench new-site 127.0.0.1 \
    --mariadb-root-password 123 \
    --admin-password admin \
    --install-app <Name of your app>
docker-compose restart backend
```

Cool! You just containerized your app!

## Installing multiple apps

Both backend and frontend builds contain `install-app` script that places app where it should be. Each call to script installs given app. Usage: `install-app [APP_NAME]`.

If you want to install an app from git, clone it locally, COPY in Dockerfile.
