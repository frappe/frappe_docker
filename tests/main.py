import os
import shutil
import ssl
import subprocess
from enum import Enum
from functools import wraps
from time import sleep
from typing import Any, Callable, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CI = os.getenv("CI")
SITE_NAME = "tests"
BACKEND_SERVICES = (
    "backend",
    "queue-short",
    "queue-default",
    "queue-long",
    "scheduler",
)


def patch_print():
    # Patch `print()` builtin to have nice logs when running GitHub Actions
    if not CI:
        return
    global print
    _old_print = print

    def print(
        *values: Any,
        sep: Optional[str] = None,
        end: Optional[str] = None,
        file: Any = None,
        flush: bool = False,
    ):
        return _old_print(*values, sep=sep, end=end, file=file, flush=True)


class Color(Enum):
    GREY = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37


def colored(text: str, color: Color):
    return f"\033[{color.value}m{text}\033[0m"


def log(text: str):
    def decorator(f: Callable[..., Any]):
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any):
            if CI:
                print(f"::group::{text}")
            else:
                print(colored(text, Color.YELLOW))
            ret = f(*args, **kwargs)
            if CI:
                print("::endgroup::")
            return ret

        return wrapper

    return decorator


def run(*cmd: str):
    print(colored(f"> {' '.join(cmd)}", Color.GREEN))
    return subprocess.check_call(cmd)


def docker_compose(*cmd: str):
    args = [
        "docker",
        "compose",
        "-p",
        "test",
        "--env-file",
        "tests/.env",
        "-f",
        "compose.yml",
    ]
    if CI:
        args.extend(("-f", "tests/compose.ci.yml"))
    return run(*args, *cmd)


@log("Setup .env")
def setup_env():
    shutil.copy("example.env", "tests/.env")
    if CI:
        with open("tests/.env", "a") as f:
            f.write(
                f"""
FRAPPE_VERSION={os.getenv("FRAPPE_VERSION")}
ERPNEXT_VERSION={os.getenv("ERPNEXT_VERSION")}
"""
            )
        with open("tests/.env") as f:
            print(f.read())


@log("Print compose configuration")
def print_compose_configuration():
    docker_compose("config")


@log("Create containers")
def create_containers():
    docker_compose("up", "-d")


@log("Check if backend services have connections")
def ping_links_in_backends():
    for service in BACKEND_SERVICES:
        for _ in range(10):
            try:
                docker_compose("exec", service, "healthcheck.sh")
                break
            except subprocess.CalledProcessError:
                sleep(1)
        else:
            raise Exception(f"Connections healthcheck failed for service {service}")


@log("Create test site")
def create_site():
    docker_compose(
        "exec",
        "backend",
        "bench",
        "new-site",
        SITE_NAME,
        "--mariadb-root-password",
        "123",
        "--admin-password",
        "admin",
    )
    docker_compose("restart", "backend")


# This is needed to check https override
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def ping_and_check_content(url: str, callback: Callable[[str], Optional[str]]):
    request = Request(url, headers={"Host": SITE_NAME})
    print(f"Checking {url}")
    for _ in range(100):
        try:
            response = urlopen(request, context=_ssl_ctx)
        except HTTPError as exc:
            if exc.code not in (404, 502):
                raise
        else:
            text: str = response.read().decode()
            ret = callback(text)
            if ret:
                print(ret)
                return

        sleep(0.1)
    raise AssertionError(f"Couldn't ping {url}")


def index_callback(text: str):
    if "404 page not found" not in text:
        return text[:200]


@log("Check /")
def check_index():
    ping_and_check_content(url="http://127.0.0.1", callback=index_callback)


@log("Check /api/method/version")
def check_api():
    ping_and_check_content(
        url="http://127.0.0.1/api/method/version",
        callback=lambda text: text if '"message"' in text else None,
    )


