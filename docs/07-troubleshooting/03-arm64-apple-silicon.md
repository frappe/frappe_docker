---
title: ARM64 / Apple Silicon
---

## Notes on ARM64 and Apple Silicon

- Enable Docker Desktop's Rosetta emulation for initial builds when running on Apple Silicon with x86-only images.
- Prefer published multi-arch images (`frappe/bench`, `frappe/erpnext`) or build locally with `docker buildx bake --set *.platform=linux/amd64,linux/arm64` to cover both architectures in one pass.
- When using `pwd.yml`, export `DOCKER_DEFAULT_PLATFORM=linux/arm64` (or select the provided compose profile) to avoid unexpected emulation.
- Keep bind mounts under your user home directory and apply `:cached` or `:delegated` consistency flags for better performance on macOS.
