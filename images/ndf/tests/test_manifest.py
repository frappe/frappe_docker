import os
import shutil
import subprocess
import sys

import json
import pytest
from pathlib import Path

from scripts.resolve_manifest import (
    ManifestLoader,
    ManifestError,
)


def run_resolver(environment, *arguments):
    """Execute the manifest resolver as a subprocess."""

    return subprocess.run(
        [
            sys.executable,
            str(environment["script"]),
            environment["manifest_argument"],
            *arguments,
        ],
        cwd=environment["ndf_dir"].parents[1],
        capture_output=True,
        text=True,
    )

def write_test_manifest(
    manifests_dir,
    filename,
    manifest_id,
    includes=None,
    applications=None,
):
    manifests_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": "1.0",
        "id": manifest_id,
        "name": manifest_id.replace("-", " ").title(),
        "framework": {
            "name": "frappe",
            "version": "16",
            "release_channel": "stable",
            "target_ref": "version-16",
        },
        "profile": {
            "type": "product",
            "required": True,
            "install_by_default": True,
        },
        "resolution": {
            "strategy": "locked",
            "immutable_commit": True,
            "allow_development_branches": False,
            "fail_on_unverified_compatibility": True,
            "notes": [],
        },
        "validation": {},
        "includes": includes or [],
        "applications": applications if applications is not None else [
           {
               "name": "frappe",
               "repository": "https://github.com/frappe/frappe",
               "target_ref": "version-16",
               "required": True,
               "install_order": 0,
               "dependencies": [],
               "ref": None,
               "compatibility_status": "pending",
           }
       ],
    }

    path = manifests_dir / filename
    path.write_text(json.dumps(manifest, indent=2))

    return path

def shared_test_application():
    """Return an identical application definition for manifest tests."""

    return {
        "name": "frappe",
        "repository": "https://github.com/frappe/frappe",
        "target_ref": "version-16",
        "required": True,
        "install_order": 0,
        "dependencies": [],
        "ref": "a" * 40,
        "compatibility_status": "verified",
    }

@pytest.fixture
def loader(tmp_path):
    """Create a resolver using an isolated temporary manifest directory."""

    manifests_dir = tmp_path / "manifests"
    schemas_dir = tmp_path / "schemas"

    manifests_dir.mkdir()
    schemas_dir.mkdir()

    # Copy the actual project schema into the temporary environment.
    project_ndf_dir = Path(__file__).resolve().parents[1]

    shutil.copy2(
        project_ndf_dir / "schemas" / "application-manifest-v1.schema.json",
        schemas_dir / "application-manifest-v1.schema.json",
    )

    return ManifestLoader(manifests_dir)


@pytest.fixture
def sample_manifest(loader):
    """Create a minimal source manifest for lock tests."""

    source_path = loader.manifests_dir / "test-product.json"

    source_data = {
        "manifest_version": "1.0",
        "id": "test-product",
        "name": "Test Product",
    }

    source_path.write_text(
        json.dumps(source_data, indent=2),
        encoding="utf-8",
    )

    return {
        "manifest_version": "1.0",
        "id": "test-product",
        "name": "Test Product",
        "profile": {
            "type": "product",
            "required": True,
            "install_by_default": True,
        },
        "framework": {
            "name": "frappe",
            "version": "16",
        },
        "_source_path": str(source_path),
        "_loaded_includes": [],
    }


@pytest.fixture
def sample_applications():
    """Create a minimal application list."""

    return [
        {
            "name": "frappe",
            "repository": "https://github.com/frappe/frappe",
            "target_ref": "version-16",
            "ref": "a" * 40,
            "dependencies": [],
        }
    ]


@pytest.fixture
def generated_lock(loader, sample_manifest, sample_applications, tmp_path):
    """Generate and persist a valid sample lock."""

    lock_data = loader.build_lock_data(
        sample_manifest,
        sample_applications,
    )

    lock_path = tmp_path / "test-product.lock.json"

    loader.write_lock_file(
        lock_data,
        lock_path,
    )

    return lock_path, lock_data

