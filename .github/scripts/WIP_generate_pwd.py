import shutil
import subprocess

from get_latest_tags import get_latest_tag, update_env


def prepare_env():
    version = "13"
    frappe_tag = get_latest_tag("frappe", version)
    erpnext_tag = get_latest_tag("erpnext", version)
    shutil.copyfile("example.env", ".env")
    update_env(".env", frappe_tag, erpnext_tag)


def generate_compose_file():
    output = subprocess.check_output(
        (
            "docker-compose",
            "-f",
            "compose.yaml",
            "-f",
            "overrides/compose.erpnext.yaml",
            "--env-file",
            ".env",
            "config",
        ),
        encoding="UTF-8",
    )
    text = f'version: "3.9"\n\n{output}'
    with open("pwd.yml", "a+") as f:
        f.seek(0)
        f.truncate()
        f.write(text)


def main() -> int:
    prepare_env()
    generate_compose_file()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
