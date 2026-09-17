import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.utils import CI, Compose


def _add_version_var(name: str, env_path: Path):
    value = os.getenv(name)

    if not value:
        return

    if value == "develop":
        os.environ[name] = "latest"

    with open(env_path, "a") as f:
        f.write(f"\n{name}={os.environ[name]}")


def _add_sites_var(env_path: Path):
    with open(env_path, "r+") as f:
        content = f.read()
        sites = (
            "tests.localhost",
            "test-erpnext-site.localhost",
            "test-pg-site.localhost",
        )
        sites_rule = " || ".join(f"Host(`{site}`)" for site in sites)
        content = re.sub(rf"SITES_RULE=.*", f"SITES_RULE={sites_rule}", content)
        f.seek(0)
        f.truncate()
        f.write(content)


@pytest.fixture(scope="session")
def env_file(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("frappe-docker")
    file_path = tmp_path / ".env"
    shutil.copy("example.env", file_path)

    _add_sites_var(file_path)

    for var in ("FRAPPE_VERSION", "ERPNEXT_VERSION"):
        _add_version_var(name=var, env_path=file_path)

    yield str(file_path)
    os.remove(file_path)


@pytest.fixture(scope="session")
def compose(env_file: str):
    return Compose(project_name="test", env_file=env_file)


@pytest.fixture(autouse=True, scope="session")
def frappe_setup(compose: Compose):
    compose.stop()

    compose("up", "-d", "--quiet-pull")
    yield

    compose.stop()


@pytest.fixture(scope="session")
def frappe_site(compose: Compose):
    site_name = "tests.localhost"
    compose.bench(
        "new-site",
        # TODO: change to --mariadb-user-host-login-scope=%
        "--no-mariadb-socket",
        "--db-root-password=123",
        "--admin-password=admin",
        site_name,
    )
    compose("restart", "backend")
    yield site_name


@pytest.fixture(scope="class")
def erpnext_setup(compose: Compose):
    compose.stop()
    compose("up", "-d", "--quiet-pull")

    yield
    compose.stop()


@pytest.fixture(scope="class")
def erpnext_site(compose: Compose):
    site_name = "test-erpnext-site.localhost"
    args = [
        "new-site",
        # TODO: change to --mariadb-user-host-login-scope=%
        "--no-mariadb-socket",
        "--db-root-password=123",
        "--admin-password=admin",
        "--install-app=erpnext",
        site_name,
    ]
    compose.bench(*args)
    compose("restart", "backend")
    yield site_name


@pytest.fixture
def postgres_setup(compose: Compose):
    compose.stop()
    compose("-f", "overrides/compose.postgres.yaml", "up", "-d", "--quiet-pull")
    compose.bench("set-config", "-g", "root_login", "postgres")
    compose.bench("set-config", "-g", "root_password", "123")
    yield
    compose.stop()


@pytest.fixture
def python_path():
    return "/home/frappe/frappe-bench/env/bin/python"


@dataclass
class S3ServiceResult:
    endpoint_url: str
    bucket: str
    access_key: str
    secret_key: str


@pytest.fixture
def s3_service(python_path: str, compose: Compose):
    endpoint_url = "http://s3:8333"
    bucket = "frappe"
    access_key = "AKIAIOSFODNN7EXAMPLE"
    secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    container_name = f"{compose.project_name}-s3"
    try:
        subprocess.check_call(
            (
                "docker",
                "run",
                "--detach",
                "--pull=always",
                "--name",
                container_name,
                "--network",
                f"{compose.project_name}_default",
                "--network-alias",
                "s3",
                "-e",
                f"AWS_ACCESS_KEY_ID={access_key}",
                "-e",
                f"AWS_SECRET_ACCESS_KEY={secret_key}",
                "-e",
                f"S3_BUCKET={bucket}",
                "chrislusf/seaweedfs:latest",
                "mini",
                "-dir=/data",
            )
        )
        compose("cp", "tests/_wait_for_s3.py", "backend:/tmp")
        compose.exec("backend", "bench", "pip", "install", "boto3~=1.34.143")
        compose.exec(
            "-e",
            f"S3_ENDPOINT_URL={endpoint_url}",
            "-e",
            f"S3_BUCKET={bucket}",
            "-e",
            f"AWS_ACCESS_KEY_ID={access_key}",
            "-e",
            f"AWS_SECRET_ACCESS_KEY={secret_key}",
            "backend",
            python_path,
            "/tmp/_wait_for_s3.py",
        )

        yield S3ServiceResult(
            endpoint_url=endpoint_url,
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
        )
    finally:
        subprocess.call(("docker", "logs", "--tail", "100", container_name))
        subprocess.call(("docker", "rm", "-fv", container_name))
