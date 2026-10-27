"""Check image growth using registry metadata and successful main-run artifacts."""

from __future__ import annotations

import argparse
import html
import io
import json
import math
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from get_latest_tags import get_latest_tag

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURES = ("amd64", "arm64")
TRUSTED_EVENTS = {"push", "repository_dispatch", "schedule", "workflow_dispatch"}
MANIFEST_TYPES = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


def artifact_name(repo: str, version: str, arch: str) -> str:
    return f"image-sizes-{repo}-{version}-{arch}"


def github_api(endpoint: str, *, binary: bool = False):
    # gh handles authentication and artifact-download redirects without passing
    # the API token to the storage host. Do not extract artifact-provided paths.
    result = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, check=True
    ).stdout
    return result if binary else json.loads(result)


def download_report(repository: str, artifact_id: int, api=github_api) -> dict:
    archive = api(
        f"repos/{repository}/actions/artifacts/{artifact_id}/zip", binary=True
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        entry = bundle.getinfo("report.json")
        if entry.file_size > 2 * 1024 * 1024:
            raise ValueError("Image size report exceeds 2 MiB")
        report = json.loads(bundle.read(entry))
    if report.get("schema_version") != 1:
        raise ValueError("Unsupported image size report schema")
    return report


def trusted_run(run: dict, repository: str, workflow: str, current_run: int) -> bool:
    return (
        run["id"] < current_run
        and run["conclusion"] == "success"
        and run["head_branch"] == "main"
        and run["head_repository"]["full_name"] == repository
        and run["event"] in TRUSTED_EVENTS
        and run["path"] == workflow
    )


def find_baseline(
    repository: str,
    workflow: str,
    repo: str,
    version: str,
    current_run: int,
    api=github_api,
) -> tuple[dict | None, dict[str, int]]:
    """Choose a completed main run, never a PR or a partially successful run."""
    query = urlencode({"name": artifact_name(repo, version, "amd64"), "per_page": 100})
    candidates = []
    for page in range(1, 6):
        artifacts = api(f"repos/{repository}/actions/artifacts?{query}&page={page}")[
            "artifacts"
        ]
        candidates.extend(artifacts)
        if len(artifacts) < 100:
            break
    # Artifact creation order follows completion, not the order of main pushes.
    # A slow older run must not replace a newer successful baseline.
    candidates.sort(key=lambda item: item["workflow_run"]["id"], reverse=True)
    for artifact in candidates:
        origin = artifact["workflow_run"]
        if (
            artifact["expired"]
            or origin["head_branch"] != "main"
            or origin["head_repository_id"] != origin["repository_id"]
            or origin["id"] >= current_run
        ):
            continue
        run = api(f"repos/{repository}/actions/runs/{origin['id']}")
        if not trusted_run(run, repository, workflow, current_run):
            continue
        siblings = api(
            f"repos/{repository}/actions/runs/{run['id']}/artifacts?per_page=100"
        )["artifacts"]
        ids = {
            arch: item["id"]
            for arch in ARCHITECTURES
            for item in siblings
            if item["name"] == artifact_name(repo, version, arch)
            and not item["expired"]
        }
        if set(ids) != set(ARCHITECTURES):
            continue
        report = download_report(repository, ids["amd64"], api)
        validate_identity(report, repo, version, "amd64")
        if report["source"]["run_id"] != run["id"]:
            raise ValueError("Baseline report does not match its workflow run")
        return report, ids
    return None, {}


def validate_identity(report: dict, repo: str, version: str, arch: str) -> None:
    if (report["repo"], report["release_line"], report["arch"]) != (
        repo,
        version,
        arch,
    ):
        raise ValueError("Baseline image type, release line or architecture differs")
    for key in ("frappe_version", "erpnext_version"):
        value = report["inputs"][key]
        if value and not re.fullmatch(r"develop|v[0-9][A-Za-z0-9._-]*", value):
            raise ValueError(f"Invalid baseline {key}")


def prepare(args) -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    workflow = os.environ["GITHUB_WORKFLOW_REF"].split("@", 1)[0]
    workflow = workflow.removeprefix(f"{repository}/")
    baseline, ids = find_baseline(
        repository, workflow, args.repo, args.version, int(os.environ["GITHUB_RUN_ID"])
    )
    if os.environ["GITHUB_EVENT_NAME"] == "pull_request" and baseline:
        frappe_version = baseline["inputs"]["frappe_version"]
        erpnext_version = baseline["inputs"]["erpnext_version"]
        print(
            f"Using application versions from main run {baseline['source']['run_id']}"
        )
    else:
        frappe_version = get_latest_tag("frappe", args.version)
        erpnext_version = (
            get_latest_tag("erpnext", args.version) if args.repo == "erpnext" else ""
        )
    outputs = {
        "frappe_version": frappe_version,
        "erpnext_version": erpnext_version,
        "baseline_artifacts": json.dumps(ids),
    }
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key, value in outputs.items():
            output.write(f"{key}={value}\n")
    if not baseline:
        print("No retained successful main baseline; this run will report sizes only.")


def registry_json(url: str) -> dict:
    request = Request(url, headers={"Accept": MANIFEST_TYPES})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def measure_image(registry: str, name: str, tag: str, arch: str) -> dict:
    url = f"http://{registry}/v2/frappe/{name}"
    manifest = registry_json(f"{url}/manifests/{quote(tag, safe='')}")
    if "manifests" in manifest:
        matches = [
            item
            for item in manifest["manifests"]
            if item.get("platform", {}).get("os") == "linux"
            and item.get("platform", {}).get("architecture") == arch
        ]
        if len(matches) != 1:
            available = ", ".join(
                f"{item.get('platform', {}).get('os', '?')}/"
                f"{item.get('platform', {}).get('architecture', '?')}"
                for item in manifest["manifests"]
            )
            raise ValueError(
                f"Expected one linux/{arch} manifest for {name}:{tag}; "
                f"available: {available or 'none'}"
            )
        manifest = registry_json(f"{url}/manifests/{matches[0]['digest']}")
    config = registry_json(f"{url}/blobs/{manifest['config']['digest']}")
    if (config["os"], config["architecture"]) != ("linux", arch):
        raise ValueError(f"Wrong platform for {name}:{tag}")
    history = [item for item in config["history"] if not item.get("empty_layer", False)]
    if len(history) != len(manifest["layers"]):
        raise ValueError(f"Layer history does not match manifest for {name}:{tag}")
    layers = [
        {
            "digest": layer["digest"],
            "bytes": layer["size"],
            "command": item.get("created_by", ""),
        }
        for layer, item in zip(manifest["layers"], history)
    ]
    return {
        "compressed_bytes": sum(item["bytes"] for item in layers),
        "layers": layers,
        "history": [item.get("created_by", "") for item in config["history"]],
    }


def growth_exceeds(current: int, previous: int, policy: dict) -> bool:
    delta = current - previous
    return (
        delta > policy["max_growth_bytes"]
        and delta * 100 > previous * policy["max_growth_percent"]
    )


def mib(size: int) -> str:
    return f"{size / 1024 / 1024:,.1f} MiB"


def compare(report: dict, baseline: dict | None, policy: dict) -> tuple[str, list[str]]:
    failures = []
    lines = [
        f"## Image sizes: {report['release_line']} / {report['arch']}",
        "",
        "Sizes are the sum of compressed filesystem layers from registry manifests.",
        "Each image is measured separately, including its shared base layers.",
        "",
    ]
    if baseline:
        lines += [f"Baseline: successful main run {baseline['source']['run_id']}.", ""]
        if report["inputs"] != baseline["inputs"]:
            lines += [
                "Build inputs changed; the delta also includes application or dependency growth.",
                f"Previous inputs: <code>{html.escape(json.dumps(baseline['inputs']))}</code>",
                f"Current inputs: <code>{html.escape(json.dumps(report['inputs']))}</code>",
                "",
            ]
    else:
        lines += [
            "**No retained successful main baseline.** Sizes are reported; the next successful",
            "main build supplies a baseline automatically.",
            "",
        ]
    lines += [
        f"Fail when growth exceeds both {policy['max_growth_percent']}% and "
        f"{mib(policy['max_growth_bytes'])}.",
        "",
        "| Image | Baseline | Current | Change | Layers | Result |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if baseline and set(report["images"]) != set(baseline["images"]):
        raise ValueError("Baseline contains different image targets")
    for name, image in report["images"].items():
        previous = baseline["images"][name]["compressed_bytes"] if baseline else None
        current = image["compressed_bytes"]
        exceeded = previous is not None and growth_exceeds(current, previous, policy)
        if exceeded:
            failures.append(
                f"{name} grew by {mib(current - previous)}; size limit exceeded"
            )
        delta = f"{mib(current - previous)}" if previous is not None else "—"
        percent = (current - previous) * 100 / previous if previous else 0
        if previous:
            delta += f" ({percent:+.1f}%)"
        result = "FAIL" if exceeded else ("PASS" if baseline else "First baseline")
        lines.append(
            f"| {name} | {mib(previous) if previous is not None else '—'} | "
            f"{mib(current)} | {delta} | {len(image['layers'])} | {result} |"
        )
    if failures:
        lines += ["", "### Failures", ""]
        lines += [f"- {html.escape(failure)}" for failure in failures]
    for name, image in report["images"].items():
        lines += ["", f"<details><summary>{name}: largest layers</summary>", ""]
        lines += ["| Compressed size | Instruction |", "| ---: | --- |"]
        for layer in sorted(
            image["layers"], key=lambda item: item["bytes"], reverse=True
        )[:10]:
            command = html.escape(layer["command"][:1000]).replace("|", "&#124;")
            command = command.replace("\n", " ")
            lines.append(f"| {mib(layer['bytes'])} | <code>{command}</code> |")
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n", failures


def check(args) -> list[str]:
    baseline = None
    if args.baseline.is_file():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        validate_identity(baseline, args.repo, args.version, args.arch)
    inputs = {
        key.lower(): os.environ.get(key, "")
        for key in (
            "FRAPPE_VERSION",
            "ERPNEXT_VERSION",
            "PYTHON_VERSION",
            "NODE_VERSION",
            "DEBIAN_BASE",
        )
    }
    images = {
        "base": measure_image(
            args.registry, "base", inputs["frappe_version"], args.arch
        )
    }
    if args.repo == "erpnext":
        for name in ("build", "erpnext"):
            images[name] = measure_image(
                args.registry, name, inputs["erpnext_version"], args.arch
            )
    report = {
        "schema_version": 1,
        "repo": args.repo,
        "release_line": args.version,
        "arch": args.arch,
        "inputs": inputs,
        "source": {
            "sha": os.environ.get("GITHUB_SHA", ""),
            "run_id": int(os.environ.get("GITHUB_RUN_ID", "0")),
        },
        "images": images,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    if set(policy) != {"max_growth_bytes", "max_growth_percent"} or any(
        type(value) not in (int, float) or not math.isfinite(value) or value < 0
        for value in policy.values()
    ):
        raise ValueError("Image growth limits must be non-negative numbers")
    summary, failures = compare(report, baseline, policy)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as output:
            output.write(summary)
    print(summary)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    download_parser = subparsers.add_parser("download")
    check_parser = subparsers.add_parser("check")
    for child in (prepare_parser, check_parser):
        child.add_argument("--repo", choices=("frappe", "erpnext"), required=True)
        child.add_argument("--version", choices=("15", "16", "develop"), required=True)
    download_parser.add_argument("--artifact-id", required=True)
    download_parser.add_argument("--output", type=Path, required=True)
    check_parser.add_argument("--arch", choices=ARCHITECTURES, required=True)
    check_parser.add_argument("--registry", default="localhost:5000")
    check_parser.add_argument(
        "--baseline", type=Path, default=Path("image-size-baseline.json")
    )
    check_parser.add_argument("--output", type=Path, default=Path("report.json"))
    check_parser.add_argument(
        "--policy", type=Path, default=ROOT / ".github/image-size-policy.json"
    )
    args = parser.parse_args()
    try:
        failures = []
        if args.command == "prepare":
            prepare(args)
        elif args.command == "download":
            if args.artifact_id:
                report = download_report(
                    os.environ["GITHUB_REPOSITORY"], int(args.artifact_id)
                )
                args.output.write_text(json.dumps(report), encoding="utf-8")
        else:
            failures = check(args)
        for failure in failures:
            escaped = (
                failure.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            )
            print(f"::error::{escaped}")
        return int(bool(failures))
    except (
        OSError,
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Image size check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
