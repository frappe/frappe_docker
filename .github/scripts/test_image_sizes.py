"""Unit and HTTP integration tests; no Docker daemon or external service needed."""

import argparse
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import image_sizes as sizes

MIB = 1024 * 1024
POLICY = {"max_growth_percent": 5, "max_growth_bytes": 100 * MIB}
REPOSITORY = "frappe/frappe_docker"
WORKFLOW = ".github/workflows/core-build-stable.yml"


def report(size=1000 * MIB, arch="amd64", run_id=10):
    return {
        "schema_version": 1,
        "repo": "erpnext",
        "release_line": "16",
        "arch": arch,
        "inputs": {
            "frappe_version": "v16.52.0",
            "erpnext_version": "v16.51.1",
            "python_version": "3.14",
            "node_version": "24",
            "debian_base": "trixie",
        },
        "source": {"run_id": run_id, "sha": "abc"},
        "images": {
            "erpnext": {
                "compressed_bytes": size,
                "layers": [
                    {"digest": "sha256:abc", "bytes": size, "command": "COPY bench"}
                ],
                "history": ["COPY bench"],
            }
        },
    }


def archive(payload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("report.json", json.dumps(payload))
    return buffer.getvalue()


class GrowthTests(unittest.TestCase):
    def test_both_limits_must_be_exceeded(self):
        for previous, current, expected in (
            (1000, 1200, True),
            (1000, 1100, False),  # Exactly 100 MiB is permitted.
            (4000, 4200, False),  # Exactly 5% is permitted.
            (4000, 4190, False),
            (100, 150, False),
            (1000, 900, False),
        ):
            with self.subTest(previous=previous, current=current):
                self.assertEqual(
                    sizes.growth_exceeds(current * MIB, previous * MIB, POLICY),
                    expected,
                )

    def test_missing_baseline_reports_sizes(self):
        current = report()
        summary, failures = sizes.compare(current, None, POLICY)
        self.assertIn("next successful", summary)
        self.assertEqual(failures, [])

    def test_report_shows_delta_and_large_layers(self):
        summary, failures = sizes.compare(report(1200 * MIB), report(), POLICY)
        self.assertEqual(len(failures), 1)
        self.assertIn("200.0 MiB (+20.0%)", summary)
        self.assertIn("largest layers", summary)

    def test_changed_inputs_are_explicit_and_still_checked(self):
        current = report(1200 * MIB)
        current["inputs"]["erpnext_version"] = "v16.52.0"
        summary, failures = sizes.compare(current, report(), POLICY)
        self.assertIn("Build inputs changed", summary)
        self.assertTrue(failures)

    def test_image_sets_cannot_silently_change(self):
        previous = report()
        previous["images"]["base"] = previous["images"]["erpnext"]
        with self.assertRaisesRegex(ValueError, "different image targets"):
            sizes.compare(report(), previous, POLICY)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.run = {
            "id": 10,
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "head_repository": {"full_name": REPOSITORY},
            "path": WORKFLOW,
        }
        self.artifacts = [
            {
                "id": 101 + index,
                "name": sizes.artifact_name("erpnext", "16", arch),
                "expired": False,
                "workflow_run": {
                    "id": 10,
                    "head_branch": "main",
                    "repository_id": 1,
                    "head_repository_id": 1,
                },
            }
            for index, arch in enumerate(sizes.ARCHITECTURES)
        ]

    def api(self, endpoint, binary=False):
        self.calls.append(endpoint)
        if "/zip" in endpoint:
            self.assertTrue(binary)
            return archive(report())
        if "/runs/10/artifacts" in endpoint:
            return {"artifacts": self.artifacts}
        if endpoint.endswith("/runs/10"):
            return self.run
        if "/actions/artifacts?" in endpoint:
            return {"artifacts": self.artifacts[:1]}
        self.fail(f"Unexpected API call: {endpoint}")

    def find(self):
        return sizes.find_baseline(REPOSITORY, WORKFLOW, "erpnext", "16", 20, self.api)

    def test_successful_main_run_provides_both_architectures(self):
        baseline, ids = self.find()
        self.assertEqual(baseline["source"]["run_id"], 10)
        self.assertEqual(ids, {"amd64": 101, "arm64": 102})

    def test_failed_pr_wrong_branch_repository_and_workflow_are_rejected(self):
        for change in (
            {"conclusion": "failure"},
            {"conclusion": None},
            {"event": "pull_request"},
            {"event": "pull_request_target"},
            {"head_branch": "feature"},
            {"head_repository": {"full_name": "someone/frappe_docker"}},
            {"path": ".github/workflows/unrelated.yml"},
        ):
            with self.subTest(change=change):
                with patch.dict(self.run, change):
                    self.assertEqual(self.find(), (None, {}))

    def test_expired_fork_and_future_artifacts_are_rejected_before_download(self):
        for change in (
            {"expired": True},
            {
                "workflow_run": {
                    **self.artifacts[0]["workflow_run"],
                    "head_repository_id": 2,
                }
            },
            {"workflow_run": {**self.artifacts[0]["workflow_run"], "id": 21}},
        ):
            with self.subTest(change=change):
                self.calls.clear()
                with patch.dict(self.artifacts[0], change):
                    self.assertEqual(self.find(), (None, {}))
                self.assertEqual(len(self.calls), 1)

    def test_missing_architecture_prevents_partial_baseline(self):
        self.artifacts.pop()
        self.assertEqual(self.find(), (None, {}))

    def test_a_failed_newer_run_does_not_replace_a_successful_baseline(self):
        previous_api = self.api
        newer = copy.deepcopy(self.artifacts[0])
        newer["id"] = 103
        newer["workflow_run"]["id"] = 11

        def api(endpoint, binary=False):
            if "/actions/artifacts?" in endpoint:
                return {"artifacts": [newer, self.artifacts[0]]}
            if endpoint.endswith("/runs/11"):
                return {**self.run, "id": 11, "conclusion": "failure"}
            return previous_api(endpoint, binary=binary)

        baseline, ids = sizes.find_baseline(
            REPOSITORY, WORKFLOW, "erpnext", "16", 20, api
        )
        self.assertEqual(baseline["source"]["run_id"], 10)
        self.assertEqual(ids, {"amd64": 101, "arm64": 102})

    def test_an_older_run_finishing_late_does_not_replace_a_newer_baseline(self):
        previous_api = self.api
        newer = copy.deepcopy(self.artifacts)
        for item in newer:
            item["id"] += 100
            item["workflow_run"]["id"] = 11

        def api(endpoint, binary=False):
            if "/actions/artifacts?" in endpoint:
                return {"artifacts": [self.artifacts[0], newer[0]]}
            if endpoint.endswith("/runs/11"):
                return {**self.run, "id": 11}
            if "/runs/11/artifacts" in endpoint:
                return {"artifacts": newer}
            if endpoint.endswith("/201/zip"):
                return archive(report(run_id=11))
            return previous_api(endpoint, binary=binary)

        baseline, ids = sizes.find_baseline(
            REPOSITORY, WORKFLOW, "erpnext", "16", 20, api
        )
        self.assertEqual(baseline["source"]["run_id"], 11)
        self.assertEqual(ids, {"amd64": 201, "arm64": 202})

    def test_api_failure_is_not_treated_as_first_run(self):
        with patch.object(sizes, "github_api", side_effect=RuntimeError("unavailable")):
            with self.assertRaises(RuntimeError):
                sizes.find_baseline(
                    REPOSITORY, WORKFLOW, "erpnext", "16", 20, sizes.github_api
                )

    def test_pr_versions_are_taken_from_the_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "outputs"
            environment = {
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@refs/pull/1/merge",
                "GITHUB_RUN_ID": "20",
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_OUTPUT": str(output),
            }
            with (
                patch.dict(os.environ, environment),
                patch.object(
                    sizes, "find_baseline", return_value=(report(), {"amd64": 101})
                ),
                patch.object(sizes, "get_latest_tag") as resolve,
            ):
                sizes.prepare(argparse.Namespace(repo="erpnext", version="16"))
                resolve.assert_not_called()
            self.assertIn("frappe_version=v16.52.0\n", output.read_text())
            self.assertIn("erpnext_version=v16.51.1\n", output.read_text())

    def test_main_and_first_run_resolve_latest_versions_automatically(self):
        for event, baseline in (("push", report()), ("pull_request", None)):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "outputs"
                environment = {
                    "GITHUB_REPOSITORY": REPOSITORY,
                    "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@refs/heads/main",
                    "GITHUB_RUN_ID": "20",
                    "GITHUB_EVENT_NAME": event,
                    "GITHUB_OUTPUT": str(output),
                }
                with (
                    patch.dict(os.environ, environment),
                    patch.object(sizes, "find_baseline", return_value=(baseline, {})),
                    patch.object(
                        sizes, "get_latest_tag", return_value="v16.99.0"
                    ) as resolve,
                ):
                    sizes.prepare(argparse.Namespace(repo="erpnext", version="16"))
                self.assertEqual(resolve.call_count, 2)
                self.assertIn("frappe_version=v16.99.0\n", output.read_text())


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.routes = {}
        self.requests = []
        self.config = {
            "os": "linux",
            "architecture": "amd64",
            "history": [
                {
                    "created_by": "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench"
                },
                {
                    "created_by": "WORKDIR /home/frappe/frappe-bench",
                    "empty_layer": True,
                },
                {"created_by": "RUN chmod g=u /home/frappe/frappe-bench"},
                {"created_by": 'CMD ["start.sh"]', "empty_layer": True},
            ],
        }
        self.manifest = {
            "schemaVersion": 2,
            "config": {"digest": "sha256:config"},
            "layers": [
                {"digest": "sha256:bench", "size": 900 * MIB},
                {"digest": "sha256:assets", "size": 100 * MIB},
            ],
        }
        index = {
            "manifests": [
                {
                    "digest": "sha256:attestation",
                    "platform": {"os": "unknown", "architecture": "unknown"},
                },
                {
                    "digest": "sha256:amd64",
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
                {
                    "digest": "sha256:arm64",
                    "platform": {"os": "linux", "architecture": "arm64"},
                },
            ]
        }
        for name, tag in (
            ("base", "v16.52.0"),
            ("build", "v16.51.1"),
            ("erpnext", "v16.51.1"),
        ):
            prefix = f"/v2/frappe/{name}"
            self.routes[f"{prefix}/manifests/{tag}"] = index
            self.routes[f"{prefix}/manifests/sha256:amd64"] = self.manifest
            self.routes[f"{prefix}/blobs/sha256:config"] = self.config
        routes, requests = self.routes, self.requests

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                payload = routes.get(self.path)
                self.send_response(200 if payload else 404)
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.registry = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_index_platform_selection_and_empty_history_entries(self):
        image = sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")
        self.assertEqual(image["compressed_bytes"], 1000 * MIB)
        self.assertEqual(len(image["layers"]), 2)
        self.assertEqual(len(image["history"]), 4)
        self.assertEqual(
            image["layers"][1]["command"], self.config["history"][2]["created_by"]
        )
        self.assertEqual(
            len(self.requests), 3
        )  # Index, manifest, config; no filesystem blobs.

    def test_wrong_platform_is_an_error(self):
        self.config["architecture"] = "arm64"
        with self.assertRaisesRegex(ValueError, "Wrong platform"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")

    def test_arm64_manifest_is_selected_and_verified(self):
        prefix = "/v2/frappe/erpnext"
        arm_manifest = copy.deepcopy(self.manifest)
        arm_manifest["config"]["digest"] = "sha256:config-arm64"
        self.routes[f"{prefix}/manifests/sha256:arm64"] = arm_manifest
        self.routes[f"{prefix}/blobs/sha256:config-arm64"] = {
            **self.config,
            "architecture": "arm64",
        }
        image = sizes.measure_image(self.registry, "erpnext", "v16.51.1", "arm64")
        self.assertEqual(image["compressed_bytes"], 1000 * MIB)
        self.assertIn(f"{prefix}/manifests/sha256:arm64", self.requests)
        self.assertNotIn(f"{prefix}/manifests/sha256:amd64", self.requests)

    def test_mislabeled_arm64_build_reports_the_actual_platform(self):
        index = self.routes["/v2/frappe/erpnext/manifests/v16.51.1"]
        index["manifests"] = [index["manifests"][1]]
        with self.assertRaisesRegex(ValueError, "linux/arm64.*available: linux/amd64"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "arm64")

    def test_inconsistent_history_is_an_error(self):
        self.config["history"].pop(0)
        with self.assertRaisesRegex(ValueError, "history does not match"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")

    def test_cli_reports_failure_and_keeps_measurements(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            previous = report(700 * MIB)
            previous["images"]["base"] = copy.deepcopy(previous["images"]["erpnext"])
            previous["images"]["build"] = copy.deepcopy(previous["images"]["erpnext"])
            baseline = directory / "baseline.json"
            baseline.write_text(json.dumps(previous))
            output = directory / "report.json"
            summary = directory / "summary.md"
            environment = {
                **os.environ,
                **{key.upper(): value for key, value in report()["inputs"].items()},
            }
            environment["GITHUB_STEP_SUMMARY"] = str(summary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(sizes.__file__)),
                    "check",
                    "--repo",
                    "erpnext",
                    "--version",
                    "16",
                    "--arch",
                    "amd64",
                    "--registry",
                    self.registry,
                    "--baseline",
                    str(baseline),
                    "--output",
                    str(output),
                ],
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("size limit exceeded", result.stdout)
            self.assertIn("FAIL", summary.read_text())
            self.assertEqual(
                json.loads(output.read_text())["images"]["erpnext"]["compressed_bytes"],
                1000 * MIB,
            )
            self.assertEqual(len(self.requests), 9)


if __name__ == "__main__":
    unittest.main()
