### Clone frappe_docker and switch directory

```shell
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

### Load custom apps through json

`apps.json` needs to be passed in as build arg environment variable.

```shell
export APPS_JSON='[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/frappe/payments",
    "branch": "version-15"
  },
  {
    "url": "https://{{ PAT }}@git.example.com/project/repository.git",
    "branch": "main"
  }
]'

export APPS_JSON_BASE64=$(echo ${APPS_JSON} | base64 -w 0)
```

You can also generate base64 string from json file:

```shell
export APPS_JSON_BASE64=$(base64 -w 0 /path/to/apps.json)
```

Note:

- `url` needs to be http(s) git url with personal access tokens without username eg:- http://{{PAT}}@github.com/project/repository.git in case of private repo.
- add dependencies manually in `apps.json` e.g. add `payments` if you are installing `erpnext`
- use fork repo or branch for ERPNext in case you need to use your fork or test a PR.

### Build Image

```shell
docker build \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/user/repo/custom:1.0.0 \
  --file=images/custom/Containerfile .
```

Note:

- Use `buildah` instead of `docker` as per your setup.
- Make sure `APPS_JSON_BASE64` variable has correct base64 encoded JSON string. It is consumed as build arg, base64 encoding ensures it to be friendly with environment variables. Use `jq empty apps.json` to validate `apps.json` file.
- Make sure the `--tag` is valid image name that will be pushed to registry. See section [below](#use-images) for remarks about its use.
- `.git` directories for all apps are removed from the image.

Customize these optional `--build-arg`s to use a different Frappe Framework repo and branch, or version of Python and NodeJS:

```shell
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=PYTHON_VERSION=3.11.9 \
  --build-arg=NODE_VERSION=18.20.2 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/user/repo/custom:1.0.0 \
  --file=images/custom/Containerfile .
```

### Push image to use in yaml files

Login to `docker` or `buildah`

```shell
buildah login
```

Push image

```shell
buildah push ghcr.io/user/repo/custom:1.0.0
```

### Use Kaniko

Following executor args are required. Example runs locally in docker container.
You can run it part of CI/CD or part of your cluster.

```shell
podman run --rm -it \
  -v "$HOME"/.docker/config.json:/kaniko/.docker/config.json \
  gcr.io/kaniko-project/executor:latest \
  --dockerfile=images/custom/Containerfile \
  --context=git://github.com/frappe/frappe_docker \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --cache=true \
  --destination=ghcr.io/user/repo/custom:1.0.0 \
  --destination=ghcr.io/user/repo/custom:latest
```

More about [kaniko](https://github.com/GoogleContainerTools/kaniko)

### Use Images

In the [compose.yaml](../compose.yaml), you can set the image name and tag through environment variables, making it easier to customize.

```yaml
x-customizable-image: &customizable_image
  image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-${ERPNEXT_VERSION:?No ERPNext version or tag set}}
  pull_policy: ${PULL_POLICY:-always}
```

The environment variables can be set in the shell or in the .env file as [setup-options.md](setup-options.md) describes.

- `CUSTOM_IMAGE`: The name of your custom image. Defaults to `frappe/erpnext` if not set.
- `CUSTOM_TAG`: The tag for your custom image. Must be set if `CUSTOM_IMAGE` is used. Defaults to the value of `ERPNEXT_VERSION` if not set.
- `PULL_POLICY`: The Docker pull policy. Defaults to `always`. Recommended set to `never` for local images, so prevent `docker` from trying to download the image when it has been built locally.
- `HTTP_PUBLISH_PORT`: The port to publish through no SSL channel. Default depending on deployment, it may be `80` if SSL activated or `8080` if not.
- `HTTPS_PUBLISH_PORT`: The secure port to publish using SSL. Default is `443`.

Make sure image name is correct to be pushed to registry. After the images are pushed, you can pull them to servers to be deployed. If the registry is private, additional auth is needed.

#### Example

If you built an image with the tag `ghcr.io/user/repo/custom:1.0.0`, you would set the environment variables as follows:

```bash
export CUSTOM_IMAGE='ghcr.io/user/repo/custom'
export CUSTOM_TAG='1.0.0'
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yaml
```
