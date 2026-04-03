---
title: Workflows
---

# Workflows

The wizard follows a simple order:

1. Create a stack.
2. Choose `single-host` or review `split-services`.
3. Select the apps and branches for the stack.
4. Generate the stack environment and render the Compose snapshot.
5. Build the custom image.
6. Start the stack.
7. Create or select the configured site.
8. Manage site apps or create a backup.

Stack actions are grouped around image and Compose lifecycle:

- `Apps` manages the stack app selection
- `Updates` handles app-branch changes and custom image tag updates
- `Site` handles site creation, backup, install, uninstall, and deletion
- `Start`, `Restart`, `Stop`, and `Delete` control the Compose lifecycle

Site app management is intentionally scoped to apps that are already part of the
stack image. The wizard does not try to install arbitrary apps that are not part
of the selected stack configuration.
