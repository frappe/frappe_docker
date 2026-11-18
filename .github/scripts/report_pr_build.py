"""Summarize a completed PR image build using GitHub jobs and size artifacts."""

from __future__ import annotations

import json
import os
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from image_sizes import ARCHITECTURES, artifact_name, download_report, mib

WORKFLOWS = {
    ".github/workflows/core-build-stable.yml": (
        "Stable",
        (("15", "v15_test"), ("16", "v16_test")),
    ),
    ".github/workflows/core-build-develop.yml": ("Develop", (("develop", "test"),)),
}
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


def build_duration(step):
    if not (step.get("started_at") and step.get("completed_at")):
        return "—"
    elapsed = datetime.fromisoformat(step["completed_at"]) - datetime.fromisoformat(
        step["started_at"]
    )
    if elapsed.total_seconds() < 0:
        return "—"
    minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
    return f"{minutes}m {seconds:02d}s"


def image_sizes(repository, artifact, run_id, version, arch, step):
    if (
        not artifact
        or artifact["expired"]
        or artifact["size_in_bytes"] > 1024 * 1024
        or step.get("conclusion") != "success"
        or not step.get("completed_at")
        or datetime.fromisoformat(artifact["created_at"])
        < datetime.fromisoformat(step["completed_at"])
    ):
        return {}
    try:
        # Only numeric sizes from the untrusted report are rendered.
        report = download_report(repository, artifact["id"])
        if (report["repo"], report["release_line"], report["arch"]) != (
            "erpnext",
            version,
            arch,
        ) or report["source"]["run_id"] != run_id:
            return {}
        sizes = {}
        for image in IMAGES:
            value = report["images"][image]["compressed_bytes"]
            if type(value) is not int or not 0 <= value < 2**64:
                return {}
            sizes[image] = mib(value)
        return sizes
    except (
        KeyError,
        TypeError,
        ValueError,
        OSError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
    ):
        return {}


def report_rows(repository, run, release_lines):
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
    for version, job_prefix in release_lines:
        for arch in ARCHITECTURES:
            job = jobs.get(f"{job_prefix} / Build ({arch})")
            step = build_step(job) if job else {}
            name = artifact_name("erpnext", version, arch, pull_request=True)
            sizes = image_sizes(
                repository, artifacts.get(name), run["id"], version, arch, step
            )
            yield [
                version,
                arch,
                build_duration(step),
                *(sizes.get(image, "—") for image in IMAGES),
            ]


def report_comment(repository, run, label, rows):
    run_url = f"https://github.com/{repository}/actions/runs/{run['id']}/attempts/{run['run_attempt']}"
    lines = [
        f"<!-- image-build-report:{label}:{run['id']}:{run['run_attempt']} -->",
        f"### {label} image build report",
        "",
        f"[Workflow run]({run_url}) · {run['conclusion'].replace('_', ' ')}",
        "",
        "| Release line | Architecture | Docker Bake time | Base | Build | ERPNext |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines += [
        "",
        "Image sizes are compressed. A dash means no measurement was available.",
    ]
    return "\n".join(lines)


def update_comment(repository, number, run, label, body):
    endpoint = f"repos/{repository}/issues/{number}/comments"
    marker = re.compile(rf"^<!-- image-build-report:{label}:(\d+):(\d+) -->")
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
    workflow = WORKFLOWS.get(run["path"])
    if not workflow or run["event"] != "pull_request":
        return
    label, release_lines = workflow
    rows = list(report_rows(repository, run, release_lines))
    number = matching_pull_request(repository, run)
    if number is not None:
        body = report_comment(repository, run, label, rows)
        update_comment(repository, number, run, label, body)


if __name__ == "__main__":
    main()
