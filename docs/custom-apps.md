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
    "url": "https://user:password@git.example.com/project/repository.git",
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

- `url` needs to be http(s) git url with token/auth in case of private repo.
- add dependencies manually in `apps.json` e.g. add `payments` if you are installing `erpnext`
- use fork repo or branch for ERPNext in case you need to use your fork or test a PR.

### Build Image

```shell
buildah build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=PYTHON_VERSION=3.11.6 \
  --build-arg=NODE_VERSION=18.18.2 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/user/repo/custom:1.0.0 \
  --file=images/custom/Containerfile .
```

Note:

- Use `docker` instead of `buildah` as per your setup.
- `FRAPPE_PATH` and `FRAPPE_BRANCH` build args are optional and can be overridden in case of fork/branch or test a PR.
- Make sure `APPS_JSON_BASE64` variable has correct base64 encoded JSON string. It is consumed as build arg, base64 encoding ensures it to be friendly with environment variables. Use `jq empty apps.json` to validate `apps.json` file.
- Make sure the `--tag` is valid image name that will be pushed to registry. See section [below](#use-images) for remarks about its use.
- Change `--build-arg` as per version of Python, NodeJS, Frappe Framework repo and branch
- `.git` directories for all apps are removed from the image.

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
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-14 \
  --build-arg=PYTHON_VERSION=3.10.12 \
  --build-arg=NODE_VERSION=16.20.1 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --cache=true \
  --destination=ghcr.io/user/repo/custom:1.0.0 \
  --destination=ghcr.io/user/repo/custom:latest
```

More about [kaniko](https://github.com/GoogleContainerTools/kaniko)

### Use Images

On the [compose.yaml](../compose.yaml) replace the image reference to the `tag` you used when you built it. Then, if you used a tag like `custom_erpnext:staging` the `x-customizable-image` section will look like this:

```
x-customizable-image: &customizable_image
  image: custom_erpnext:staging
  pull_policy: never
```

The `pull_policy` above is optional and prevents `docker` to try to download the image when that one has been built locally.

Make sure image name is correct to be pushed to registry. After the images are pushed, you can pull them to servers to be deployed. If the registry is private, additional auth is needed.
