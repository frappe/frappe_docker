"""Validate every supported Docker Compose override combination."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "tests" / "compose-configs.json"
OVERRIDES_PATH = ROOT / "overrides"


def fail(message: str) -> None:
    print(f"Compose validation configuration error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_matrix() -> Dict[str, object]:
    try:
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {MATRIX_PATH.relative_to(ROOT)}: {exc}")

    if not isinstance(matrix, dict):
        fail("the matrix root must be a JSON object")

    environment = matrix.get("environment")
    configurations = matrix.get("configurations")
    if not isinstance(environment, dict):
        fail("'environment' must be a JSON object")
    if not isinstance(configurations, list) or not configurations:
        fail("'configurations' must be a non-empty JSON array")

    return matrix


def validate_matrix(configurations: List[object]) -> None:
    names = set()
    covered_overrides = set()

    for index, configuration in enumerate(configurations, start=1):
        if not isinstance(configuration, dict):
            fail(f"configuration #{index} must be a JSON object")

        name = configuration.get("name")
        files = configuration.get("files")
        if not isinstance(name, str) or not name:
            fail(f"configuration #{index} needs a non-empty 'name'")
        if name in names:
            fail(f"configuration name '{name}' is duplicated")
        names.add(name)

        if not isinstance(files, list) or not files:
            fail(f"configuration '{name}' needs a non-empty 'files' array")
        if len(files) != len(set(files)):
            fail(f"configuration '{name}' references a file more than once")

        for filename in files:
            if not isinstance(filename, str):
                fail(f"configuration '{name}' contains a non-string file name")

            path = ROOT / filename
            if not path.is_file():
                fail(f"configuration '{name}' references missing file '{filename}'")
            if path.parent == OVERRIDES_PATH:
                covered_overrides.add(path.relative_to(ROOT).as_posix())

    existing_overrides = {
        path.relative_to(ROOT).as_posix()
        for path in OVERRIDES_PATH.glob("compose.*.yaml")
    }
    uncovered_overrides = sorted(existing_overrides - covered_overrides)
    if uncovered_overrides:
        formatted = "\n  - ".join(uncovered_overrides)
        fail(
            "every override must be covered by at least one configuration in "
            f"{MATRIX_PATH.relative_to(ROOT)}. Add:\n  - {formatted}"
        )


def validate_compose(
    configurations: List[object], environment: Dict[str, object]
) -> int:
    compose_environment = os.environ.copy()
    for key, value in environment.items():
        if not isinstance(key, str) or not isinstance(value, str):
            fail("all 'environment' keys and values must be strings")
        compose_environment[key] = value

    failures = 0
    total = len(configurations)
    for index, configuration in enumerate(configurations, start=1):
        name = configuration["name"]
        files = configuration["files"]
        command = [
            "docker",
            "compose",
            "--project-directory",
            str(ROOT),
            "--env-file",
            str(ROOT / "example.env"),
        ]
        for filename in files:
            command.extend(("-f", str(ROOT / filename)))
        command.extend(("config", "--quiet"))

        print(f"[{index}/{total}] Validating {name}")
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=compose_environment,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            fail("Docker Compose is required, but the 'docker' command was not found")

        if result.returncode:
            failures += 1
            print(f"FAILED: {name}", file=sys.stderr)
            if result.stdout:
                print(result.stdout.rstrip(), file=sys.stderr)
            if result.stderr:
                print(result.stderr.rstrip(), file=sys.stderr)

    if failures:
        print(
            f"{failures} of {total} Compose configurations failed validation.",
            file=sys.stderr,
        )
        return 1

    print(f"Validated {total} Compose configurations.")
    return 0


def main() -> int:
    matrix = load_matrix()
    configurations = matrix["configurations"]
    environment = matrix["environment"]
    validate_matrix(configurations)
    return validate_compose(configurations, environment)


if __name__ == "__main__":
    raise SystemExit(main())
