import pytest

from scripts.validate_image_definitions import (
    ImageDefinitionError,
    validate_definitions,
)


@pytest.fixture
def image_environment(tmp_path):
    """Create an isolated image-definition environment."""

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Create two valid product manifests.
    for manifest_id in ("product-a", "product-b"):
        manifest_path = manifests_dir / f"{manifest_id}.json"
        manifest_path.write_text(
            f'{{"id": "{manifest_id}"}}',
            encoding="utf-8",
        )

    definitions = {
        "schema_version": "1.0",
        "registry": {
            "host": "ghcr.io",
            "namespace": "ndftechlabs",
        },
        "images": [
            {
                "id": "product-a",
                "product": "product-a",
                "manifest": "product-a.json",
                "repository": "ghcr.io/ndftechlabs/product-a",
            },
            {
                "id": "product-b",
                "product": "product-b",
                "manifest": "product-b.json",
                "repository": "ghcr.io/ndftechlabs/product-b",
            },
        ],
    }

    return {
        "manifests_dir": manifests_dir,
        "definitions": definitions,
    }


class TestImageDefinitionValidation:

    def test_valid_definitions_pass(self, image_environment):
        environment = image_environment

        validate_definitions(
            environment["definitions"],
            environment["manifests_dir"],
        )

    def test_duplicate_image_ids_are_rejected(self, image_environment):
        environment = image_environment
        definitions = environment["definitions"]

        definitions["images"][1]["id"] = "product-a"

        with pytest.raises(
            ImageDefinitionError,
            match="Duplicate image ID",
        ):
            validate_definitions(
                definitions,
                environment["manifests_dir"],
            )

    def test_duplicate_repositories_are_rejected(self, image_environment):
        environment = image_environment
        definitions = environment["definitions"]

        definitions["images"][1]["repository"] = (
            definitions["images"][0]["repository"]
        )

        with pytest.raises(
            ImageDefinitionError,
            match="Duplicate image repository",
        ):
            validate_definitions(
                definitions,
                environment["manifests_dir"],
            )

    def test_missing_manifest_is_rejected(self, image_environment):
        environment = image_environment
        definitions = environment["definitions"]

        definitions["images"][1]["manifest"] = "missing-product.json"

        with pytest.raises(
            ImageDefinitionError,
            match="Referenced manifest does not exist",
        ):
            validate_definitions(
                definitions,
                environment["manifests_dir"],
            )

    def test_manifest_path_traversal_is_rejected(self, image_environment):
        environment = image_environment
        definitions = environment["definitions"]

        definitions["images"][1]["manifest"] = (
            "../../outside/malicious.json"
        )

        with pytest.raises(
            ImageDefinitionError,
            match="Manifest path escapes the manifests directory",
        ):
            validate_definitions(
                definitions,
                environment["manifests_dir"],
            )

    def test_manifest_identity_mismatch_is_rejected(self, image_environment):
        environment = image_environment
        definitions = environment["definitions"]

        definitions["images"][1]["manifest"] = "product-a.json"

        with pytest.raises(
            ImageDefinitionError,
            match="whose ID is",
        ):
            validate_definitions(
                definitions,
                environment["manifests_dir"],
            )