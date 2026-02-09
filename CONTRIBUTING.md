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

Documentation is written as markdown files, and placed inside the `docs/` directory. There are multiple sub directories under `docs/`, and be sure to place the `.md` file in the relevant sub directory if you are adding a new page.

If you want to include any image in the markdown file, place them in the `docs/images/` folder, and add a relative link in the `.md` file.

Frappe Docker also have a static site version of the documentation, which is made using the same `.md` files in the `docs/` directory. Build pipeline uses [VitePress](https://vitepress.dev/) as the Static Site builder, which is a JavaScript (TypeScript) static site builder. Note that to contribute to the documentation JavaScript or VitePress knowledge is not needed. Updating the `.md` file is enough.

The only additional content needed that is specific to VitePress, is a ['frontmatter'](https://vitepress.dev/guide/frontmatter#frontmatter). Frontmatter is like the `metadata` or `config` of that specific `.md` file, added at the beginning of the file and enclosed in `---`. For example, the frontmatter can include a friendly title, author, date of publishing, etc. A more detailed overview on what is frontmatter can be found in this [blog](https://www.seancdavis.com/posts/wtf-is-frontmatter/).

In this project only one field is used in the frontmatter. The `title` field. This is used to specify the title of the page shown in the sidebar, which is either same or a simpler and smaller version of the first heading `#` of the page. To add the required frontmatter just add a block at the beginning of the `.md` file as shown below

```yaml
---
title: <short-title-for-sidebar>
---
```

In case of any doubt, just refer to any of the existing `.md` file. Also checkout the Markdown section in the VitePress documentation to see some additional features supported by VitePress: [Markdown Extensions](https://vitepress.dev/guide/markdown). Be careful not to break compatibility with what is supported by GitHub markdown. It is recommended to keep the documentation simple.

If you want details on how to configure or update VitePress specific settings and and functionalities, refer this page: [Configuring VitePress](https://github.com/frappe/frappe_docker/blob/main/docs/08-reference/02-configuring-vitepress.md)

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.

# Maintenance

In case of new release of Debian. e.g. bullseye to bookworm. Change following files:

- `images/erpnext/Containerfile` and `images/custom/Containerfile`: Change the files to use new debian release, make sure new python version tag that is available on new debian release image. e.g. 3.9.9 (bullseye) to 3.9.17 (bookworm) or 3.10.5 (bullseye) to 3.10.12 (bookworm). Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.
- `images/bench/Dockerfile`: Change the files to use new debian release. Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.

Change following files on release of ERPNext

- `.github/workflows/build_stable.yml`: Add the new release step under `jobs` and remove the unmaintained one. e.g. In case v12, v13 available, v14 will be added and v12 will be removed on release of v14. Also change the `needs:` for later steps to `v14` from `v13`.
