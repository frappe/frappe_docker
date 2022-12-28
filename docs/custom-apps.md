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
    "url": "https://github.com/frappe/payments",
    "branch": "develop"
  },
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-14"
  },
  {
    "url": "https://user:password@git.example.com/project/repository.git",
    "branch": "main"
  }
]'
```

Note:

- `url` needs to be http(s) git url with token/auth in case of private repo.

### Build Image

```shell
buildah build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-14 \
  --build-arg=PYTHON_VERSION=3.10.5 \
  --build-arg=NODE_VERSION=16.18.0 \
  --build-arg=APPS_JSON=$APPS_JSON \
  --tag=ghcr.io/user/repo/custom:1.0.0 \
  --file=images/custom/Containerfile .
```

Note:

- Use `docker` instead of `buildah` as per your setup.
- Make sure `APPS_JSON` variable has correct JSON.
- Make sure the `--tag` is valid image name that will be pushed to registry.
- Change `--build-arg` as per version of Python, NodeJS, Frappe Framework repo and branch

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
  --build-arg=PYTHON_VERSION=3.10.5 \
  --build-arg=NODE_VERSION=16.18.0 \
  --build-arg=APPS_JSON=$APPS_JSON \
  --destination=ghcr.io/user/repo/custom:1.0.0
```

More about [kaniko](https://github.com/GoogleContainerTools/kaniko)

### Use Images

Make sure image name is correct to be pushed to registry. After the images are pushed, you can pull them to servers to be deployed. If the registry is private, additional auth is needed.
