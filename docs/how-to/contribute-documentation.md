---
title: Contribute to the Documentation
---

# Contribute to the documentation

Use this guide to add, correct, or migrate documentation in this repository. You need a Git checkout and a Markdown editor; JavaScript knowledge is not required to edit the documentation. To preview and build the site, use Node.js 24 and the pnpm version pinned in `docs/package.json`, as in the documentation CI workflow.

## Choose a focused change

Read the repository's [contribution guidelines](https://github.com/frappe/frappe_docker/blob/main/CONTRIBUTING.md#documentation) for the documentation types, placement rules, and migration policy.

Choose one reader need and check for existing coverage before adding a page. Make a `docs/<description>` branch from current upstream `main`. For new or migrated pages, use the appropriate `tutorials/`, `how-to/`, `reference/`, or `explanation/` directory under `docs/`. A small correction to an existing page can stay at its current path.

This contributor procedure belongs in How-to Guides because it helps you complete a task. A contributor audience alone does not make a page Reference.

## Write the page and connect it

1. Give the page a descriptive, unnumbered kebab-case filename and one main heading. Add a short sidebar title in YAML [frontmatter](https://vitepress.dev/guide/frontmatter):

   ```yaml
   ---
   title: Short Sidebar Title
   ---
   ```

2. Use simple Markdown that works on GitHub and in VitePress. See [VitePress Markdown extensions](https://vitepress.dev/guide/markdown) when needed, keeping GitHub rendering in mind.
3. Put article images in `docs/images/` and use relative paths, for example `![Diagram](../images/diagram.png)` from a page one directory below `docs/`. Reserve `docs/public/` for site assets.
4. Link to other documentation with relative `.md` paths, including heading fragments when useful. Update the relevant category index and any incoming links when adding or moving content. The sidebar is generated from the files and their titles; category order is set in `docs/.vitepress/config.mts`.
5. State prerequisites, expected results, and any destructive effects for runnable instructions. Check commands against the current repository and test the affected procedure where practical. Record anything you could not verify in the PR.

For site configuration details, see [Configuring VitePress](../08-reference/02-configuring-vitepress.md).

## Validate the change

From the repository root, run the repository's pre-commit checks after [setting up pre-commit](https://github.com/frappe/frappe_docker/blob/main/CONTRIBUTING.md#lint):

```sh
pre-commit run --all-files
```

Install the locked documentation dependencies and build the site:

```sh
cd docs
pnpm install --frozen-lockfile
pnpm docs:build
pnpm docs:preview
```

Open the preview URL printed in the terminal. Check the affected pages, sidebar order, images, and links. Also check relative links and heading fragments in the Markdown source; a successful site build alone does not verify every link or command. Use `pnpm docs:dev` for live preview while editing.

## Submit for review

Use a conventional commit such as `docs: clarify documentation placement`. In the PR, explain the reader need, the chosen documentation type, any source pages consolidated or moved, and the checks performed. Reference [issue #1843](https://github.com/frappe/frappe_docker/issues/1843) for structure or migration work.

Keep unrelated corrections and further migrations for separate contributions. The documentation workflow builds affected PRs; publication follows changes merged to upstream `main`.
