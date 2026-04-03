---
title: Easy Docker
---

# Easy Docker

`easy-docker` is the interactive setup and management workflow for this repository.
It guides common stack operations through a terminal UI so you do not have to assemble
every Docker and Bench command manually.

For the detailed guide, use the dedicated docs area under `docs/10-easy-docker/`.
This getting-started page stays short and focuses on the first steps.

Current status:

- `single-host` is the primary supported topology
- `split-services` is still in development
- stack, site, app, backup, restart, and update flows are being expanded iteratively

The script entrypoint is:

```bash
bash easy-docker.sh
```

Minimal first use:

1. Start `easy-docker.sh`
2. Create a new stack
3. Choose `single-host`
4. Pick the apps and branches you want
5. Build the custom image
6. Start the stack
7. Create the first site or manage an existing one from the stack menu

Use this page as the entry point. For the full workflow reference, jump to the
dedicated `easy-docker` docs section in the root `docs` tree.