@log("Check if Frappe can connect to services in backends")
def ping_frappe_connections_in_backends():
    for service in BACKEND_SERVICES:
        docker_compose("cp", f"tests/ping_frappe_connections.py", f"{service}:/tmp/")
        docker_compose(
            "exec",
            service,
            "/home/frappe/frappe-bench/env/bin/python",
            f"/tmp/ping_frappe_connections.py",
        )


@log("Check /assets")
def check_assets():
    ping_and_check_content(
        url="http://127.0.0.1/assets/js/frappe-web.min.js",
        callback=lambda text: text[:200] if text is not None else None,
    )


@log("Check /files")
def check_files():
    file_name = "testfile.txt"
    docker_compose(
        "cp",
        f"tests/{file_name}",
        f"backend:/home/frappe/frappe-bench/sites/{SITE_NAME}/public/files/",
    )
    ping_and_check_content(
        url=f"http://127.0.0.1/files/{file_name}",
        callback=lambda text: text if text == "lalala\n" else None,
    )


@log("Recreate with https override")
def recreate_with_https_override():
    docker_compose("-f", "overrides/compose.https.yml", "up", "-d")


@log("Check / (https)")
def check_index_https():
    ping_and_check_content(url="https://127.0.0.1", callback=index_callback)


@log("Stop containers")
def stop_containers():
    docker_compose("down", "-v", "--remove-orphans")


@log("Recreate with ERPNext override")
def create_containers_with_erpnext_override():
    args = ["-f", "overrides/compose.erpnext.yml"]
    if CI:
        args.extend(("-f", "tests/compose.ci-erpnext.yml"))
    docker_compose(*args, "up", "-d")


@log("Create ERPNext site")
def create_erpnext_site():
    docker_compose(
        "exec",
        "backend",
        "bench",
        "new-site",
        SITE_NAME,
        "--mariadb-root-password",
        "123",
        "--admin-password",
        "admin",
        "--install-app",
        "erpnext",
    )
    docker_compose("restart", "backend")


@log("Check /api/method/erpnext.templates.pages.product_search.get_product_list")
def check_erpnext_api():
    ping_and_check_content(
        url="http://127.0.0.1/api/method/erpnext.templates.pages.product_search.get_product_list",
        callback=lambda text: text if '"message"' in text else None,
    )


@log("Check /assets/erpnext/js/setup_wizard.js")
def check_erpnext_assets():
    ping_and_check_content(
        url="http://127.0.0.1/assets/erpnext/js/setup_wizard.js",
        callback=lambda text: text[:200] if text is not None else None,
    )


@log("Create containers with Postgres override")
def create_containers_with_postgres_override():
    docker_compose("-f", "overrides/compose.postgres.yml", "up", "-d")


@log("Create Postgres site")
def create_postgres_site():
    docker_compose(
        "exec", "backend", "bench", "set-config", "-g", "root_login", "postgres"
    )
    docker_compose(
        "exec", "backend", "bench", "set-config", "-g", "root_password", "123"
    )
    docker_compose(
        "exec",
        "backend",
        "bench",
        "new-site",
        SITE_NAME,
        "--db-type",
        "postgres",
        "--admin-password",
        "admin",
    )
    docker_compose("restart", "backend")


@log("Delete .env")
def delete_env():
    os.remove("tests/.env")


@log("Show docker compose logs")
def show_docker_compose_logs():
    docker_compose("logs")


def main() -> int:
    try:
        patch_print()

        setup_env()
        print_compose_configuration()
        create_containers()

        ping_links_in_backends()
        create_site()
        check_index()
        check_api()
        ping_frappe_connections_in_backends()
        check_assets()
        check_files()

        recreate_with_https_override()
        check_index_https()
        stop_containers()

        create_containers_with_erpnext_override()
        create_erpnext_site()
        check_erpnext_api()
        check_erpnext_assets()
        stop_containers()

        create_containers_with_postgres_override()
        create_postgres_site()
        ping_links_in_backends()

    finally:
        delete_env()
        show_docker_compose_logs()
        stop_containers()

    print(colored("Tests successfully passed!", Color.YELLOW))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
