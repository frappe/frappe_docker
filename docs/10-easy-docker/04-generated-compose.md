---
title: Generated Compose
---

# Generated Compose

`easy-docker` can render a `compose.generated.yaml` snapshot from the stack
metadata and environment.

This file is useful when you want to inspect or reuse the resolved Compose
configuration outside the wizard, but it is not the primary runtime input for
stack start or stop.

What is important:

- the stack runtime reads the original Compose files from metadata
- the runtime also reads the stack `.env`
- `compose.generated.yaml` is a rendered snapshot, not the source of truth
- it is refreshed after a successful custom image build

That means the generated file stays aligned with the current stack state when the
image has actually been rebuilt, which is the point where manual reuse is most
likely to matter.
