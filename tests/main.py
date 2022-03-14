import os
import shlex
import shutil
import ssl
import subprocess
import sys
from enum import Enum
from functools import wraps
from textwrap import dedent
from time import sleep
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
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
S3_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
S3_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
TTY = sys.stdout.isatty()


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
                output = (
                    f"\n{f' {text} '.center(os.get_terminal_size().columns, '=')}\n"
                )
                print(colored(output, Color.YELLOW))

            ret = f(*args, **kwargs)

            if CI:
                print("::endgroup::")
            return ret

        return wrapper

    return decorator


def run(*cmd: str):
    print(colored(f"> {shlex.join(cmd)}", Color.GREEN))
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
        "compose.yaml",
        "-f",
        "overrides/compose.proxy.yaml",
        "-f",
        "overrides/compose.mariadb.yaml",
        "-f",
        "overrides/compose.redis.yaml",
    ]
    if CI:
        args.extend(("-f", "tests/compose.ci.yaml"))
    return run(*args, *cmd)


def docker_compose_exec(*cmd: str):
    if TTY:
        return docker_compose("exec", *cmd)
    else:
        return docker_compose("exec", "-T", *cmd)


@log("Setup .env")
def setup_env():
    shutil.copy("example.env", "tests/.env")

    if not CI:
        return

    for var in ("FRAPPE_VERSION", "ERPNEXT_VERSION"):
        if os.environ[var] == "develop":
            with open(os.environ["GITHUB_ENV"], "a") as f:
                f.write(f"\n{var}=latest")
            os.environ[var] = "latest"

    with open("tests/.env", "a") as f:
        f.write(
            dedent(
                f"""
            FRAPPE_VERSION={os.environ['FRAPPE_VERSION']}
            ERPNEXT_VERSION={os.environ['ERPNEXT_VERSION']}
        """
            )
        )

    with open("tests/.env") as f:
        print(f.read())


@log("Print configuration")
def print_compose_configuration():
    docker_compose("config")


@log("Create containers")
def create_containers():
    docker_compose("up", "-d", "--quiet-pull")


@log("Check if Python services have connections")
def ping_links_in_backends():
    for service in BACKEND_SERVICES:
        docker_compose("cp", "tests/healthcheck.sh", f"{service}:/tmp/")
        for _ in range(10):
            try:
                docker_compose_exec(service, "bash", "/tmp/healthcheck.sh")
                break
            except subprocess.CalledProcessError:
                sleep(1)
        else:
            raise RuntimeError(f"Connections healthcheck failed for service {service}")


