---
title: Build Without wkhtmltopdf
---

# Build without wkhtmltopdf

Frappe deprecated wkhtmltopdf in v16 and removes support in v17. Published v15/v16
`erpnext`, `base`, and `build` images, and the shared `bench` image, continue to
include it for compatibility. See [Frappe PDF generation](https://docs.frappe.io/framework/user/en/printing/pdf-generation).

## Prepare your site

For a v16 site, switch the PDF Generator in Print Settings and any print formats
that explicitly select wkhtmltopdf to Chrome, then verify the resulting PDFs
before opting out. This build option does not change site settings or print
formats. Keep Chromium enabled or provide another working Chromium installation.

## Build a custom image

Follow the prerequisites in [Build Setup](../02-setup/02-build-setup.md#prerequisites),
then build a custom image with `INSTALL_WKHTMLTOPDF=false`:

```bash
docker build \
 --file images/custom/Containerfile \
 --build-arg FRAPPE_BRANCH=version-16 \
 --build-arg INSTALL_WKHTMLTOPDF=false \
 --tag custom:16-chrome .
```

Add `--secret=id=apps_json,src=apps.json` to include custom apps. The same build
argument works with Podman and with `images/production/Containerfile` or
`images/bench/Dockerfile`.

## Build with Docker Buildx Bake

Set the environment variable:

```bash
INSTALL_WKHTMLTOPDF=false docker buildx bake base build erpnext
```

## Use the reusable workflows

The reusable `core-build-test-images.yml` and `core-publish-images.yml` workflows
accept `install_wkhtmltopdf` (boolean, default `true`). Pass the same value to both
workflows when testing and publishing a release line. This allows develop/v17
builds to opt out explicitly without changing v15/v16 defaults.

## Build a layered image

`images/layered/Containerfile` inherits system packages from its `frappe/base` and
`frappe/build` images and does not accept `INSTALL_WKHTMLTOPDF`. To omit wkhtmltopdf
from a layered image, first build and publish both base images with the option
disabled under your own image prefix and matching tags, then use that prefix via
`FRAPPE_IMAGE_PREFIX`. Otherwise, use the custom Containerfile shown above.
