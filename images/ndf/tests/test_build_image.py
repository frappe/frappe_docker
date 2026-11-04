import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.build_image import (
    BuildExecutionError,
    build_command,
    build_labels,
    execute_build,
    get_manifest_checksum,
)


def test_get_manifest_checksum_returns_matching_source_revision():
    lock = {
        "manifests": [
            {"path": "products/dalali-v16.json", "sha256": "a" * 64}
        ]
    }
    assert get_manifest_checksum(lock, "products/dalali-v16.json") == "a" * 64


def test_get_manifest_checksum_rejects_missing_or_duplicate_entries():
    with pytest.raises(BuildExecutionError, match="exactly one"):
        get_manifest_checksum({"manifests": []}, "products/missing.json")

    lock = {
        "manifests": [
            {"path": "products/app.json", "sha256": "a" * 64},
            {"path": "products/app.json", "sha256": "b" * 64},
        ]
    }
    with pytest.raises(BuildExecutionError, match="exactly one"):
        get_manifest_checksum(lock, "products/app.json")


def test_build_labels_include_manifest_lock_and_application_refs():
    metadata = {
        "image": {
            "id": "dalali-v16",
            "product": "dalali",
            "manifest": "products/dalali-v16.json",
        },
        "framework": {"name": "frappe", "version": "16", "target_ref": "version-16"},
        "lock": {"sha256": "b" * 64},
        "applications": [
            {"name": "erpnext", "target_ref": "version-16", "resolved_sha": "c" * 40}
        ],
    }
    lock = {
        "manifests": [
            {"path": "products/dalali-v16.json", "sha256": "a" * 64}
        ]
    }

    labels = build_labels(metadata, lock)
    apps = json.loads(labels["com.ndf.applications"])

    assert labels["org.opencontainers.image.source"] == (
        "https://github.com/NdfTechLabs/frappe_docker"
    )
    assert labels["org.opencontainers.image.url"] == (
        "https://github.com/NdfTechLabs/frappe_docker"
    )
    assert labels["com.ndf.image.id"] == "dalali-v16"
    assert labels["com.ndf.manifest.sha256"] == "a" * 64
    assert labels["com.ndf.lock.sha256"] == "b" * 64
    assert labels["com.ndf.framework.target-ref"] == "version-16"
    assert apps[0]["target_ref"] == "version-16"
    assert apps[0]["resolved_sha"] == "c" * 40


def _build_command(tmp_path, **overrides):
    root = tmp_path
    dockerfile = root / "images" / "layered" / "Containerfile"
    apps_json = root / "images" / "ndf" / ".build" / "dalali" / "apps.json"
    dockerfile.parent.mkdir(parents=True, exist_ok=True)
    apps_json.parent.mkdir(parents=True, exist_ok=True)
    dockerfile.touch()
    apps_json.write_text("[]", encoding="utf-8")

    arguments = {
        "repository_root": root,
        "dockerfile": dockerfile,
        "apps_json": apps_json,
        "image_repository": "ghcr.io/ndftechlabs/dhanaerp-dalali",
        "image_tag": "local",
        "frappe_branch": "version-16",
        "labels": {"com.ndf.image.id": "dalali-v16"},
        "platform": "linux/amd64",
        "no_cache": False,
        "builder": None,
    }
    arguments.update(overrides)
    return build_command(**arguments)


def test_build_command_loads_locally_and_uses_buildkit_secret(tmp_path):
    command = _build_command(
        tmp_path,
        no_cache=True,
        builder="ndf-local",
    )

    assert "--load" in command
    assert "--push" not in command
    assert "--secret" in command
    assert any(item.startswith("id=apps_json,src=") for item in command)
    assert "FRAPPE_BRANCH=version-16" in command
    assert "ghcr.io/ndftechlabs/dhanaerp-dalali:local" in command
    assert "linux/amd64" in command
    assert "--no-cache" in command
    assert "ndf-local" in command


def test_build_command_adds_buildkit_cache_sources_and_destinations(tmp_path):
    command = _build_command(
        tmp_path,
        cache_from=["type=gha,scope=ndf-dalali-v16"],
        cache_to=["type=gha,mode=max,scope=ndf-dalali-v16"],
    )

    assert command.count("--cache-from") == 1
    assert "type=gha,scope=ndf-dalali-v16" in command
    assert command.count("--cache-to") == 1
    assert "type=gha,mode=max,scope=ndf-dalali-v16" in command


def test_build_command_supports_multiple_cache_backends(tmp_path):
    command = _build_command(
        tmp_path,
        cache_from=["type=gha,scope=product", "type=registry,ref=example/cache:latest"],
        cache_to=["type=gha,mode=max,scope=product"],
    )

    assert command.count("--cache-from") == 2
    assert command.count("--cache-to") == 1


def test_execute_build_dry_run_does_not_call_subprocess():
    with patch("scripts.build_image.subprocess.run") as run:
        execute_build(["docker", "buildx", "build", "--load", "."], dry_run=True)
    run.assert_not_called()


def test_execute_build_rejects_unavailable_buildx():
    class Result:
        returncode = 1
        stderr = "buildx not installed"
        stdout = ""

    with patch("scripts.build_image.subprocess.run", return_value=Result()):
        with pytest.raises(BuildExecutionError, match="Buildx is unavailable"):
            execute_build(["docker", "buildx", "build", "--load", "."])


def test_execute_build_reports_build_failure():
    class VersionResult:
        returncode = 0
        stderr = ""
        stdout = "github.com/docker/buildx"

    class BuildResult:
        returncode = 17

    with patch(
        "scripts.build_image.subprocess.run",
        side_effect=[VersionResult(), BuildResult()],
    ):
        with pytest.raises(BuildExecutionError, match="exit code 17"):
            execute_build(["docker", "buildx", "build", "--load", "."])