@log("Create site")
def create_site():
    docker_compose_exec(
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

        except URLError:
            pass

        else:
            text: str = response.read().decode()
            ret = callback(text)
            if ret:
                print(ret)
                return

        sleep(0.1)

    raise RuntimeError(f"Couldn't ping {url}")


def check_index_callback(text: str):
    if "404 page not found" not in text:
        return text[:200]


@log("Check /")
def check_index():
    ping_and_check_content("http://127.0.0.1", check_index_callback)


@log("Check /api/method/version")
def check_api():
    ping_and_check_content(
        "http://127.0.0.1/api/method/version",
        lambda text: text if '"message"' in text else None,
    )


@log("Check if Frappe can connect to services in Python services")
def ping_frappe_connections_in_backends():
    for service in BACKEND_SERVICES:
        docker_compose("cp", "tests/_ping_frappe_connections.py", f"{service}:/tmp/")
        docker_compose_exec(
            service,
            "/home/frappe/frappe-bench/env/bin/python",
            f"/tmp/_ping_frappe_connections.py",
        )


@log("Check /assets")
def check_assets():
    ping_and_check_content(
        "http://127.0.0.1/assets/frappe/images/frappe-framework-logo.svg",
        lambda text: text[:200] if text else None,
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
        f"http://127.0.0.1/files/{file_name}",
        lambda text: text if text == "lalala\n" else None,
    )


@log("Prepare S3 server")
def prepare_s3_server():
    run(
        "docker",
        "run",
        "--name",
        "minio",
        "-d",
        "-e",
        f"MINIO_ACCESS_KEY={S3_ACCESS_KEY}",
        "-e",
        f"MINIO_SECRET_KEY={S3_SECRET_KEY}",
        "--network",
        "test_default",
        "minio/minio",
        "server",
        "/data",
    )
    docker_compose("cp", "tests/_create_bucket.py", "backend:/tmp")
    docker_compose_exec(
        "-e",
        f"S3_ACCESS_KEY={S3_ACCESS_KEY}",
        "-e",
        f"S3_SECRET_KEY={S3_SECRET_KEY}",
        "backend",
        "/home/frappe/frappe-bench/env/bin/python",
        "/tmp/_create_bucket.py",
    )


@log("Push backup to S3")
def push_backup_to_s3():
    docker_compose_exec(
        "backend", "bench", "--site", SITE_NAME, "backup", "--with-files"
    )
    docker_compose_exec(
        "backend",
        "push-backup",
        "--site",
        SITE_NAME,
        "--bucket",
        "frappe",
        "--region-name",
        "us-east-1",
        "--endpoint-url",
        "http://minio:9000",
        "--aws-access-key-id",
        S3_ACCESS_KEY,
        "--aws-secret-access-key",
        S3_SECRET_KEY,
    )


@log("Check backup files in S3")
def check_backup_in_s3():
    docker_compose("cp", "tests/_check_backup_files.py", "backend:/tmp")
    docker_compose_exec(
        "-e",
        f"S3_ACCESS_KEY={S3_ACCESS_KEY}",
        "-e",
        f"S3_SECRET_KEY={S3_SECRET_KEY}",
        "-e",
        f"SITE_NAME={SITE_NAME}",
        "backend",
        "/home/frappe/frappe-bench/env/bin/python",
        "/tmp/_check_backup_files.py",
    )


@log("Stop S3 container")
def stop_s3_container():
    run("docker", "rm", "minio", "-f")


@log("Recreate with HTTPS override")
def recreate_with_https_override():
    docker_compose("-f", "overrides/compose.https.yaml", "up", "-d")


@log("Check / (HTTPS)")
def check_index_https():
    ping_and_check_content("https://127.0.0.1", check_index_callback)


@log("Stop containers")
def stop_containers():
    docker_compose("down", "-v", "--remove-orphans")


@log("Recreate with ERPNext override")
def create_containers_with_erpnext_override():
    args = ["-f", "overrides/compose.erpnext.yaml"]
    if CI:
        args += ("-f", "tests/compose.ci-erpnext.yaml")

    docker_compose(*args, "up", "-d", "--quiet-pull")


@log("Create ERPNext site")
def create_erpnext_site():
    docker_compose_exec(
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


@log("Check /api/method")
def check_erpnext_api():
    ping_and_check_content(
        "http://127.0.0.1/api/method/erpnext.templates.pages.product_search.get_product_list",
        lambda text: text if '"message"' in text else None,
    )


@log("Check /assets")
def check_erpnext_assets():
    ping_and_check_content(
        "http://127.0.0.1/assets/erpnext/js/setup_wizard.js",
        lambda text: text[:200] if text else None,
    )


@log("Create containers with Postgres override")
def create_containers_with_postgres_override():
    docker_compose("-f", "overrides/compose.postgres.yaml", "up", "-d", "--quiet-pull")


@log("Create Postgres site")
def create_postgres_site():
    docker_compose_exec(
        "backend", "bench", "set-config", "-g", "root_login", "postgres"
    )
    docker_compose_exec("backend", "bench", "set-config", "-g", "root_password", "123")
    docker_compose_exec(
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


@log("Show logs")
def show_docker_compose_logs():
    docker_compose("logs")


def start():
    setup_env()
    print_compose_configuration()
    create_containers()
    ping_links_in_backends()


def create_frappe_site_and_check_availability():
    create_site()
    check_index()
    check_api()
    ping_frappe_connections_in_backends()
    check_assets()
    check_files()


def check_s3():
    prepare_s3_server()

    try:
        push_backup_to_s3()
        check_backup_in_s3()
    finally:
        stop_s3_container()


def check_https():
    print_compose_configuration()
    recreate_with_https_override()
    check_index_https()
    stop_containers()


def check_erpnext():
    print_compose_configuration()
    create_containers_with_erpnext_override()
    create_erpnext_site()
    check_erpnext_api()
    check_erpnext_assets()
    stop_containers()


def check_postgres():
    print_compose_configuration()
    create_containers_with_postgres_override()
    create_postgres_site()
    ping_links_in_backends()


def main() -> int:
    try:
        patch_print()
        start()
        create_frappe_site_and_check_availability()
        check_s3()
        check_https()
        check_erpnext()
        check_postgres()

    finally:
        delete_env()
        show_docker_compose_logs()
        stop_containers()

    print(colored("\nTests successfully passed!", Color.YELLOW))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
