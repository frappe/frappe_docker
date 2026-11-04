#!/usr/bin/env python3
"""Prepare deterministic inputs for an NDF product image build.

The image definition selects the product and image repository. The product
manifest is used to validate the corresponding lock file. Bench receives the
branch/tag references recorded in that lock file; resolved SHAs are retained
in build metadata for traceability.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .resolve_manifest import ManifestError, ManifestLoader
    from .validate_image_definitions import (
        ImageDefinitionError,
        load_json,
        validate_definitions,
        validate_schema,
    )
except ImportError:
    # Support direct execution: python images/ndf/scripts/prepare_build.py
    from resolve_manifest import ManifestError, ManifestLoader
    from validate_image_definitions import (
        ImageDefinitionError,
        load_json,
        validate_definitions,
        validate_schema,
    )


class BuildPreparationError(Exception):
    """Raised when image build inputs cannot be prepared."""


def resolve_inside(root: Path, relative_path: str, description: str) -> Path:
    """Resolve a relative path and prevent it from escaping its root."""
    path = (root / relative_path).resolve()
    root = root.resolve()

    if not path.is_relative_to(root):
        raise BuildPreparationError(
            f"{description} path escapes its configured directory: {relative_path}"
        )

    return path


def load_image_definition(
    ndf_dir: Path,
    definitions_relative_path: str,
    image_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and validate image definitions, then select one image."""
    definitions_path = resolve_inside(
        ndf_dir,
        definitions_relative_path,
        "Image definitions",
    )
    schema_path = ndf_dir / "schemas" / "image-definitions-v1.schema.json"
    manifests_dir = ndf_dir / "manifests"

    try:
        definitions = load_json(definitions_path)
        validate_schema(definitions, schema_path)
        validate_definitions(definitions, manifests_dir)
    except ImageDefinitionError as exc:
        raise BuildPreparationError(str(exc)) from exc

    matches = [
        image for image in definitions["images"]
        if image["id"] == image_id
    ]

    if not matches:
        available = ", ".join(
            image["id"] for image in definitions["images"]
        )
        raise BuildPreparationError(
            f"Unknown image ID '{image_id}'. Available images: {available}"
        )

    return definitions, matches[0]


def validate_build_lock(
    ndf_dir: Path,
    image: dict[str, Any],
) -> tuple[dict[str, Any], Path, str]:
    """Load and validate the lock file associated with the image manifest."""
    manifests_dir = ndf_dir / "manifests"
    manifest_path = resolve_inside(
        manifests_dir,
        image["manifest"],
        "Product manifest",
    )

    manifest_relative_path = manifest_path.relative_to(manifests_dir).as_posix()
    lock_path = ndf_dir / "locks" / f"{manifest_path.stem}.lock.json"

    if not lock_path.is_file():
        raise BuildPreparationError(
            f"Lock file not found for image '{image['id']}': {lock_path}"
        )

    try:
        loader = ManifestLoader(manifests_dir)
        manifest = loader.load(manifest_relative_path)
        loader.validate_lock_file(lock_path, manifest)
        lock_data = load_json(lock_path)
    except (ManifestError, ImageDefinitionError) as exc:
        raise BuildPreparationError(str(exc)) from exc

    product_id = lock_data.get("product", {}).get("id")
    if product_id != image["id"]:
        raise BuildPreparationError(
            f"Lock product ID '{product_id}' does not match image ID '{image['id']}'."
        )

    framework = lock_data.get("framework")
    if not isinstance(framework, dict):
        raise BuildPreparationError("Lock file has no valid framework section.")

    frappe_apps = [
        app for app in lock_data["applications"]
        if app["name"] == "frappe"
    ]
    if len(frappe_apps) != 1:
        raise BuildPreparationError(
            "Lock file must contain exactly one 'frappe' application."
        )

    frappe_app = frappe_apps[0]
    if framework.get("name") != "frappe":
        raise BuildPreparationError(
            "Only the Frappe framework is currently supported."
        )

    if framework.get("target_ref") != frappe_app.get("target_ref"):
        raise BuildPreparationError(
            "Framework target_ref does not match the Frappe application target_ref."
        )

    if not isinstance(framework.get("version"), str) or not framework["version"]:
        raise BuildPreparationError("Framework version is missing from lock file.")

    return lock_data, lock_path, manifest_relative_path


