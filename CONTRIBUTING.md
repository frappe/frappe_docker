# Contribution Guidelines

## Branches

* *master*:  images on the master branch are built monthly and with github action triggered by ERPNext release.
* *develop*: images on this branch are built daily and when PR is merged into develop.

# Pull Requests

Please **send all pull request exclusively to the *develop*** branch.
When the PR are merged, the merge will trigger the image build automatically.

Please test all PR as extensively as you can, considering that the software can be run in different modes:

* with docker-compose for production
* with or without Nginx proxy
* with VScode for testing environments

Every once in a while (or with monthly release) develop will be merged into master.

There is Github Action is configured on ERPNext repository. Whenever there is a ERPNext release it will trigger a build on master branch of frappe_docker repo to generate images for released version.

When a PR is sent, the images are built and all commands are tested.

If update or fixes to documentation are pushed use `[skip travis]` anywhere in commit message to skip travis.

## Reducing the number of branching and builds :evergreen_tree: :evergreen_tree: :evergreen_tree:

Please be considerate when pushing commits and opening PR for multiple branches, as the process of building images (triggered on push and PR branch push) uses energy and contributes to global warming.


# Documentation

Place relevant markdown file(s) in the `docs` directory and index them in README.md located at the root of repo.

# Wiki

Add alternatives that can be used optionally along with frappe_docker. Add articles to list on home page as well.

# Prerequisites to pass CI

### Check shell script format

Use the following script

```shell
./tests/check-format.sh
```

### Build images locally

Use the following commands

```shell
docker build -t frappe/frappe-socketio:edge -f build/frappe-socketio/Dockerfile .
docker build -t frappe/frappe-worker:develop -f build/frappe-worker/Dockerfile .
docker build -t frappe/erpnext-worker:edge -f build/erpnext-worker/Dockerfile .
docker build -t frappe/frappe-nginx:develop -f build/frappe-nginx/Dockerfile .
docker build -t frappe/erpnext-nginx:edge -f build/erpnext-nginx/Dockerfile .
```

### Test running docker containers

Use the following script

```shell
./tests/docker-test.sh
```
