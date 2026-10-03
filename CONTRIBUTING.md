# Contribution Guidelines

Before publishing a PR, run the checks relevant to your change. Test Docker builds locally when changing images or container behavior; for documentation changes, follow the [documentation contribution guide](docs/11-how-to/01-contribute-documentation.md#check-the-documentation).

On each PR that contains changes relevant to Docker builds, images are being built and tested in our CI (GitHub Actions).

> :evergreen_tree: Please be considerate when pushing commits and opening PR for multiple branches, as the process of building images uses energy and contributes to global warming.

## Pull Request Process

1. Run the relevant local checks before submitting
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

## Detailed Guidelines

A detailed form management guidelines are available in the [Fork Management](./docs/08-reference/03-fork-management.md)

## Documentation

Documentation lives in `docs/` and is published with VitePress from the same Markdown files. Follow [Diataxis](https://diataxis.fr/start-here/) to choose a page's purpose. The repository uses these four categories, in this order:

| Category      | Reader need                                                | Location               |
| ------------- | ---------------------------------------------------------- | ---------------------- |
| Tutorials     | Learn by completing a guided exercise with a clear outcome | `docs/10-tutorials/`   |
| How-to Guides | Accomplish a specific task using existing knowledge        | `docs/11-how-to/`      |
| Reference     | Look up precise facts, settings, interfaces, or defaults   | `docs/12-reference/`   |
| Explanation   | Understand concepts, relationships, and design choices     | `docs/13-explanation/` |

### Placement rules

- Choose the category by the reader's purpose, not just the topic or audience. Debugger setup and documentation contribution procedures are how-to guides; option tables are reference; architecture and tradeoffs are explanation.
- Keep one primary purpose per page. When a page mixes substantial instructions, reference tables, and background, split it into focused pages and link between them. A setup example is only a tutorial if it is designed as a guided learning exercise.
- Use descriptive kebab-case names with numeric prefixes, following the existing folders and files. The sidebar uses these prefixes to order pages and categories.

For Markdown, frontmatter, links, images, and CI requirements, follow [Contribute to the documentation](docs/11-how-to/01-contribute-documentation.md). Update documentation alongside feature and fix PRs whenever behavior changes.

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.

# Maintenance

In case of new release of Debian. e.g. bookworm to trixie. Change following files:

- `images/production/Containerfile` and `images/custom/Containerfile`: Change the files to use new debian release, make sure new python version tag that is available on new debian release image. Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.
- `images/bench/Dockerfile`: Change the files to use new debian release. Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.

Change following files on release of ERPNext

- `.github/workflows/core-build-stable.yml`: Add the new release step under `jobs` and remove the unmaintained one. e.g. In case v12, v13 available, v14 will be added and v12 will be removed on release of v14. Also change the `needs:` for later steps to `v14` from `v13`.
