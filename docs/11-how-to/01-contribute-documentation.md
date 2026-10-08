---
title: Contribute to the Documentation
---

# Contribute to the documentation

The documentation lives in Markdown files in `docs/`. The same files are also published as a website using VitePress. To update the documentation, edit the Markdown files; you do not need JavaScript or VitePress knowledge or a local website setup. CI builds the website from PRs that change `docs/` to check that the documentation builds correctly.

Include documentation changes in feature and fix PRs when they affect how people use the project; documentation-only improvements are also welcome.

## Choose the right page

Update existing coverage where appropriate. For a new page, choose a directory by the reader's purpose:

- `docs/10-tutorials/`: a guided exercise that teaches a skill.
- `docs/11-how-to/`: steps to complete a specific task.
- `docs/12-reference/`: technical facts, settings, and defaults to look up.
- `docs/13-explanation/`: background, concepts, and design choices.

Keep the page focused on that purpose and link to related material instead of repeating it. See the [documentation contribution guidelines](https://github.com/frappe/frappe_docker/blob/main/CONTRIBUTING.md#documentation) for the placement policy.

Category indexes should briefly explain their purpose rather than list every document.

## Write Markdown that works on GitHub and the site

1. Follow the directory's numbered kebab-case naming convention, for example `01-contribute-documentation.md`. The sidebar orders folders and files by name.
2. Start the file with YAML [frontmatter](https://vitepress.dev/guide/frontmatter) containing a short sidebar title. After the frontmatter, add one main `#` heading:

   ```markdown
   ---
   title: Short Sidebar Title
   ---

   # Main Page Heading
   ```

3. Use `##` and `###` headings to organize sections, backticks for inline code, and fenced code blocks with a language such as `sh` for commands. Keep Markdown compatible with GitHub; use [VitePress Markdown extensions](https://vitepress.dev/guide/markdown) only when they preserve that compatibility.
4. Link to documentation using relative `.md` paths, for example `[Environment variables](../02-setup/04-env-variables.md)`. A `#heading-fragment` can link to a specific section. Check that the target file and heading exist.
5. Put article images in `docs/images/` and use relative paths with descriptive alternative text, for example `![Service diagram](../images/service-diagram.png)`. Reserve `docs/public/` for site assets.
6. State prerequisites and expected results for instructions. Clearly identify destructive operations. Keep commands, configuration names, and examples consistent with the repository's behavior.

## Check the documentation

Review the Markdown preview in your editor or on GitHub. Check heading levels, code fences, tables, links, and images.

Follow the repository's existing [pre-commit requirements](https://github.com/frappe/frappe_docker/blob/main/CONTRIBUTING.md#lint) and [commit conventions](https://github.com/frappe/frappe_docker/blob/main/CONTRIBUTING.md#commit-message-convention). Documentation changes accompanying a feature or fix belong with that change; they do not require a separate documentation branch or PR.

The PR must pass the lint and documentation build checks. CI builds the site and reports errors such as broken page links or invalid Markdown syntax. If a check fails, read its log, correct the affected source, and push the fix. CI does not verify every heading fragment, so check those yourself.

Maintainers working on site configuration can use the specialist [Configuring VitePress](../08-reference/02-configuring-vitepress.md) guide.
