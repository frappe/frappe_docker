#!/usr/bin/env python3
"""Validate an NDF product image against its build metadata and manifest lock."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class ImageValidationError(Exception):
    """Raised when a built image does not match its expected composition."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImageValidationError(f"Unable to read JSON file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ImageValidationError(f"Expected a JSON object in {path}")
    return data


def run_docker(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ImageValidationError(f"Unable to execute Docker: {exc}") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ImageValidationError(
            f"Docker command failed with exit code {result.returncode}: {detail}"
        )
    return result.stdout.strip()


def inspect_image_labels(image_ref: str) -> dict[str, str]:
    output = run_docker([
        "docker", "image", "inspect", image_ref,
        "--format", "{{json .Config.Labels}}",
    ])
    try:
        labels = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ImageValidationError(
            f"Docker returned invalid image-label JSON: {exc}"
        ) from exc
    if not isinstance(labels, dict):
        raise ImageValidationError("Image has no valid OCI/NDF label object.")
    return labels


def inspect_image_contents(image_ref: str) -> dict[str, Any]:
    inspection_code = (
        "import json,pathlib;"
        "root=pathlib.Path('/home/frappe/frappe-bench/apps');"
        "apps_file=pathlib.Path('/home/frappe/frappe-bench/sites/apps.txt');"
        "print(json.dumps({"
        "'directories':sorted(p.name for p in root.iterdir() if p.is_dir()),"
        "'apps_txt':[line.strip() for line in apps_file.read_text().splitlines() "
        "if line.strip()]"
        "}))"
    )
    output = run_docker([
        "docker", "run", "--rm", "--entrypoint", "bash", image_ref,
        "-lc", f"python -c {json.dumps(inspection_code)}",
    ])
    try:
        contents = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ImageValidationError(
            f"Container returned invalid application inspection JSON: {exc}"
        ) from exc
    if not isinstance(contents, dict):
        raise ImageValidationError("Container returned an invalid content report.")
    return contents


def validate_image(
    image_ref: str,
    metadata: dict[str, Any],
    lock_data: dict[str, Any],
    labels: dict[str, str],
    contents: dict[str, Any],
) -> dict[str, Any]:
    """Compare image contents and labels against build metadata and lock data."""
    expected_apps = [app["name"] for app in metadata["applications"]]
    expected_app_set = set(expected_apps)
    if len(expected_apps) != len(expected_app_set):
        raise ImageValidationError("Build metadata contains duplicate application names.")

    actual_dirs = contents.get("directories")
    actual_apps_txt = contents.get("apps_txt")
    if not isinstance(actual_dirs, list) or not isinstance(actual_apps_txt, list):
        raise ImageValidationError("Image inspection did not return application lists.")

    actual_dir_set = set(actual_dirs)
    actual_apps_txt_set = set(actual_apps_txt)

    missing_dirs = sorted(expected_app_set - actual_dir_set)
    unexpected_dirs = sorted(actual_dir_set - expected_app_set)
    missing_apps_txt = sorted(expected_app_set - actual_apps_txt_set)
    unexpected_apps_txt = sorted(actual_apps_txt_set - expected_app_set)

    problems = []
    if missing_dirs or unexpected_dirs:
        problems.append(
            f"Application directory mismatch: missing={missing_dirs}, "
            f"unexpected={unexpected_dirs}"
        )
    if missing_apps_txt or unexpected_apps_txt:
        problems.append(
            f"sites/apps.txt mismatch: missing={missing_apps_txt}, "
            f"unexpected={unexpected_apps_txt}"
        )

    image = metadata["image"]
    framework = metadata["framework"]
    manifest_entries = [
        item for item in lock_data.get("manifests", [])
        if item.get("path") == image["manifest"]
    ]
    if len(manifest_entries) != 1:
        raise ImageValidationError(
            f"Expected exactly one lock checksum for '{image['manifest']}'."
        )

    expected_label_values = {
        "org.opencontainers.image.title": image["product"],
        "org.opencontainers.image.source": (
            "https://github.com/NdfTechLabs/frappe_docker"
        ),
        "org.opencontainers.image.url": (
            "https://github.com/NdfTechLabs/frappe_docker"
        ),
        "com.ndf.image.id": image["id"],
        "com.ndf.product": image["product"],
        "com.ndf.manifest.path": image["manifest"],
        "com.ndf.manifest.sha256": manifest_entries[0]["sha256"],
        "com.ndf.framework.name": framework["name"],
        "com.ndf.framework.version": framework["version"],
        "com.ndf.framework.target-ref": framework["target_ref"],
        "com.ndf.lock.sha256": metadata["lock"]["sha256"],
    }
    for name, expected in expected_label_values.items():
        actual = labels.get(name)
        if actual != expected:
            problems.append(
                f"Image label '{name}' mismatch: expected {expected!r}, "
                f"got {actual!r}"
            )

    expected_label_apps = [
        {
            "name": app["name"],
            "target_ref": app["target_ref"],
            "resolved_sha": app["resolved_sha"],
        }
        for app in metadata["applications"]
    ]
    try:
        actual_label_apps = json.loads(labels.get("com.ndf.applications", ""))
    except json.JSONDecodeError:
        actual_label_apps = None
    if actual_label_apps != expected_label_apps:
        problems.append(
            "Image label 'com.ndf.applications' does not match build metadata."
        )

    if problems:
        raise ImageValidationError("\n".join(problems))

    return {
        "image": image_ref,
        "product": image["product"],
        "image_id": image["id"],
        "framework": framework,
        "application_count": len(expected_apps),
        "applications": expected_apps,
        "directories_verified": True,
        "apps_txt_verified": True,
        "labels_verified": True,
        "status": "passed",
    }


def validate_from_files(
    image_ref: str,
    metadata_path: Path,
    lock_path: Path,
) -> dict[str, Any]:
    metadata = load_json(metadata_path)
    lock_data = load_json(lock_path)
    labels = inspect_image_labels(image_ref)
    contents = inspect_image_contents(image_ref)
    return validate_image(image_ref, metadata, lock_data, labels, contents)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an NDF product image against its build metadata and lock."
    )
    parser.add_argument("--image", required=True, help="Local Docker image reference.")
    parser.add_argument("--metadata", required=True, type=Path, help="Build metadata JSON.")
    parser.add_argument("--lock", required=True, type=Path, help="Manifest lock JSON.")
    parser.add_argument("--report", type=Path, help="Optional JSON validation report path.")
    args = parser.parse_args()

    try:
        report = validate_from_files(args.image, args.metadata, args.lock)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    except (ImageValidationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Validated {report['application_count']} applications and OCI/NDF labels "
        f"for {report['image']}."
    )
    if args.report:
        print(f"Validation report: {args.report}")
    print("Image validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
