---
title: Easy Docker
---

# Easy Docker

`easy-docker` is the interactive setup and management workflow for this repository.
It is designed to make common Frappe Docker tasks easier from the terminal while
keeping the underlying Compose and Bench model visible.

This section documents the current behavior of the wizard:

- `single-host` is the supported production workflow today
- `split-services` is available for separated stack setup and Compose runtime control
- site actions currently remain part of the `single-host` workflow
- stack, site, app, and update actions are handled through the wizard
- the generated Compose output is available as a rendered snapshot

Start here:

- [Overview](./01-overview.md)
- [Workflows](./02-workflows.md)
- [Updates](./03-updates.md)
- [Generated Compose](./04-generated-compose.md)
- [Split Services](./05-split-services.md)
