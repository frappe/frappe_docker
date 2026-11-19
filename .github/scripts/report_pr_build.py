"""Summarize a completed PR image build using GitHub jobs and size artifacts."""

from __future__ import annotations

import json
import os
import re
import subprocess
import zipfile
from datetime import datetime
from functools import cache
from pathlib import Path
from urllib.parse import urlencode

from image_sizes import ARCHITECTURES, artifact_name, download_report, mib, trusted_run

STABLE_WORKFLOW = ".github/workflows/core-build-stable.yml"
RELEASE_LINES = (("15", "v15_test"), ("16", "v16_test"))
IMAGES = ("base", "build", "erpnext")


def api(endpoint, *, paginate=False, method="GET", body=None):
    command = ["gh", "api", "--method", method]
    if paginate:
        command += ["--paginate", "--slurp"]
    payload = None
    if body is not None:
        command += ["--input", "-"]
        payload = json.dumps(body)
    result = subprocess.run(
        [*command, endpoint],
        input=payload,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def matching_pull_request(repository, run):
    head_repo = run.get("head_repository")
    if not head_repo or not run.get("head_branch"):
        return None
    head_ref = run["head_branch"]
    query = urlencode(
        {
            "head": f"{head_repo['owner']['login']}:{head_ref}",
            "base": "main",
            "state": "open",
        }
    )
    # GitHub can omit the PR association in workflow_run, including for fork PRs.
    pulls = api(f"repos/{repository}/pulls?{query}")
    matches = [
        pull["number"]
        for pull in pulls
        if (pull["head"].get("repo") or {}).get("id") == head_repo["id"]
        and pull["head"]["ref"] == head_ref
        and pull["head"]["sha"] == run["head_sha"]
    ]
    return matches[0] if len(matches) == 1 else None


def build_step(job):
    return next((step for step in job.get("steps", []) if step["name"] == "Build"), {})


def build_status(conclusion):
    if conclusion is None:
        return "—"
    return {"success": "✅ Passed", "failure": "❌ Failed"}.get(
        conclusion, conclusion.replace("_", " ")
    )


def build_duration(step):
    if step.get("conclusion") == "skipped" or not (
        step.get("started_at") and step.get("completed_at")
    ):
        return None
    elapsed = datetime.fromisoformat(step["completed_at"]) - datetime.fromisoformat(
        step["started_at"]
    )
    seconds = elapsed.total_seconds()
    return int(seconds) if seconds >= 0 else None


def duration_text(seconds):
    minutes, seconds = divmod(abs(seconds), 60)
    return f"{minutes}m {seconds:02d}s"


def change_text(delta, previous, absolute):
    circle = "🟠 " if delta > 0 else "🟢 " if delta < 0 else ""
    percent = f" ({delta * 100 / previous:+.1f}%)" if previous else ""
    return f"{circle}{absolute}{percent}"


def duration_cell(current, previous):
    if current is None:
        return "—"
    if previous is None:
        return duration_text(current)
    delta = current - previous
    sign = "+" if delta > 0 else "−" if delta < 0 else ""
    change = change_text(delta, previous, f"{sign}{duration_text(delta)}")
    return f"{duration_text(previous)} → {duration_text(current)}<br>{change}"


def size_cell(current, previous):
    if current is None:
        return "—"
    if previous is None:
        return mib(current)
    delta = current - previous
    sign = "+" if delta > 0 else ""
    change = change_text(delta, previous, f"{sign}{mib(delta)}")
    return f"{mib(previous)} → {mib(current)}<br>{change}"


def size_values(values):
    if not isinstance(values, dict):
        return {}
    sizes = {image: values.get(image) for image in IMAGES}
    if any(
        type(value) is not int or not 0 <= value < 2**64 for value in sizes.values()
    ):
        return {}
    return sizes


def image_report(repository, artifact, run_id, version, arch):
    if not artifact or artifact["expired"] or artifact["size_in_bytes"] > 1024 * 1024:
        return {}, None
    try:
        # Only numeric sizes from the untrusted report are rendered.
        report = download_report(repository, artifact["id"])
        if (report["repo"], report["release_line"], report["arch"]) != (
            "erpnext",
            version,
            arch,
        ) or report["source"]["run_id"] != run_id:
            return {}, None
        sizes = size_values(
            {image: report["images"][image]["compressed_bytes"] for image in IMAGES}
        )
        baseline = report.get("baseline")
        return sizes, baseline if isinstance(baseline, dict) else None
    except (KeyError, TypeError, ValueError, zipfile.BadZipFile):
        return {}, None


def report_rows(repository, run):
    endpoint = f"repos/{repository}/actions/runs/{run['id']}"
    jobs = {}
    for page in api(f"{endpoint}/jobs?filter=all&per_page=100", paginate=True):
        for job in page["jobs"]:
            # A failed-job rerun retains successful jobs from earlier attempts.
            previous = jobs.get(job["name"], {})
            if (
                previous.get("run_attempt", 0)
                < job["run_attempt"]
                <= run["run_attempt"]
            ):
                jobs[job["name"]] = job
    artifacts = {
        artifact["name"]: artifact
        for page in api(f"{endpoint}/artifacts?per_page=100", paginate=True)
        for artifact in page["artifacts"]
    }

    @cache
    def baseline_run(run_id):
        previous = api(f"repos/{repository}/actions/runs/{run_id}")
        if trusted_run(previous, repository, STABLE_WORKFLOW, run["id"]):
            return previous
        return None

    @cache
    def baseline_jobs(run_id, attempt):
        endpoint = f"repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100"
        return {
            job["name"]: job
            for page in api(endpoint, paginate=True)
            for job in page["jobs"]
        }

    def baseline_measurements(baseline, job_name):
        run_id = (baseline or {}).get("run_id")
        if type(run_id) is not int or not 0 < run_id < run["id"]:
            return "—", None, {}
        previous = baseline_run(run_id)
        if previous is None:
            return "—", None, {}

        attempt = baseline.get("run_attempt")
        if attempt is None and previous["run_attempt"] == 1:
            attempt = 1  # Reports from before attempt tracking.
        duration = None
        if type(attempt) is int and 0 < attempt <= previous["run_attempt"]:
            job = baseline_jobs(run_id, attempt).get(job_name, {})
            duration = build_duration(build_step(job))
        link = f"[Run {run_id}](https://github.com/{repository}/actions/runs/{run_id})"
        return link, duration, size_values(baseline.get("sizes"))

    for version, job_prefix in RELEASE_LINES:
        for arch in ARCHITECTURES:
            job_name = f"{job_prefix} / Build ({arch})"
            job = jobs.get(job_name, {})
            step = build_step(job)
            sizes, baseline = {}, None
            if step.get("conclusion") == "success":
                name = artifact_name(
                    "erpnext", version, arch, attempt=job["run_attempt"]
                )
                sizes, baseline = image_report(
                    repository, artifacts.get(name), run["id"], version, arch
                )
            baseline_link, previous_time, previous_sizes = baseline_measurements(
                baseline, job_name
            )
            yield [
                version,
                arch,
                build_status(job.get("conclusion")),
                baseline_link,
                duration_cell(build_duration(step), previous_time),
                *(
                    size_cell(sizes.get(image), previous_sizes.get(image))
                    for image in IMAGES
                ),
            ]


def report_comment(repository, run, rows):
    run_url = f"https://github.com/{repository}/actions/runs/{run['id']}/attempts/{run['run_attempt']}"
    status = build_status(run["conclusion"])
    lines = [
        f"<!-- image-build-report:Stable:{run['id']}:{run['run_attempt']} -->",
        "### Stable image build report",
        "",
        f"[Workflow run]({run_url}) for `{run['head_sha'][:7]}` · {status}",
        "",
        "| Release line | Architecture | Status | Baseline | Docker Bake time | Base | Build | ERPNext |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines += [
        "",
        "Cells with two values show baseline → current, with the change below. "
        "Image sizes are compressed. A dash means no measurement was available.",
    ]
    return "\n".join(lines)


def update_comment(repository, number, run, body):
    endpoint = f"repos/{repository}/issues/{number}/comments"
    marker = re.compile(r"^<!-- image-build-report:Stable:(\d+):(\d+) -->")
    for page in api(f"{endpoint}?per_page=100", paginate=True):
        for comment in page:
            if comment["user"]["login"] != "github-actions[bot]":
                continue
            match = marker.match(comment["body"])
            if match:
                if tuple(map(int, match.groups())) <= (run["id"], run["run_attempt"]):
                    api(
                        f"repos/{repository}/issues/comments/{comment['id']}",
                        method="PATCH",
                        body={"body": body},
                    )
                return
    api(endpoint, method="POST", body={"body": body})


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(
        Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")
    )
    run = event["workflow_run"]
    if run["path"] != STABLE_WORKFLOW or run["event"] != "pull_request":
        return
    rows = list(report_rows(repository, run))
    number = matching_pull_request(repository, run)
    if number is not None:
        body = report_comment(repository, run, rows)
        update_comment(repository, number, run, body)


if __name__ == "__main__":
    main()
