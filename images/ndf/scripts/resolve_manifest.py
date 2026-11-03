#!/usr/bin/env python3
import subprocess
import argparse
import json
import sys
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator
import hashlib
import re


class ManifestError(Exception):
    """Raised when manifest loading or resolution fails."""

class DuplicateManifestIDError(ManifestError):
    """Raised when different manifest files declare the same ID."""


class ManifestLoader:
    def __init__(self, manifests_dir: Path):
        self.manifests_dir = manifests_dir.resolve()
        self.loaded = {}
        self.loading_stack = []
        self.manifest_ids = {}

    def resolve_path(self, manifest_path: str) -> Path:
        """Resolve a manifest path relative to the manifests root."""

        path = (self.manifests_dir / manifest_path).resolve()

        if not path.is_relative_to(self.manifests_dir):
            raise ManifestError(
                f"Manifest path escapes the manifests directory: {manifest_path}"
            )

        if not path.is_file():
            raise ManifestError(
                f"Manifest not found: {manifest_path}"
            )

        return path

    def load_json(self, path: Path) -> dict:
        """Load and parse a JSON manifest."""

        try:
            with path.open("r", encoding="utf-8") as file:
                manifest = json.load(file)

        except json.JSONDecodeError as exc:
            raise ManifestError(
                f"Invalid JSON in {path.name}: {exc}"
            ) from exc

        except OSError as exc:
            raise ManifestError(
                f"Unable to read {path}: {exc}"
            ) from exc

        if not isinstance(manifest, dict):
            raise ManifestError(
                f"Manifest must contain a JSON object: {path.name}"
            )

        return manifest

    def load(self, manifest_path: str) -> dict:
        """Load a manifest and recursively load its includes."""

        path = self.resolve_path(manifest_path)

        if path in self.loading_stack:
            cycle = self.loading_stack + [path]
            chain = " -> ".join(p.name for p in cycle)

            raise ManifestError(
                f"Circular manifest inclusion detected: {chain}"
            )

        if path in self.loaded:
            return self.loaded[path]

        manifest = self.load_json(path)
        self.validate(manifest, path)

        if "id" not in manifest:
            raise ManifestError(
                f"Manifest is missing its ID: {path.name}"
            )

        self.loading_stack.append(path)

        try:
            includes = manifest.get("includes", [])

            if not isinstance(includes, list):
                raise ManifestError(
                    f"'includes' must be an array in {path.name}"
                )

            loaded_includes = []
            loaded_include_paths = set()

            for include in includes:

                if not isinstance(include, dict):
                    raise ManifestError(
                        f"Invalid include entry in {path.name}"
                    )

                include_path = include.get("manifest")

                if not isinstance(include_path, str) or not include_path:
                    raise ManifestError(
                        f"Include entry has no valid manifest path in {path.name}"
                    )

                required = include.get("required", True)

                if not isinstance(required, bool):
                    raise ManifestError(
                        f"Include 'required' must be boolean in {path.name}"
                    )

                try:
                    resolved_include_path = self.resolve_path(include_path)
                    child = self.load(include_path)

                except ManifestError as exc:
                    if required or isinstance(exc, DuplicateManifestIDError):
                        raise

                    print(
                        f"WARNING: Optional manifest unavailable: {include_path}",
                        file=sys.stderr,
                    )
                    continue

                # Prevent the same manifest from appearing more than once
                # in this parent's loaded includes.
                if resolved_include_path not in loaded_include_paths:
                    loaded_includes.append(child)
                    loaded_include_paths.add(resolved_include_path)

            manifest_id = manifest["id"]
            existing_path = self.manifest_ids.get(manifest_id)

            if existing_path is not None and existing_path != path:
                raise DuplicateManifestIDError(
                    f"Duplicate manifest ID '{manifest_id}' detected.\n"
                    f"First defined in: {existing_path}\n"
                    f"Conflicting definition in: {path}"
                )

            manifest["_source_path"] = str(path)
            manifest["_loaded_includes"] = loaded_includes

            self.manifest_ids[manifest_id] = path
            self.loaded[path] = manifest

            return manifest

        finally:
            self.loading_stack.pop()

    def validate(self, manifest: dict, path: Path):
        """Validate a manifest against the NDF manifest schema."""

        schema_path = (
            self.manifests_dir.parent
            / "schemas"
            / "application-manifest-v1.schema.json"
        )

        try:
            with schema_path.open("r", encoding="utf-8") as file:
                schema = json.load(file)

        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(
                f"Unable to load manifest schema: {exc}"
            ) from exc

        validator = Draft202012Validator(schema)

        errors = sorted(
            validator.iter_errors(manifest),
            key=lambda error: list(error.absolute_path),
        )

        if errors:
            details = []

            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path)
                location = location or "<root>"

                details.append(f"  - {location}: {error.message}")

            raise ManifestError(
                f"Schema validation failed for {path.name}:\n"
                + "\n".join(details)
            )

    def compose_applications(self, manifest: dict) -> list:
        """Collect required applications from the complete manifest hierarchy."""

        applications = {}
        sources = {}

        def collect(current: dict):
            # Process included manifests first.
            for child in current.get("_loaded_includes", []):
                collect(child)

            for app in current.get("applications", []):
                if not app.get("required", False):
                    continue

                name = app["name"]

                if name in applications:
                    existing = applications[name]

                    # Allow identical definitions, but reject conflicts.
                    if existing != app:
                        raise ManifestError(
                            f"Conflicting application definition: {name}\n"
                            f"First defined in: {sources[name]}\n"
                            f"Conflicting definition in: {current['id']}"
                        )

                    continue

                applications[name] = app
                sources[name] = current["id"]

        collect(manifest)

        return list(applications.values())

    def validate_dependencies(self, applications: list):
        """Ensure all application dependencies exist in the composition."""

        available_apps = {
            app["name"]: app
            for app in applications
        }

        errors = []

        for app in applications:
            app_name = app["name"]

            for dependency in app.get("dependencies", []):
                if dependency not in available_apps:
                    errors.append(
                        f"{app_name} requires '{dependency}', "
                        "but it is not included in the composition."
                    )

        if errors:
            raise ManifestError(
                "Application dependency validation failed:\n"
                + "\n".join(f"  - {error}" for error in errors)
            )

        return True

    def resolve_install_order(self, applications: list) -> list:
        """Calculate application installation order using dependencies."""

        available_apps = {
            app["name"]: app
            for app in applications
        }

        visited = set()
        visiting = []
        ordered = []

        def visit(app_name: str):
            if app_name in visiting:
                cycle_start = visiting.index(app_name)
                cycle = visiting[cycle_start:] + [app_name]

                raise ManifestError(
                    "Circular application dependency detected:\n"
                    + " -> ".join(cycle)
                )

            if app_name in visited:
                return

            visiting.append(app_name)

            app = available_apps[app_name]

            for dependency in sorted(app.get("dependencies", [])):
                if dependency not in available_apps:
                    raise ManifestError(
                        f"Missing dependency '{dependency}' "
                        f"required by '{app_name}'"
                    )

                visit(dependency)

            visiting.pop()
            visited.add(app_name)
            ordered.append(app)

        for app_name in sorted(available_apps):
            visit(app_name)

        return ordered

    def resolve_git_ref(self, repository: str, target_ref: str) -> str:
        """Resolve a Git branch or tag to an immutable commit SHA."""

        refs = [
            f"refs/heads/{target_ref}",
            f"refs/tags/{target_ref}",
            f"refs/tags/{target_ref}^{{}}",
        ]

        try:
            result = subprocess.run(
                ["git", "ls-remote", repository, *refs],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )

        except subprocess.TimeoutExpired as exc:
            raise ManifestError(
                f"Git reference resolution timed out: {repository}"
            ) from exc

        except subprocess.CalledProcessError as exc:
            raise ManifestError(
                f"Unable to resolve Git reference '{target_ref}' "
                f"from {repository}: {exc.stderr.strip()}"
            ) from exc

        resolved = {}

        for line in result.stdout.splitlines():
            sha, ref = line.split("\t", 1)
            resolved[ref] = sha

        branch_ref = f"refs/heads/{target_ref}"
        tag_ref = f"refs/tags/{target_ref}"
        peeled_tag_ref = f"refs/tags/{target_ref}^{{}}"

        if branch_ref in resolved:
            return resolved[branch_ref]

        if peeled_tag_ref in resolved:
            return resolved[peeled_tag_ref]

        if tag_ref in resolved:
            return resolved[tag_ref]

        raise ManifestError(
            f"Git reference '{target_ref}' not found in {repository}"
        )

    def resolve_application_refs(self, applications: list) -> list:
        """Resolve all application Git references to immutable commits."""

        for app in applications:
            repository = app.get("repository")
            target_ref = app.get("target_ref")

            if not repository or not target_ref:
                raise ManifestError(
                    f"Application '{app['name']}' is missing "
                    "repository or target_ref."
                )

            app["ref"] = self.resolve_git_ref(repository, target_ref)

            print(
                f"Resolved {app['name']}: "
                f"{target_ref} -> {app['ref']}"
            )

        return applications

    def build_lock_data(
        self,
        manifest: dict,
        applications: list,
    ) -> dict[str, Any]:
        """Build deterministic application lock data in memory."""

        loaded_manifests = []
        collected_manifest_paths = set()


        def collect_manifests(current: dict):
            source_path = Path(current["_source_path"]).resolve()

            # Prevent shared manifests from appearing multiple times
            # when reached through different branches.
            if source_path in collected_manifest_paths:
                return

            collected_manifest_paths.add(source_path)

            relative_path = source_path.relative_to(
                self.manifests_dir
            )

            checksum = hashlib.sha256(
                source_path.read_bytes()
            ).hexdigest()

            loaded_manifests.append({
                "id": current["id"],
                "path": relative_path.as_posix(),
                "sha256": checksum,
            })

            for child in current.get("_loaded_includes", []):
                collect_manifests(child)


        collect_manifests(manifest)

        return {
            "lock_version": 1,
            "resolver": {
                "name": "ndf-manifest-resolver",
                "version": "1.0.0",
            },
            "product": {
                "id": manifest["id"],
                "name": manifest["name"],
                "manifest_version": manifest["manifest_version"],
                "profile": manifest["profile"],
            },
            "framework": manifest["framework"],
            "manifests": loaded_manifests,
            "applications": [
                {
                    "name": app["name"],
                    "repository": app["repository"],
                    "target_ref": app["target_ref"],
                    "ref": app["ref"],
                    "dependencies": app.get("dependencies", []),
                    "installation_order": index,
                }
                for index, app in enumerate(applications, start=1)
            ],
        }

    def write_lock_file(
        self,
        lock_data: dict,
        output_path: Path,
    ) -> Path:
        """Write lock data atomically to disk."""

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = output_path.with_suffix(
            output_path.suffix + ".tmp"
        )

        try:
            temporary_path.write_text(
                json.dumps(
                    lock_data,
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )

            temporary_path.replace(output_path)

        except OSError as exc:
            raise ManifestError(
                f"Unable to write lock file {output_path}: {exc}"
            ) from exc

        return output_path

    def validate_lock_file(
        self,
        lock_path: Path,
        expected_manifest: dict,
        verify_manifest_checksums: bool = True,
    ):
        """Validate a lock file and optionally verify source manifest checksums."""

        try:
            with lock_path.open("r", encoding="utf-8") as file:
                lock = json.load(file)

        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(
                f"Unable to read lock file {lock_path}: {exc}"
            ) from exc

        if not isinstance(lock, dict):
            raise ManifestError("Lock file must contain a JSON object.")

        # 1. Lock format version
        if lock.get("lock_version") != 1:
            raise ManifestError(
                f"Unsupported lock version: {lock.get('lock_version')}"
            )

        # 2. Product identity
        product = lock.get("product")

        if not isinstance(product, dict):
            raise ManifestError("Lock file has an invalid product section.")

        if product.get("id") != expected_manifest["id"]:
            raise ManifestError(
                "Lock file product ID does not match the requested manifest."
            )

        if product.get("manifest_version") != expected_manifest["manifest_version"]:
            raise ManifestError(
                "Lock file manifest version does not match the source manifest."
            )

        # 3. Source manifest checksums
        manifests = lock.get("manifests")

        if not isinstance(manifests, list) or not manifests:
            raise ManifestError("Lock file has no source manifests.")

        seen_paths = set()
        seen_ids = set()

        for entry in manifests:
            if not isinstance(entry, dict):
                raise ManifestError("Invalid source manifest entry in lock file.")

            manifest_id = entry.get("id")
            relative_path = entry.get("path")
            expected_sha256 = entry.get("sha256")

            if not all(isinstance(value, str) and value for value in (
                manifest_id,
                relative_path,
                expected_sha256,
            )):
                raise ManifestError("Incomplete source manifest entry in lock file.")

            if manifest_id in seen_ids:
                raise ManifestError(
                    f"Duplicate manifest ID in lock file: {manifest_id}"
                )

            if relative_path in seen_paths:
                raise ManifestError(
                    f"Duplicate manifest path in lock file: {relative_path}"
                )

            seen_ids.add(manifest_id)
            seen_paths.add(relative_path)

            if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
                raise ManifestError(
                    f"Invalid SHA-256 checksum for manifest: {relative_path}"
                )

            source_path = self.resolve_path(relative_path)

            if not source_path.is_file():
                raise ManifestError(
                    f"Source manifest does not exist: {relative_path}"
                )

            if verify_manifest_checksums:
                actual_sha256 = hashlib.sha256(
                    source_path.read_bytes()
                ).hexdigest()

                if actual_sha256 != expected_sha256:
                    raise ManifestError(
                        f"Source manifest has changed since lock generation: "
                        f"{relative_path}"
                    )

        if expected_manifest["id"] not in seen_ids:
            raise ManifestError(
                "Requested product manifest is missing from the lock file."
            )

        # 4. Application entries and immutable Git references
        applications = lock.get("applications")

        if not isinstance(applications, list) or not applications:
            raise ManifestError("Lock file contains no applications.")

        available_apps = {}
        previous_order = 0

        for app in applications:
            if not isinstance(app, dict):
                raise ManifestError("Invalid application entry in lock file.")

            name = app.get("name")
            repository = app.get("repository")
            target_ref = app.get("target_ref")
            commit = app.get("ref")
            order = app.get("installation_order")
            dependencies = app.get("dependencies")

            if not isinstance(name, str) or not name:
                raise ManifestError("Application has an invalid name.")

            if name in available_apps:
                raise ManifestError(
                    f"Duplicate application in lock file: {name}"
                )

            if not isinstance(repository, str) or not repository:
                raise ManifestError(
                    f"Application '{name}' has no repository."
                )

            if not isinstance(target_ref, str) or not target_ref:
                raise ManifestError(
                    f"Application '{name}' has no target_ref."
                )

            if not isinstance(commit, str) or not re.fullmatch(
                r"[a-fA-F0-9]{40}", commit
            ):
                raise ManifestError(
                    f"Application '{name}' has an invalid Git commit SHA."
                )

            if (
                not isinstance(order, int)
                or isinstance(order, bool)
                or order != previous_order + 1
            ):
                raise ManifestError(
                    f"Invalid installation order for application '{name}'."
                )

            if (
                not isinstance(dependencies, list)
                or any(not isinstance(dep, str) or not dep for dep in dependencies)
                or len(dependencies) != len(set(dependencies))
            ):
                raise ManifestError(
                    f"Invalid dependencies for application '{name}'."
                )

            available_apps[name] = app
            previous_order = order

        # 5. Dependency existence and installation order
        installed_apps = set()

        for app in applications:
            name = app["name"]

            for dependency in app["dependencies"]:
                if dependency not in available_apps:
                    raise ManifestError(
                        f"Application '{name}' requires missing dependency "
                        f"'{dependency}'."
                    )

                if dependency not in installed_apps:
                    raise ManifestError(
                        f"Application '{name}' appears before its dependency "
                        f"'{dependency}' in the lock file."
                    )

            installed_apps.add(name)

        return True

    def compare_lock_files(
        self,
        previous_lock_path: Path,
        new_lock_data: dict,
        manifest: dict,
    ) -> list:
        """Compare an existing lock file with newly resolved lock data."""

        if not previous_lock_path.exists():
            return ["No previous lock file found. A new lock will be created."]

        try:
            previous_lock = json.loads(
                previous_lock_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(
                f"Unable to read previous lock file "
                f"{previous_lock_path}: {exc}"
            ) from exc

        # Validate structure, but allow source checksum changes.
        self.validate_lock_file(
            previous_lock_path,
            manifest,
            verify_manifest_checksums=False,
        )

        changes = []

        # Compare top-level metadata.
        for section in ("product", "framework", "lock_version", "resolver"):
            old_value = previous_lock.get(section)
            new_value = new_lock_data.get(section)

            if old_value != new_value:
                changes.append(
                    f"Changed {section}: {old_value} -> {new_value}"
                )

        # Compare manifests by manifest ID.
        old_manifests = {
            item["id"]: item
            for item in previous_lock.get("manifests", [])
        }

        new_manifests = {
            item["id"]: item
            for item in new_lock_data.get("manifests", [])
        }

        for manifest_id in sorted(new_manifests.keys() - old_manifests.keys()):
            changes.append(f"Added manifest: {manifest_id}")

        for manifest_id in sorted(old_manifests.keys() - new_manifests.keys()):
            changes.append(f"Removed manifest: {manifest_id}")

        for manifest_id in sorted(old_manifests.keys() & new_manifests.keys()):
            old_item = old_manifests[manifest_id]
            new_item = new_manifests[manifest_id]

            if old_item.get("path") != new_item.get("path"):
                changes.append(f"Changed manifest path: {manifest_id}")

            if old_item.get("sha256") != new_item.get("sha256"):
                changes.append(f"Changed manifest content: {manifest_id}")

        # Compare applications by application name.
        old_apps = {
            item["name"]: item
            for item in previous_lock.get("applications", [])
        }

        new_apps = {
            item["name"]: item
            for item in new_lock_data.get("applications", [])
        }

        for app_name in sorted(new_apps.keys() - old_apps.keys()):
            changes.append(f"Added application: {app_name}")

        for app_name in sorted(old_apps.keys() - new_apps.keys()):
            changes.append(f"Removed application: {app_name}")

        compared_fields = (
            "repository",
            "target_ref",
            "ref",
            "dependencies",
            "installation_order",
        )

        for app_name in sorted(old_apps.keys() & new_apps.keys()):
            old_app = old_apps[app_name]
            new_app = new_apps[app_name]

            for field in compared_fields:
                if old_app.get(field) != new_app.get(field):
                    changes.append(
                        f"Changed {app_name}.{field}: "
                        f"{old_app.get(field)} -> {new_app.get(field)}"
                    )

        return changes

def print_manifest_tree(manifest: dict, level: int = 0):
    """Display the loaded manifest hierarchy."""

    indent = "  " * level

    print(
        f"{indent}- {manifest['id']} "
        f"({Path(manifest['_source_path']).name})"
    )

    for child in manifest.get("_loaded_includes", []):
        print_manifest_tree(child, level + 1)


def main():
    parser = argparse.ArgumentParser(
        description="NDF Frappe Manifest Resolver"
    )

    parser.add_argument(
        "manifest",
        help="Product manifest path relative to images/ndf/manifests",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether the existing lock file is up to date without modifying it.",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    ndf_dir = script_dir.parent
    manifests_dir = ndf_dir / "manifests"

    loader = ManifestLoader(manifests_dir)

    # 1. Load manifest tree
    try:
        manifest = loader.load(args.manifest)

    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nManifest loading successful.\n")
    print_manifest_tree(manifest)

    print(f"\nTotal unique manifests loaded: {len(loader.loaded)}")

    # 2. Compose applications
    try:
        applications = loader.compose_applications(manifest)

        loader.validate_dependencies(applications)

    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nTotal unique applications composed: {len(applications)}")
    print("\nApplication dependency validation successful.")

    # 3. Resolve installation order
    try:
        ordered_applications = loader.resolve_install_order(
            applications
        )

    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nApplication installation order:")

    for index, app in enumerate(ordered_applications, start=1):
        print(f"  {index:02d}. {app['name']}")

    # 4. Resolve immutable Git references
    try:
        ordered_applications = loader.resolve_application_refs(
            ordered_applications
        )

    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nApplication Git references resolved.")

    # 5. Determine lock file location
    lock_filename = f"{Path(args.manifest).stem}.lock.json"

    lock_path = (
        ndf_dir
        / "locks"
        / lock_filename
    )

    # 6. Build new lock data in memory
    try:
        lock_data = loader.build_lock_data(
            manifest,
            ordered_applications,
        )

        # 7. Check whether a previous lock exists
        if args.check and not lock_path.exists():
            print(
                f"\nERROR: Lock file does not exist: {lock_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        # 8. Compare against the previous lock
        changes = loader.compare_lock_files(
            lock_path,
            lock_data,
            manifest,
        )

        print("\nLock file comparison:")

        if changes:
            for change in changes:
                print(f"  - {change}")
        else:
            print("  No changes detected.")

        # 9. Handle check-only mode
        if args.check:
            if changes:
                print("\nERROR: Lock file is outdated.")
                sys.exit(1)

            print("\nLock file is up to date.")
            return

        # 10. Write the new lock file
        loader.write_lock_file(
            lock_data,
            lock_path,
        )

        # 11. Validate the newly written lock
        loader.validate_lock_file(
            lock_path,
            manifest,
        )

    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nLock file generated and validated: {lock_path}")

if __name__ == "__main__":
    main()