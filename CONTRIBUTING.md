# Contribution Guidelines

Before publishing a PR, please test builds locally.

On each PR that contains changes relevant to Docker builds, images are being built and tested in our CI (GitHub Actions).

> :evergreen_tree: Please be considerate when pushing commits and opening PR for multiple branches, as the process of building images uses energy and contributes to global warming.

## Pull Request Process

1. Test builds locally before submitting
2. Follow conventional commit format
3. Update documentation if needed
4. Ensure all pre-commit checks pass
5. Reference related issues in PR description

## Commit Message Convention

We recommend [Conventional Commits](https://www.conventionalcommits.org/) for clear and semantic commit history.

Format: `<type>(<scope>): <description>`

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config, etc.)
- `ci`: CI/CD changes

**Examples:**

```
chore(deps): bump wkhtmltopdf version
fix(ci): correct buildx cache configuration
docs(contributing): add conventional commits guidelines
```

## Branch Naming

- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `docs/<description>` - Documentation updates

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

# Documentation

Place relevant markdown files in the `docs` directory and index them in README.md located at the root of repo.

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.

# Maintenance

In case of new release of Debian. e.g. bullseye to bookworm. Change following files:

- `images/erpnext/Containerfile` and `images/custom/Containerfile`: Change the files to use new debian release, make sure new python version tag that is available on new debian release image. e.g. 3.9.9 (bullseye) to 3.9.17 (bookworm) or 3.10.5 (bullseye) to 3.10.12 (bookworm). Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.
- `images/bench/Dockerfile`: Change the files to use new debian release. Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.

Change following files on release of ERPNext

- `.github/workflows/build_stable.yml`: Add the new release step under `jobs` and remove the unmaintained one. e.g. In case v12, v13 available, v14 will be added and v12 will be removed on release of v14. Also change the `needs:` for later steps to `v14` from `v13`.
