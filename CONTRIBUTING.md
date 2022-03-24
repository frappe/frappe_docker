# Contribution Guidelines

Before publishing a PR, please test builds locally.

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

We use [Docker Buildx Bake](https://docs.docker.com/engine/reference/commandline/buildx_bake/). To build the images, run command below:

```shell
FRAPPE_VERSION=... ERPNEXT_VERSION=... docker buildx bake <targets>
```

Available targets can be found in `docker-bake.hcl`.

## Test

We use [pytest](https://pytest.org) for our integration tests.

Install Python test requirements:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
```

Run pytest:

```shell
pytest
```

> We also have `requirements-dev.txt` file that contains development requirements for backend image (you can find it in `images/worker/` directory).

# Documentation

Place relevant markdown files in the `docs` directory and index them in README.md located at the root of repo.

# Wiki

Add alternatives that can be used optionally along with frappe_docker. Add articles to list on home page as well.

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.
