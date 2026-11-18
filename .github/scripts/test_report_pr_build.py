import unittest
from unittest.mock import patch

import report_pr_build as reporter

REPOSITORY = "frappe/frappe_docker"
RUN = {"id": 19, "run_attempt": 2, "conclusion": "failure"}


def job(arch, attempt):
    return {
        "name": f"v15_test / Build ({arch})",
        "run_attempt": attempt,
        "steps": [
            {
                "name": "Build",
                "conclusion": "success",
                "started_at": f"2026-11-18T12:00:0{attempt}Z",
                "completed_at": "2026-11-18T12:02:01Z",
            }
        ],
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

    def test_report_keeps_build_times_and_available_sizes_on_failure(self):
        artifact = {
            "name": "image-sizes-pr-erpnext-15-arm64",
            "id": 72,
            "expired": False,
            "size_in_bytes": 2000,
            "created_at": "2026-11-18T12:02:05Z",
        }
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
                    [{"jobs": [job("amd64", 3), job("amd64", 2), job("arm64", 1)]}],
                    [{"artifacts": [artifact]}],
                ],
            ),
            patch.object(reporter, "download_report", return_value=report),
        ):
            rows = list(reporter.report_rows(REPOSITORY, RUN, (("15", "v15_test"),)))
        self.assertEqual(
            rows,
            [
                ["15", "amd64", "1m 59s", "—", "—", "—"],
                ["15", "arm64", "2m 00s", "1.0 MiB", "1.0 MiB", "1.0 MiB"],
            ],
        )
        body = reporter.report_comment(REPOSITORY, RUN, "Stable", rows)
        self.assertIn("attempts/2) · failure", body)
        self.assertNotIn("@someone", body)

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
            with self.subTest(expected=expected), patch.object(
                reporter, "api", return_value=[comments]
            ) as api:
                reporter.update_comment(REPOSITORY, 42, RUN, "Stable", "Report")
                self.assertEqual(api.call_args.kwargs.get("method", "GET"), expected)


if __name__ == "__main__":
    unittest.main()
