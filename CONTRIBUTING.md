# Contribution Guidelines

Before publishing a PR, please test builds locally:

- with docker-compose for production,
- with and without nginx proxy,
- with VSCode for testing environments (only for frappe/bench image).

On each PR that contains changes relevant to Docker builds, images are being built and tested in our CI (GitHub Actions).

> :evergreen_tree: Please be considerate when pushing commits and opening PR for multiple branches, as the process of building images uses energy and contributes to global warming.

## Lint

We use `pre-commit` framework to lint the codebase before committing.
First, you need to install pre-commit with pip:

```shell
pip install pre-commit
```

Also you can use brew if you're on Mac:

```shell
brew install pre-commit
```

To setup _pre-commit_ hook, run:

```shell
pre-commit install
```

To run all the files in repository, run:

```shell
pre-commit run --all-files
```

## Build

```shell
# *...* — targets from docker-bake.hcl,
# e.g. bench-build, frappe-socketio-develop or erpnext-nginx-stable.
# Stable builds require GIT_BRANCH (e.g. v13.15.0), IMAGE_TAG (version-13), VERSION (13)
# environment variables set.
docker buildx bake -f docker-bake.hcl *...*
```

## Test

### Ping site

Lightweight test that just checks if site will be available after creation.

Frappe:

```shell
./tests/test-frappe.sh
```

ERPNext:

```shell
./tests/test-erpnext.sh
```

### Integration test

Tests frappe-bench-like commands, for example, `backup` and `restore`.

```shell
./tests/integration-test.sh
```

# Documentation

Place relevant markdown file(s) in the `docs` directory and index them in README.md located at the root of repo.

# Wiki

Add alternatives that can be used optionally along with frappe_docker. Add articles to list on home page as well.

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.
