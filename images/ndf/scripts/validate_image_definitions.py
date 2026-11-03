#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


class ImageDefinitionError(Exception):
    """Raised when image definitions are invalid."""


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise ImageDefinitionError(
            f"Invalid JSON in {path}: {exc}"
        ) from exc

    except OSError as exc:
        raise ImageDefinitionError(
            f"Unable to read {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ImageDefinitionError(
            f"Expected a JSON object in {path}"
        )

    return data


def validate_schema(definitions: dict, schema_path: Path):
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(definitions),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        details = []

        for error in errors:
            location = ".".join(
                str(part) for part in error.absolute_path
            ) or "<root>"

            details.append(f"  - {location}: {error.message}")

        raise ImageDefinitionError(
            "Image-definition schema validation failed:\n"
            + "\n".join(details)
        )


def validate_definitions(
    definitions: dict,
    manifests_dir: Path,
):
    images = definitions["images"]
    registry = definitions["registry"]

    seen_ids = set()
    seen_repositories = set()

    expected_prefix = (
        f"{registry['host']}/{registry['namespace']}/"
    )

    manifests_root = manifests_dir.resolve()

    for image in images:
        image_id = image["id"]
        repository = image["repository"]
        manifest = image["manifest"]

        if image_id in seen_ids:
            raise ImageDefinitionError(
                f"Duplicate image ID: {image_id}"
            )

        if repository in seen_repositories:
            raise ImageDefinitionError(
                f"Duplicate image repository: {repository}"
            )

        if not repository.startswith(expected_prefix):
            raise ImageDefinitionError(
                f"Image repository '{repository}' must use "
                f"the configured registry prefix '{expected_prefix}'"
            )

        seen_ids.add(image_id)
        seen_repositories.add(repository)

        manifest_path = (manifests_root / manifest).resolve()

        if not manifest_path.is_relative_to(manifests_root):
            raise ImageDefinitionError(
                f"Manifest path escapes the manifests directory: "
                f"{manifest}"
            )

        if not manifest_path.is_file():
            raise ImageDefinitionError(
                f"Referenced manifest does not exist: {manifest}"
            )

        manifest_data = load_json(manifest_path)

        if manifest_data.get("id") != image_id:
            raise ImageDefinitionError(
                f"Image '{image_id}' references manifest "
                f"'{manifest}', whose ID is "
                f"'{manifest_data.get('id')}'"
            )


def main():
    ndf_dir = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        description="Validate NDF image definitions."
    )

    parser.add_argument(
        "definitions",
        nargs="?",
        default="image-definitions/images-v1.json",
        help="Path relative to images/ndf.",
    )

    args = parser.parse_args()

    definitions_path = (ndf_dir / args.definitions).resolve()
    schema_path = (
        ndf_dir / "schemas" / "image-definitions-v1.schema.json"
    )
    manifests_dir = ndf_dir / "manifests"

    try:
        definitions = load_json(definitions_path)

        validate_schema(
            definitions,
            schema_path,
        )

        validate_definitions(
            definitions,
            manifests_dir,
        )

    except ImageDefinitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(definitions['images'])} image definitions."
    )
    print("Image definitions are valid.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())