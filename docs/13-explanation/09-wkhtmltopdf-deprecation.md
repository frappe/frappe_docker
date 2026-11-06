---
title: wkhtmltopdf Deprecation
---

# wkhtmltopdf deprecation and removal

Frappe deprecated wkhtmltopdf in v16 and removes support in v17 in favor of
Chromium. Frappe Docker is preparing for this transition while preserving
compatibility with supported versions. See [Frappe PDF generation](https://docs.frappe.io/framework/user/en/printing/pdf-generation).

## Optional installation

The `INSTALL_WKHTMLTOPDF` build argument controls whether production, custom, and
bench images include wkhtmltopdf. It defaults to `true`; setting it to `false`
skips downloading and installing wkhtmltopdf when building an image. Docker Buildx
Bake accepts the same setting through the shell environment, and the reusable
test and publish workflows expose it as `install_wkhtmltopdf`.

This is a build-time choice. Existing images and site printing settings are
unaffected. A v16 deployment opting out must use Chromium for its site defaults
and any print formats that explicitly select wkhtmltopdf, and verify its PDF
output. Chromium must remain available in the image.

Layered images inherit this choice from their base and build images. Omitting
wkhtmltopdf requires building those images with the option disabled before
building the layered image.

See [Build Setup](../02-setup/02-build-setup.md#build-args-secrets-and-flags) for the
build argument reference.

## Planned removal

- **v15 and v16:** Published `erpnext`, `base`, and `build` images continue to
  include wkhtmltopdf for compatibility. The shared `bench` image also keeps it
  while v16 is supported. Custom builds can opt out with
  `INSTALL_WKHTMLTOPDF=false`.
- **v17:** When v17 is released, its published images will be built without
  wkhtmltopdf. Installation support remains available for supported older versions
  that still use it.
- **v18:** When v18 is released, support for v16 will be dropped. Since v16 is the
  last Frappe version with wkhtmltopdf support, wkhtmltopdf installation code and
  the `INSTALL_WKHTMLTOPDF` option will then be removed entirely, including from
  the bench image build.
