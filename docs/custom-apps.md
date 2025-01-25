### Load custom apps through apps.json file

Base64 encoded string of `apps.json` file needs to be passed in as build arg environment variable.

Create the following `apps.json` file:

```json
[
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
]
```

Note:

- The `url` needs to be http(s) git url with personal access tokens without username eg:- `http://{{PAT}}@github.com/project/repository.git` in case of private repo.
- Add dependencies manually in `apps.json` e.g. add `erpnext` if you are installing `hrms`.
- Use fork repo or branch for ERPNext in case you need to use your fork or test a PR.

Generate base64 string from json file:

```shell
export APPS_JSON_BASE64=$(base64 -w 0 /path/to/apps.json)
```

Test the Previous Step: Decode the Base64-encoded Environment Variable

To verify the previous step, decode the `APPS_JSON_BASE64` environment variable (which is Base64-encoded) into a JSON file. Follow the steps below:

1. Use the following command to decode and save the output into a JSON file named apps-test-output.json:

```shell
echo -n ${APPS_JSON_BASE64} | base64 -d > apps-test-output.json
```

2. Open the apps-test-output.json file to review the JSON output and ensure that the content is correct.

### Clone frappe_docker and switch directory

```shell
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

### Configure build

Common build args.

- `FRAPPE_PATH`, customize the source repo for frappe framework. Defaults to `https://github.com/frappe/frappe`
- `FRAPPE_BRANCH`, customize the source repo branch for frappe framework. Defaults to `version-15`.
- `APPS_JSON_BASE64`, correct base64 encoded JSON string generated from `apps.json` file.

Notes

- Use `buildah` or `docker` as per your setup.
- Make sure `APPS_JSON_BASE64` variable has correct base64 encoded JSON string. It is consumed as build arg, base64 encoding ensures it to be friendly with environment variables. Use `jq empty apps.json` to validate `apps.json` file.
- Make sure the `--tag` is valid image name that will be pushed to registry. See section [below](#use-images) for remarks about its use.
- `.git` directories for all apps are removed from the image.

### Quick build image

This method uses pre-built `frappe/base:${FRAPPE_BRANCH}` and `frappe/build:${FRAPPE_BRANCH}` image layers which come with required Python and NodeJS runtime. It speeds up the build time.

It uses `images/layered/Containerfile`.

```shell
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/user/repo/custom:1.0.0 \
  --file=images/layered/Containerfile .
```

### Custom build image

This method builds the base and build layer every time, it allows to customize Python and NodeJS runtime versions. It takes more time to build.

It uses `images/custom/Containerfile`.

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

Custom build args,

- `PYTHON_VERSION`, use the specified python version for base image. Default is `3.11.6`.
- `NODE_VERSION`, use the specified nodejs version, Default `18.18.2`.
- `DEBIAN_BASE` use the base Debian version, defaults to `bookworm`.
- `WKHTMLTOPDF_VERSION`, use the specified qt patched `wkhtmltopdf` version. Default is `0.12.6.1-3`.
- `WKHTMLTOPDF_DISTRO`, use the specified distro for debian package. Default is `bookworm`.

### Push image to use in yaml files

Login to `docker` or `buildah`

```shell
docker login
```

Push image

```shell
docker push ghcr.io/user/repo/custom:1.0.0
```

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

Make sure the image name is correct before pushing to the registry. After the images are pushed, you can pull them to servers to be deployed. If the registry is private, additional auth is needed.

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
