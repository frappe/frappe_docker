---
title: Overview
---

# Overview

`easy-docker` guides the main stack lifecycle through menus instead of requiring
users to assemble long Docker and Bench commands by hand.

Current scope:

- create a stack
- choose the topology
- configure apps and branches
- build the custom image
- start, restart, stop, and delete the stack
- create and manage a site
- install and uninstall apps on an existing site
- create a site backup

Current limitations:

- `single-host` is the supported path
- `split-services` is still marked as in development
- site management currently assumes one configured site per stack
- backup and app management are focused on the configured stack image and site

The current entrypoint is:

```bash
bash easy-docker.sh
```
