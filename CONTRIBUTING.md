# Contribution Guidelines

Before publishing a PR, run the checks relevant to your change. Test Docker builds locally when changing images or container behavior; for documentation changes, follow the [documentation validation steps](docs/how-to/contribute-documentation.md#validate-the-change).

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

Documentation lives in `docs/` and is published with VitePress from the same Markdown files. Follow [Diataxis](https://diataxis.fr/start-here/) to choose a page's purpose. The repository uses these four categories, in this order, following the discussion in [issue #1843](https://github.com/frappe/frappe_docker/issues/1843):

| Category      | Reader need                                                | Location for new or migrated pages |
| ------------- | ---------------------------------------------------------- | ---------------------------------- |
| Tutorials     | Learn by completing a guided exercise with a clear outcome | `docs/tutorials/`                  |
| How-to Guides | Accomplish a specific task using existing knowledge        | `docs/how-to/`                     |
| Reference     | Look up precise facts, settings, interfaces, or defaults   | `docs/reference/`                  |
| Explanation   | Understand concepts, relationships, and design choices     | `docs/explanation/`                |

### Placement rules

- Choose the category by the reader's purpose, not just the topic or audience. Debugger setup and documentation contribution procedures are how-to guides; option tables are reference; architecture and tradeoffs are explanation.
- Keep one primary purpose per page. When a page mixes substantial instructions, reference tables, and background, split it into focused pages and link between them. A setup example is only a tutorial if it is designed as a guided learning exercise.
- Use descriptive, unnumbered kebab-case filenames for new and migrated pages. Keep the four-category order in navigation configuration rather than filename prefixes.
- Keep `README.md` as repository orientation and `CONTRIBUTING.md` as the contribution entry point and policy. Category indexes provide navigation; `docs/images/`, `docs/public/`, and `docs/.vitepress/` support the documentation rather than forming additional content categories.

### Incremental migration

Apply these rules to new pages. Existing numbered topic folders and mixed pages remain usable during migration; a focused correction does not require relocating the whole page.

Migrate one coherent topic at a time. Check its content against the current repository, preserve useful information, and consolidate duplicates into a canonical page with links from related pages. Do not treat age alone as evidence that a page is obsolete. Discuss uncertain removals with maintainers before deleting material.

When moving or splitting a page, update its incoming links, heading fragments, category indexes, and any affected navigation in the same change. Old URLs do not need compatibility stubs or redirects. Keep current internal links valid and list the source and destination pages in the PR.

Publish links only to available content. Do not add empty guide placeholders or present unmigrated pages as completed rewrites. Broad content fixes, further relocations, and curated reader journeys can follow in separate contributions. See Diataxis guidance on [working incrementally](https://diataxis.fr/how-to-use-diataxis/).

For Markdown, frontmatter, images, preview, and validation steps, follow [Contribute to the documentation](docs/how-to/contribute-documentation.md). For site configuration, see [Configuring VitePress](docs/08-reference/02-configuring-vitepress.md).

# Frappe and ERPNext updates

Each Frappe/ERPNext release triggers new stable images builds as well as bump to helm chart.

# Maintenance

In case of new release of Debian. e.g. bullseye to bookworm. Change following files:

- `images/erpnext/Containerfile` and `images/custom/Containerfile`: Change the files to use new debian release, make sure new python version tag that is available on new debian release image. e.g. 3.9.9 (bullseye) to 3.9.17 (bookworm) or 3.10.5 (bullseye) to 3.10.12 (bookworm). Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.
- `images/bench/Dockerfile`: Change the files to use new debian release. Make sure apt-get packages and wkhtmltopdf version are also upgraded accordingly.

Change following files on release of ERPNext

- `.github/workflows/core-build-stable.yml`: Add the new release step under `jobs` and remove the unmaintained one. e.g. In case v12, v13 available, v14 will be added and v12 will be removed on release of v14. Also change the `needs:` for later steps to `v14` from `v13`.
