---
title: Workflows
---

# Workflows

The wizard follows a simple order:

1. Create a stack.
2. Choose `single-host` or `split-services`.
3. Select the apps and branches for the stack.
4. Generate the stack environment and render the Compose snapshot.
5. Build the custom image.
6. Start the stack.
7. Continue into site actions when the selected workflow supports them.

Stack actions are grouped around image and Compose lifecycle:

- `Apps` manages the stack app selection
- `Updates` handles app-branch changes and custom image tag updates
- `Site` handles site creation, backup, install, uninstall, and deletion
- `Start`, `Restart`, `Stop`, and `Delete` control the Compose lifecycle

Site app management is intentionally scoped to apps that are already part of the
stack image. The wizard does not try to install arbitrary apps that are not part
of the selected stack configuration.

Internally, the stack app contract is now handled through `jq` instead of
line-based `awk` parsing. This is intended to keep app selection and branch
update behavior the same while making the JSON processing more robust in the
background. The generated `metadata.json` and `apps.json` files are still meant
to look the same to users.

For the split-services path, see
[Split Services](./05-split-services.md). That page explains the intended flow
in simple terms and shows where the proxy, application, database, and Redis
choices fit into the setup.