@pytest.fixture
def cli_environment(tmp_path):
    """Create an isolated environment for CLI integration tests."""

    ndf_dir = tmp_path / "images" / "ndf"
    scripts_dir = ndf_dir / "scripts"
    manifests_dir = ndf_dir / "manifests"
    schemas_dir = ndf_dir / "schemas"
    locks_dir = ndf_dir / "locks"

    for directory in (
        scripts_dir,
        manifests_dir / "products",
        schemas_dir,
        locks_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    # Copy the actual resolver and schema.
    project_ndf_dir = Path(__file__).resolve().parents[1]

    shutil.copy2(
        project_ndf_dir / "scripts" / "resolve_manifest.py",
        scripts_dir / "resolve_manifest.py",
    )

    shutil.copy2(
        project_ndf_dir / "schemas" / "application-manifest-v1.schema.json",
        schemas_dir / "application-manifest-v1.schema.json",
    )

    # Create a local Git repository so tests don't depend on GitHub.
    repository_dir = tmp_path / "test-app-repository"
    repository_dir.mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repository_dir,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repository_dir,
        check=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "Manifest Test"],
        cwd=repository_dir,
        check=True,
    )

    (repository_dir / "README.md").write_text(
        "Test application",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "."],
        cwd=repository_dir,
        check=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repository_dir,
        check=True,
        capture_output=True,
    )

    repository_url = repository_dir.as_uri()

    manifest = {
        "manifest_version": "1.0",
        "id": "cli-test",
        "name": "CLI Test Product",

        "framework": {
            "name": "frappe",
            "version": "16",
            "release_channel": "stable",
            "target_ref": "version-16",
        },

        "profile": {
            "type": "product",
            "required": True,
            "install_by_default": True,
        },

        "resolution": {
            "strategy": "locked",
            "immutable_commit": True,
            "allow_development_branches": False,
            "fail_on_unverified_compatibility": True,
            "notes": [],
        },

        "validation": {},

        "applications": [
            {
                "name": "test_app",
                "repository": repository_url,
                "target_ref": "main",
                "required": True,
                "install_order": 1,
                "dependencies": [],
                "ref": None,
                "compatibility_status": "verified",
            }
        ],
    }

    manifest_path = manifests_dir / "products" / "cli-test.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return {
        "ndf_dir": ndf_dir,
        "script": scripts_dir / "resolve_manifest.py",
        "manifest_path": manifest_path,
        "lock_path": locks_dir / "cli-test.lock.json",
        "manifest_argument": "products/cli-test.json",
    }


# ---------------------------------------------------------
# Lock generation
# ---------------------------------------------------------

class TestLockGeneration:

    def test_build_lock_data(self, loader, sample_manifest, sample_applications):
        lock_data = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        assert lock_data["lock_version"] == 1
        assert lock_data["product"]["id"] == "test-product"
        assert len(lock_data["applications"]) == 1
        assert lock_data["applications"][0]["name"] == "frappe"

    def test_lock_generation_is_deterministic(
        self,
        loader,
        sample_manifest,
        sample_applications,
    ):
        first = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        second = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        assert first == second

    def test_write_lock_file(self, loader, sample_manifest, sample_applications, tmp_path):
        lock_data = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        lock_path = tmp_path / "test.lock.json"

        result = loader.write_lock_file(
            lock_data,
            lock_path,
        )

        assert result == lock_path
        assert lock_path.exists()

        written_data = json.loads(
            lock_path.read_text(encoding="utf-8")
        )

        assert written_data == lock_data


# ---------------------------------------------------------
# Lock validation
# ---------------------------------------------------------

