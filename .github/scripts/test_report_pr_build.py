import json
import subprocess
import unittest
from unittest.mock import patch

import report_pr_build as reporter

REPOSITORY = "frappe/frappe_docker"
RUN = {
    "id": 19,
    "run_attempt": 2,
    "conclusion": "failure",
    "head_sha": "f1234567890abcdef",
    "path": ".github/workflows/core-build-stable.yml",
}


def job(arch, attempt, conclusion="success"):
    return {
        "name": f"v15_test / Build ({arch})",
        "run_attempt": attempt,
        "conclusion": conclusion,
        "steps": [
            {
                "name": "Build",
                "conclusion": "success",
                "started_at": f"2026-11-18T12:00:0{attempt}Z",
                "completed_at": "2026-11-18T12:02:01Z",
            }
        ],
    }


def artifact(arch, attempt, artifact_id):
    return {
        "name": f"image-sizes-pr-erpnext-15-{arch}-attempt-{attempt}",
        "id": artifact_id,
        "expired": False,
        "size_in_bytes": 2000,
    }


class BuildReportTests(unittest.TestCase):
    def test_fork_pull_request_requires_matching_head(self):
        run = {
            **RUN,
            "head_repository": {"id": 34, "owner": {"login": "fork-owner"}},
            "head_branch": "topic/build",
            "head_sha": "current",
            "pull_requests": [],
        }
        head = {"repo": {"id": 34}, "ref": "topic/build", "sha": "current"}
        with patch.object(
            reporter,
            "api",
            return_value=[
                {"number": 41, "head": {**head, "sha": "earlier"}},
                {"number": 42, "head": head},
            ],
        ) as api:
            self.assertEqual(reporter.matching_pull_request(REPOSITORY, run), 42)
            self.assertIn("head=fork-owner%3Atopic%2Fbuild", api.call_args.args[0])
            self.assertIsNone(
                reporter.matching_pull_request(REPOSITORY, {**run, "head_sha": "stale"})
            )

    def test_report_pairs_sizes_with_the_selected_job_attempt(self):
        report = {
            "repo": "erpnext",
            "release_line": "15",
            "arch": "arm64",
            "source": {"run_id": 19},
            "images": {
                name: {"compressed_bytes": 1024 * 1024, "history": ["@someone"]}
                for name in ("base", "build", "erpnext")
            },
        }
        with (
            patch.object(
                reporter,
                "api",
                side_effect=[
                    [
                        {
                            "jobs": [
                                job("amd64", 3),
                                job("amd64", 2, "failure"),
                                job("arm64", 1),
                            ]
                        }
                    ],
                    [
                        {
                            "artifacts": [
                                artifact("arm64", 1, 72),
                                artifact("arm64", 2, 73),
                                artifact("amd64", 1, 74),
                            ]
                        }
                    ],
                ],
            ),
            patch.object(reporter, "download_report", return_value=report) as download,
        ):
            rows = list(reporter.report_rows(REPOSITORY, RUN))
        download.assert_called_once_with(REPOSITORY, 72)
        self.assertEqual(
            rows,
            [
                ["15", "amd64", "❌ Failed", "—", "1m 59s", "—", "—", "—"],
                [
                    "15",
                    "arm64",
                    "✅ Passed",
                    "—",
                    "2m 00s",
                    "1.0 MiB",
                    "1.0 MiB",
                    "1.0 MiB",
                ],
                ["16", "amd64", "—", "—", "—", "—", "—", "—"],
                ["16", "arm64", "—", "—", "—", "—", "—", "—"],
            ],
        )
        body = reporter.report_comment(REPOSITORY, RUN, rows)
        self.assertIn("attempts/2) for `f123456` · ❌ Failed", body)
        self.assertNotIn("@someone", body)

    def test_comment_status_distinguishes_passed_and_cancelled_runs(self):
        for conclusion, status in (
            ("success", "✅ Passed"),
            ("cancelled", "cancelled"),
        ):
            with self.subTest(conclusion=conclusion):
                body = reporter.report_comment(
                    REPOSITORY, {**RUN, "conclusion": conclusion}, []
                )
                self.assertIn(f" · {status}", body)

    def test_duration_change_handles_unchanged_and_zero_time_baselines(self):
        self.assertEqual(
            reporter.duration_cell(10, 10), "0m 10s → 0m 10s<br>0m 00s (+0.0%)"
        )
        self.assertEqual(reporter.duration_cell(10, 0), "0m 00s → 0m 10s<br>🟠 +0m 10s")

    def test_report_compares_the_recorded_baseline_attempt(self):
        previous_run = {
            **RUN,
            "id": 12,
            "conclusion": "success",
            "head_branch": "main",
            "head_repository": {"full_name": REPOSITORY},
            "event": "push",
        }
        mib = 1024 * 1024
        report = {
            "repo": "erpnext",
            "release_line": "15",
            "arch": "amd64",
            "source": {"run_id": RUN["id"]},
            "images": {
                image: {"compressed_bytes": 110 * mib} for image in reporter.IMAGES
            },
            "baseline": {
                "run_id": 12,
                "run_attempt": 1,
                "sizes": {image: 100 * mib for image in reporter.IMAGES},
            },
        }
        for attempt, previous_latest, expected_time in (
            (1, 2, "2m 00s → 1m 59s<br>🟢 −0m 01s (-0.8%)"),
            (None, 1, "2m 00s → 1m 59s<br>🟢 −0m 01s (-0.8%)"),
            (None, 2, "1m 59s"),
        ):
            with self.subTest(attempt=attempt, previous_latest=previous_latest):
                report["baseline"]["run_attempt"] = attempt
                responses = [
                    [{"jobs": [job("amd64", 2)]}],
                    [{"artifacts": [artifact("amd64", 2, 73)]}],
                    {**previous_run, "run_attempt": previous_latest},
                    [{"jobs": [job("amd64", 1)]}],
                ]
                with (
                    patch.object(reporter, "api", side_effect=responses) as api,
                    patch.object(reporter, "download_report", return_value=report),
                ):
                    row = next(reporter.report_rows(REPOSITORY, RUN))
                self.assertIn("/actions/runs/12", row[3])
                self.assertEqual(row[4], expected_time)
                self.assertEqual(
                    row[5:], ["100.0 MiB → 110.0 MiB<br>🟠 +10.0 MiB (+10.0%)"] * 3
                )
                if attempt or previous_latest == 1:
                    self.assertIn("/runs/12/attempts/1/jobs", api.call_args.args[0])
                else:
                    self.assertEqual(api.call_count, 3)

    def test_failed_download_prevents_comment_update(self):
        event = {
            "workflow_run": {
                **RUN,
                "path": ".github/workflows/core-build-stable.yml",
                "event": "pull_request",
            }
        }
        with (
            patch.dict(
                "os.environ",
                {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_PATH": "event.json"},
            ),
            patch.object(reporter.Path, "read_text", return_value=json.dumps(event)),
            patch.object(
                reporter,
                "api",
                side_effect=[
                    [{"jobs": [job("amd64", 2)]}],
                    [{"artifacts": [artifact("amd64", 2, 73)]}],
                ],
            ),
            patch.object(
                reporter,
                "download_report",
                side_effect=subprocess.CalledProcessError(1, ["gh", "api"]),
            ),
            patch.object(reporter, "update_comment") as update,
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                reporter.main()
        update.assert_not_called()

    def test_develop_run_does_not_report(self):
        event = {
            "workflow_run": {
                **RUN,
                "path": ".github/workflows/core-build-develop.yml",
                "event": "pull_request",
            }
        }
        with (
            patch.dict(
                "os.environ",
                {"GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_PATH": "event.json"},
            ),
            patch.object(reporter.Path, "read_text", return_value=json.dumps(event)),
            patch.object(reporter, "api") as api,
        ):
            reporter.main()
        api.assert_not_called()

    def test_comment_is_created_or_updated_without_replacing_a_newer_report(self):
        for comments, expected in (
            ([], "POST"),
            (
                [
                    {
                        "user": {"login": "someone"},
                        "body": "<!-- image-build-report:Stable:19:1 -->",
                    }
                ],
                "POST",
            ),
            (
                [
                    {
                        "id": 7,
                        "user": {"login": "github-actions[bot]"},
                        "body": "<!-- image-build-report:Stable:19:1 -->",
                    }
                ],
                "PATCH",
            ),
            (
                [
                    {
                        "id": 7,
                        "user": {"login": "github-actions[bot]"},
                        "body": "<!-- image-build-report:Stable:20:1 -->",
                    }
                ],
                "GET",
            ),
        ):
            with (
                self.subTest(expected=expected),
                patch.object(reporter, "api", return_value=[comments]) as api,
            ):
                reporter.update_comment(REPOSITORY, 42, RUN, "Report")
                self.assertEqual(api.call_args.kwargs.get("method", "GET"), expected)


if __name__ == "__main__":
    unittest.main()