def build_apps_json(lock_data: dict[str, Any]) -> list[dict[str, str]]:
    """Create Bench apps.json entries in lock installation order.

    Frappe is excluded because images/layered/Containerfile installs it through
    FRAPPE_PATH and FRAPPE_BRANCH.
    """
    applications = lock_data["applications"]
    ordered = sorted(
        applications,
        key=lambda app: app["installation_order"],
    )

    apps_json = []
    for app in ordered:
        if app["name"] == "frappe":
            continue

        repository = app["repository"]
        target_ref = app["target_ref"]

        if not isinstance(repository, str) or not repository:
            raise BuildPreparationError(
                f"Application '{app['name']}' has an invalid repository."
            )

        if not isinstance(target_ref, str) or not target_ref:
            raise BuildPreparationError(
                f"Application '{app['name']}' has an invalid target_ref."
            )

        apps_json.append({
            "url": repository,
            "branch": target_ref,
        })

    return apps_json


def build_metadata(
    image: dict[str, Any],
    lock_data: dict[str, Any],
    lock_path: Path,
    manifest_relative_path: str,
) -> dict[str, Any]:
    """Create traceability metadata for the image build."""
    lock_bytes = lock_path.read_bytes()
    framework = lock_data["framework"]

    return {
        "schema_version": "1.0",
        "image": {
            "id": image["id"],
            "product": image["product"],
            "repository": image["repository"],
            "manifest": manifest_relative_path,
        },
        "product": lock_data["product"],
        "framework": framework,
        "lock": {
            "version": lock_data["lock_version"],
            "path": lock_path.name,
            "sha256": hashlib.sha256(lock_bytes).hexdigest(),
        },
        "applications": [
            {
                "name": app["name"],
                "repository": app["repository"],
                "target_ref": app["target_ref"],
                "resolved_sha": app["ref"],
                "dependencies": app["dependencies"],
                "installation_order": app["installation_order"],
            }
            for app in sorted(
                lock_data["applications"],
                key=lambda item: item["installation_order"],
            )
        ],
    }


def write_json(path: Path, data: Any) -> Path:
    """Write JSON atomically with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary_path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as exc:
        raise BuildPreparationError(
            f"Unable to write build input {path}: {exc}"
        ) from exc

    return path


def prepare_build(
    ndf_dir: Path,
    image_id: str,
    definitions_relative_path: str = "image-definitions/images-v1.json",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Prepare Bench apps.json and NDF build metadata for one product image."""
    ndf_dir = ndf_dir.resolve()

    _, image = load_image_definition(
        ndf_dir,
        definitions_relative_path,
        image_id,
    )

    lock_data, lock_path, manifest_relative_path = validate_build_lock(
        ndf_dir,
        image,
    )

    apps_json = build_apps_json(lock_data)
    metadata = build_metadata(
        image,
        lock_data,
        lock_path,
        manifest_relative_path,
    )

    output_dir = output_dir or (ndf_dir / ".build" / image_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    apps_json_path = write_json(output_dir / "apps.json", apps_json)
    metadata_path = write_json(output_dir / "build-metadata.json", metadata)

    return {
        "image": image,
        "framework": lock_data["framework"],
        "lock_path": lock_path,
        "apps_json_path": apps_json_path,
        "metadata_path": metadata_path,
        "applications_count": len(lock_data["applications"]),
        "bench_apps_count": len(apps_json),
    }


def main() -> int:
    ndf_dir = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        description="Prepare NDF build inputs from an image definition and lock file."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Image ID from image-definitions/images-v1.json (e.g. dalali-v16).",
    )
    parser.add_argument(
        "--definitions",
        default="image-definitions/images-v1.json",
        help="Image definitions path relative to images/ndf.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (defaults to images/ndf/.build/<image-id>).",
    )

    args = parser.parse_args()

    try:
        result = prepare_build(
            ndf_dir=ndf_dir,
            image_id=args.image,
            definitions_relative_path=args.definitions,
            output_dir=args.output_dir,
        )
    except (BuildPreparationError, ManifestError, ImageDefinitionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    framework = result["framework"]
    image = result["image"]

    print(f"Prepared image: {image['id']}")
    print(f"Repository: {image['repository']}")
    print(f"Frappe branch: {framework['target_ref']}")
    print(f"Lock file: {result['lock_path']}")
    print(f"Applications in lock: {result['applications_count']}")
    print(f"Applications for Bench: {result['bench_apps_count']}")
    print(f"Bench apps.json: {result['apps_json_path']}")
    print(f"Build metadata: {result['metadata_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