class TestLockValidation:

    def test_valid_lock_passes(self, loader, sample_manifest, generated_lock):
        lock_path, _ = generated_lock

        assert loader.validate_lock_file(
            lock_path,
            sample_manifest,
        ) is True

    def test_modified_manifest_fails_checksum_validation(
        self,
        loader,
        sample_manifest,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        source_path = Path(sample_manifest["_source_path"])

        source_path.write_text(
            '{"id": "modified-product"}',
            encoding="utf-8",
        )

        with pytest.raises(
            ManifestError,
            match="Source manifest has changed",
        ):
            loader.validate_lock_file(
                lock_path,
                sample_manifest,
            )

    def test_modified_manifest_can_be_structurally_validated(
        self,
        loader,
        sample_manifest,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        source_path = Path(sample_manifest["_source_path"])

        source_path.write_text(
            '{"id": "modified-product"}',
            encoding="utf-8",
        )

        assert loader.validate_lock_file(
            lock_path,
            sample_manifest,
            verify_manifest_checksums=False,
        ) is True

    def test_invalid_lock_json_is_rejected(
        self,
        loader,
        sample_manifest,
        tmp_path,
    ):
        lock_path = tmp_path / "invalid.lock.json"
        lock_path.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(ManifestError, match="Unable to read lock file"):
            loader.validate_lock_file(
                lock_path,
                sample_manifest,
            )


# ---------------------------------------------------------
# Lock comparison
# ---------------------------------------------------------

class TestLockComparison:

    def test_unchanged_lock_has_no_changes(
        self,
        loader,
        sample_manifest,
        generated_lock,
    ):
        lock_path, lock_data = generated_lock

        changes = loader.compare_lock_files(
            lock_path,
            lock_data,
            sample_manifest,
        )

        assert changes == []

    def test_changed_manifest_is_detected(
        self,
        loader,
        sample_manifest,
        sample_applications,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        source_path = Path(sample_manifest["_source_path"])

        source_path.write_text(
            '{"id": "test-product", "modified": true}',
            encoding="utf-8",
        )

        new_lock_data = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        changes = loader.compare_lock_files(
            lock_path,
            new_lock_data,
            sample_manifest,
        )

        assert any(
            "Changed manifest content: test-product" in change
            for change in changes
        )

    def test_changed_application_reference_is_detected(
        self,
        loader,
        sample_manifest,
        sample_applications,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        updated_applications = [
            {
                **sample_applications[0],
                "ref": "b" * 40,
            }
        ]

        new_lock_data = loader.build_lock_data(
            sample_manifest,
            updated_applications,
        )

        changes = loader.compare_lock_files(
            lock_path,
            new_lock_data,
            sample_manifest,
        )

        assert any(
            "frappe.ref" in change
            for change in changes
        )

    def test_added_application_is_detected(
        self,
        loader,
        sample_manifest,
        sample_applications,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        updated_applications = sample_applications + [
            {
                "name": "erpnext",
                "repository": "https://github.com/frappe/erpnext",
                "target_ref": "version-16",
                "ref": "b" * 40,
                "dependencies": ["frappe"],
            }
        ]

        new_lock_data = loader.build_lock_data(
            sample_manifest,
            updated_applications,
        )

        changes = loader.compare_lock_files(
            lock_path,
            new_lock_data,
            sample_manifest,
        )

        assert any(
            "Added application: erpnext" in change
            for change in changes
        )

    def test_removed_application_is_detected(
        self,
        loader,
        sample_manifest,
        generated_lock,
    ):
        lock_path, _ = generated_lock

        new_lock_data = loader.build_lock_data(
            sample_manifest,
            [
                {
                    "name": "erpnext",
                    "repository": "https://github.com/frappe/erpnext",
                    "target_ref": "version-16",
                    "ref": "b" * 40,
                    "dependencies": [],
                }
            ],
        )

        changes = loader.compare_lock_files(
            lock_path,
            new_lock_data,
            sample_manifest,
        )

        assert any(
            "Removed application: frappe" in change
            for change in changes
        )

    def test_missing_previous_lock_is_reported(
        self,
        loader,
        sample_manifest,
        sample_applications,
        tmp_path,
    ):
        lock_path = tmp_path / "missing.lock.json"

        lock_data = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        changes = loader.compare_lock_files(
            lock_path,
            lock_data,
            sample_manifest,
        )

        assert changes
        assert any(
            "No previous lock file found" in change
            for change in changes
        )

    def test_invalid_previous_lock_is_rejected_without_modification(
        self,
        loader,
        sample_manifest,
        sample_applications,
        tmp_path,
    ):
        lock_path = tmp_path / "invalid.lock.json"

        original_content = '{"lock_version": 999}'

        lock_path.write_text(
            original_content,
            encoding="utf-8",
        )

        new_lock_data = loader.build_lock_data(
            sample_manifest,
            sample_applications,
        )

        with pytest.raises(ManifestError):
            loader.compare_lock_files(
                lock_path,
                new_lock_data,
                sample_manifest,
            )

        assert lock_path.read_text(encoding="utf-8") == original_content

class TestCheckMode:

    def test_check_passes_when_lock_is_current(self, cli_environment):
        environment = cli_environment

        # Generate the initial lock.
        generation = run_resolver(environment)

        assert generation.returncode == 0
        assert environment["lock_path"].exists()

        # Run check mode.
        result = run_resolver(environment, "--check")

        assert result.returncode == 0
        assert "No changes detected." in result.stdout
        assert "Lock file is up to date." in result.stdout

    def test_check_fails_when_lock_is_outdated(self, cli_environment):
        environment = cli_environment

        # Generate the initial lock.
        generation = run_resolver(environment)

        assert generation.returncode == 0

        # Modify the source manifest without changing its meaning.
        with environment["manifest_path"].open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write("\n")

        result = run_resolver(environment, "--check")

        assert result.returncode == 1
        assert "Lock file is outdated." in result.stdout
        assert "Changed manifest content: cli-test" in result.stdout

    def test_check_does_not_modify_existing_lock(self, cli_environment):
        environment = cli_environment

        # Generate the initial lock.
        generation = run_resolver(environment)

        assert generation.returncode == 0

        original_lock = environment["lock_path"].read_bytes()

        # Modify the manifest.
        with environment["manifest_path"].open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write("\n")

        # Run check mode.
        result = run_resolver(environment, "--check")

        assert result.returncode == 1

        # The previous lock must remain untouched.
        current_lock = environment["lock_path"].read_bytes()

        assert current_lock == original_lock

    def test_normal_execution_updates_outdated_lock(self, cli_environment):
        environment = cli_environment

        # Generate the initial lock.
        generation = run_resolver(environment)

        assert generation.returncode == 0

        original_lock = environment["lock_path"].read_bytes()

        # Modify the manifest.
        with environment["manifest_path"].open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write("\n")

        # Normal execution should update the lock.
        result = run_resolver(environment)

        assert result.returncode == 0
        assert "Changed manifest content: cli-test" in result.stdout
        assert "Lock file generated and validated" in result.stdout

        updated_lock = environment["lock_path"].read_bytes()

        assert updated_lock != original_lock

        # The updated lock should now pass check mode.
        check = run_resolver(environment, "--check")

        assert check.returncode == 0
        assert "Lock file is up to date." in check.stdout

    def test_check_fails_when_lock_does_not_exist(self, cli_environment):
        environment = cli_environment

        result = run_resolver(environment, "--check")

        assert result.returncode == 1
        assert "Lock file does not exist" in result.stderr

class TestRecursiveManifestLoading:

    def test_recursive_manifest_loading(self, loader):
        manifests_dir = loader.manifests_dir

        write_test_manifest(
            manifests_dir,
            "base.json",
            "base",
        )

        write_test_manifest(
            manifests_dir,
            "capability.json",
            "capability",
            includes=[
                {
                    "manifest": "base.json",
                    "required": True,
                }
            ],
        )

        write_test_manifest(
            manifests_dir,
            "product.json",
            "product",
            includes=[
                {
                    "manifest": "capability.json",
                    "required": True,
                }
            ],
        )

        result = loader.load("product.json")

        capability = result["_loaded_includes"][0]
        base = capability["_loaded_includes"][0]

        assert result["id"] == "product"
        assert capability["id"] == "capability"
        assert base["id"] == "base"

    def test_circular_manifest_include_is_detected(self, loader):
        manifests_dir = loader.manifests_dir

        write_test_manifest(
            manifests_dir,
            "first.json",
            "first",
            includes=[
                {
                    "manifest": "second.json",
                    "required": True,
                }
            ],
        )

        write_test_manifest(
            manifests_dir,
            "second.json",
            "second",
            includes=[
                {
                    "manifest": "first.json",
                    "required": True,
                }
            ],
        )

        with pytest.raises(
            ManifestError,
            match="Circular manifest inclusion detected",
        ):
            loader.load("first.json")

    def test_duplicate_manifest_is_loaded_only_once(self, loader):
        manifests_dir = loader.manifests_dir

        write_test_manifest(
            manifests_dir,
            "shared.json",
            "shared",
        )

        write_test_manifest(
            manifests_dir,
            "product.json",
            "product",
            includes=[
                {
                    "manifest": "shared.json",
                    "required": True,
                },
                {
                    "manifest": "shared.json",
                    "required": True,
                },
            ],
        )

        result = loader.load("product.json")

        included_ids = [
            item["id"]
            for item in result["_loaded_includes"]
        ]

        assert included_ids.count("shared") == 1

    def test_shared_manifest_across_branches_is_deduplicated(
        self,
        loader,
    ):
        manifests_dir = loader.manifests_dir

        application = shared_test_application()

        # Shared manifest
        write_test_manifest(
            manifests_dir,
            "shared.json",
            "shared",
            applications=[application],
        )

        # Two capabilities both include the same shared manifest
        write_test_manifest(
            manifests_dir,
            "capability-a.json",
            "capability-a",
            includes=[
                {
                    "manifest": "shared.json",
                    "required": True,
                }
            ],
            applications=[application],
        )

        write_test_manifest(
            manifests_dir,
            "capability-b.json",
            "capability-b",
            includes=[
                {
                    "manifest": "shared.json",
                    "required": True,
                }
            ],
            applications=[application],
        )

        # Product includes both capabilities
        write_test_manifest(
            manifests_dir,
            "product.json",
            "product",
            includes=[
                {
                    "manifest": "capability-a.json",
                    "required": True,
                },
                {
                    "manifest": "capability-b.json",
                    "required": True,
                },
            ],
            applications=[application],
        )

        product = loader.load("product.json")

        # 1. The shared manifest should be the same cached object
        capability_a = product["_loaded_includes"][0]
        capability_b = product["_loaded_includes"][1]

        shared_a = capability_a["_loaded_includes"][0]
        shared_b = capability_b["_loaded_includes"][0]

        assert shared_a is shared_b

        # 2. Application composition should deduplicate identical apps
        applications = loader.compose_applications(product)

        assert len(applications) == 1
        assert applications[0]["name"] == "frappe"

        # 3. Lock generation should record each manifest only once
        lock_data = loader.build_lock_data(
            product,
            applications,
        )

        manifest_paths = [
            entry["path"]
            for entry in lock_data["manifests"]
        ]

        assert len(manifest_paths) == len(set(manifest_paths))

        assert set(manifest_paths) == {
            "product.json",
            "capability-a.json",
            "capability-b.json",
            "shared.json",
        }

    def test_duplicate_manifest_id_from_different_files_is_rejected(
        self, loader
    ):
        manifests_dir = loader.manifests_dir

        write_test_manifest(
            manifests_dir,
            "first.json",
            "shared-identity",
        )

        write_test_manifest(
            manifests_dir,
            "second.json",
            "shared-identity",
        )

        write_test_manifest(
            manifests_dir,
            "product.json",
            "product",
            includes=[
                {"manifest": "first.json", "required": True},
                {"manifest": "second.json", "required": True},
            ],
        )

        with pytest.raises(
            ManifestError,
            match="Duplicate manifest ID 'shared-identity'",
        ):
            loader.load("product.json")

    def test_duplicate_manifest_id_in_optional_include_is_rejected(
        self, loader
    ):
        manifests_dir = loader.manifests_dir

        write_test_manifest(
            manifests_dir,
            "first.json",
            "shared-identity",
        )

        write_test_manifest(
            manifests_dir,
            "second.json",
            "shared-identity",
        )

        write_test_manifest(
            manifests_dir,
            "product.json",
            "product",
            includes=[
                {"manifest": "first.json", "required": True},
                {"manifest": "second.json", "required": False},
            ],
        )

        with pytest.raises(
            ManifestError,
            match="Duplicate manifest ID 'shared-identity'",
        ):
            loader.load("product.json")

class TestApplicationComposition:

    def test_duplicate_application_definitions_are_deduplicated(self, loader):
        application = {
            "name": "frappe",
            "repository": "https://github.com/frappe/frappe",
            "target_ref": "version-16",
            "required": True,
            "install_order": 0,
            "dependencies": [],
        }

        manifest = {
            "id": "product",
            "applications": [application],
            "_loaded_includes": [
                {
                    "id": "base",
                    "applications": [application.copy()],
                    "_loaded_includes": [],
                }
            ],
        }

        applications = loader.compose_applications(manifest)

        names = [app["name"] for app in applications]

        assert names.count("frappe") == 1

    def test_conflicting_application_definitions_are_rejected(self,loader):
        first_definition = {
            "name": "frappe",
            "repository": "https://github.com/frappe/frappe",
            "target_ref": "version-16",
            "required": True,
            "install_order": 0,
            "dependencies": [],
        }

        conflicting_definition = {
            **first_definition,
            "target_ref": "develop",
        }

        manifest = {
            "id": "product",
            "applications": [first_definition],
            "_loaded_includes": [
                {
                    "id": "base",
                    "applications": [conflicting_definition],
                    "_loaded_includes": [],
                }
            ],
        }

        with pytest.raises(
            ManifestError,
            match="Conflicting application definition",
        ):
            loader.compose_applications(manifest)

class TestApplicationDependencies:

    def test_missing_application_dependency_is_rejected(self, loader):
        applications = [
            {
                "name": "dt_dalali_ecommerce",
                "dependencies": ["dt_ecommerce"],
            }
        ]

        with pytest.raises(
            ManifestError,
            match="Application dependency validation failed",
        ):
            loader.validate_dependencies(applications)

    def test_circular_application_dependencies_are_rejected(self, loader):
        applications = [
            {
                "name": "app_a",
                "dependencies": ["app_b"],
            },
            {
                "name": "app_b",
                "dependencies": ["app_c"],
            },
            {
                "name": "app_c",
                "dependencies": ["app_a"],
            },
        ]

        loader.validate_dependencies(applications)

        with pytest.raises(
            ManifestError,
            match="Circular application dependency",
        ):
            loader.resolve_install_order(applications)

    def test_installation_order_respects_dependencies(self, loader):
        applications = [
            {
                "name": "dt_dalali_ecommerce",
                "dependencies": [
                    "dt_ecommerce",
                    "dt_recomendations",
                ],
            },
            {
                "name": "dt_recomendations",
                "dependencies": ["dt_ecommerce"],
            },
            {
                "name": "dt_ecommerce",
                "dependencies": ["webshop"],
            },
            {
                "name": "webshop",
                "dependencies": ["erpnext"],
            },
            {
                "name": "erpnext",
                "dependencies": ["frappe"],
            },
            {
                "name": "frappe",
                "dependencies": [],
            },
        ]

        loader.validate_dependencies(applications)

        ordered = loader.resolve_install_order(applications)
        ordered_names = [app["name"] for app in ordered]

        assert ordered_names.index("frappe") < ordered_names.index("erpnext")
        assert ordered_names.index("erpnext") < ordered_names.index("webshop")
        assert ordered_names.index("webshop") < ordered_names.index("dt_ecommerce")
        assert ordered_names.index("dt_ecommerce") < ordered_names.index("dt_recomendations")
        assert ordered_names.index("dt_recomendations") < ordered_names.index("dt_dalali_ecommerce")