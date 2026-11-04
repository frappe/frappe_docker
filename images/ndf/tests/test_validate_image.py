import json
from unittest.mock import patch

import pytest

from scripts.validate_image import (
    ImageValidationError,
    inspect_image_contents,
    validate_image,
)


@pytest.fixture
def validation_inputs():
    metadata = {
        "image": {
            "id": "dalali-v16",
            "product": "dalali",
            "manifest": "products/tenant/dalali-v16.json",
        },
        "framework": {
            "name": "frappe",
            "version": "16",
            "target_ref": "version-16",
        },
        "lock": {"sha256": "b" * 64},
        "applications": [
            {
                "name": "frappe",
                "target_ref": "version-16",
                "resolved_sha": "a" * 40,
            },
            {
                "name": "erpnext",
                "target_ref": "version-16",
                "resolved_sha": "c" * 40,
            },
            {
                "name": "dt_dalali_ecommerce",
                "target_ref": "version-1",
                "resolved_sha": "d" * 40,
            },
        ],
    }
    lock = {
        "manifests": [
            {
                "path": "products/tenant/dalali-v16.json",
                "sha256": "e" * 64,
            }
        ]
    }
    labels = {
        "org.opencontainers.image.title": "dalali",
        "org.opencontainers.image.source": (
            "https://github.com/NdfTechLabs/frappe_docker"
        ),
        "org.opencontainers.image.url": (
            "https://github.com/NdfTechLabs/frappe_docker"
        ),
        "com.ndf.image.id": "dalali-v16",
        "com.ndf.product": "dalali",
        "com.ndf.manifest.path": "products/tenant/dalali-v16.json",
        "com.ndf.manifest.sha256": "e" * 64,
        "com.ndf.framework.name": "frappe",
        "com.ndf.framework.version": "16",
        "com.ndf.framework.target-ref": "version-16",
        "com.ndf.lock.sha256": "b" * 64,
        "com.ndf.applications": json.dumps([
            {
                "name": app["name"],
                "target_ref": app["target_ref"],
                "resolved_sha": app["resolved_sha"],
            }
            for app in metadata["applications"]
        ]),
    }
    contents = {
        "directories": [
            "frappe",
            "erpnext",
            "dt_dalali_ecommerce",
        ],
        "apps_txt": [
            "frappe",
            "erpnext",
            "dt_dalali_ecommerce",
        ],
    }
    return metadata, lock, labels, contents


def test_validate_image_accepts_matching_contents_and_labels(validation_inputs):
    metadata, lock, labels, contents = validation_inputs

    report = validate_image(
        "local/dalali:test",
        metadata,
        lock,
        labels,
        contents,
    )

    assert report["status"] == "passed"
    assert report["application_count"] == 3
    assert report["directories_verified"] is True
    assert report["apps_txt_verified"] is True
    assert report["labels_verified"] is True


def test_validate_image_rejects_missing_application_directory(validation_inputs):
    metadata, lock, labels, contents = validation_inputs
    contents["directories"].remove("erpnext")

    with pytest.raises(ImageValidationError, match="Application directory mismatch"):
        validate_image("local/dalali:test", metadata, lock, labels, contents)


def test_validate_image_rejects_unexpected_application_in_apps_txt(validation_inputs):
    metadata, lock, labels, contents = validation_inputs
    contents["apps_txt"].append("unlisted_app")

    with pytest.raises(ImageValidationError, match="sites/apps.txt mismatch"):
        validate_image("local/dalali:test", metadata, lock, labels, contents)


def test_validate_image_rejects_mismatched_oci_label(validation_inputs):
    metadata, lock, labels, contents = validation_inputs
    labels["org.opencontainers.image.url"] = "https://github.com/frappe/frappe_docker"

    with pytest.raises(ImageValidationError, match="org.opencontainers.image.url"):
        validate_image("local/dalali:test", metadata, lock, labels, contents)


def test_validate_image_rejects_mismatched_application_label(validation_inputs):
    metadata, lock, labels, contents = validation_inputs
    labels["com.ndf.applications"] = "[]"

    with pytest.raises(ImageValidationError, match="com.ndf.applications"):
        validate_image("local/dalali:test", metadata, lock, labels, contents)


def test_validate_image_rejects_duplicate_expected_applications(validation_inputs):
    metadata, lock, labels, contents = validation_inputs
    metadata["applications"].append(metadata["applications"][0])

    with pytest.raises(ImageValidationError, match="duplicate application"):
        validate_image("local/dalali:test", metadata, lock, labels, contents)


def test_inspect_image_contents_runs_one_shot_container():
    class Result:
        returncode = 0
        stdout = json.dumps({
            "directories": ["frappe", "erpnext"],
            "apps_txt": ["frappe", "erpnext"],
        })
        stderr = ""

    with patch("scripts.validate_image.subprocess.run", return_value=Result()) as run:
        result = inspect_image_contents("local/dalali:test")

    assert result["directories"] == ["frappe", "erpnext"]
    command = run.call_args.args[0]
    assert command[:4] == [
        "docker", "run", "--rm", "--entrypoint"
    ]
    assert "local/dalali:test" in command
