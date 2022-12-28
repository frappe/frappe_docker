import os
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import S3ServiceResult
from tests.utils import Compose, check_url_content

BACKEND_SERVICES = (
    "backend",
    "queue-short",
    "queue-default",
    "queue-long",
    "scheduler",
)


@pytest.mark.parametrize("service", BACKEND_SERVICES)
def test_links_in_backends(service: str, compose: Compose, python_path: str):
    filename = "_check_connections.py"
    compose("cp", f"tests/{filename}", f"{service}:/tmp/")
    compose.exec(service, python_path, f"/tmp/{filename}")


def index_cb(text: str):
    if "404 page not found" not in text:
        return text[:200]


def api_cb(text: str):
    if '"message"' in text:
        return text


def assets_cb(text: str):
    if text:
        return text[:200]


@pytest.mark.parametrize(
    ("url", "callback"), (("/", index_cb), ("/api/method/version", api_cb))
)
def test_endpoints(url: str, callback: Any, frappe_site: str):
    check_url_content(
        url=f"http://127.0.0.1{url}", callback=callback, site_name=frappe_site
    )


@pytest.mark.skipif(
    os.environ["FRAPPE_VERSION"][0:3] == "v12", reason="v12 doesn't have the asset"
)
def test_assets_endpoint(frappe_site: str):
    check_url_content(
        url=f"http://127.0.0.1/assets/frappe/images/frappe-framework-logo.svg",
        callback=assets_cb,
        site_name=frappe_site,
    )


def test_files_reachable(frappe_site: str, tmp_path: Path, compose: Compose):
    content = "lalala\n"
    file_path = tmp_path / "testfile.txt"

    with file_path.open("w") as f:
        f.write(content)

    compose(
        "cp",
        str(file_path),
        f"backend:/home/frappe/frappe-bench/sites/{frappe_site}/public/files/",
    )

    def callback(text: str):
        if text == content:
            return text

    check_url_content(
        url=f"http://127.0.0.1/files/{file_path.name}",
        callback=callback,
        site_name=frappe_site,
    )


@pytest.mark.parametrize("service", BACKEND_SERVICES)
@pytest.mark.usefixtures("frappe_site")
def test_frappe_connections_in_backends(
    service: str, python_path: str, compose: Compose
):
    filename = "_ping_frappe_connections.py"
    compose("cp", f"tests/{filename}", f"{service}:/tmp/")
    compose.exec(service, python_path, f"/tmp/{filename}")


def test_push_backup(
    python_path: str,
    frappe_site: str,
    s3_service: S3ServiceResult,
    compose: Compose,
):
    compose.bench("--site", frappe_site, "backup", "--with-files")
    compose.exec(
        "backend",
        "push-backup",
        "--site",
        frappe_site,
        "--bucket",
        "frappe",
        "--region-name",
        "us-east-1",
        "--endpoint-url",
        "http://minio:9000",
        "--aws-access-key-id",
        s3_service.access_key,
        "--aws-secret-access-key",
        s3_service.secret_key,
    )
    compose("cp", "tests/_check_backup_files.py", "backend:/tmp")
    compose.exec(
        "-e",
        f"S3_ACCESS_KEY={s3_service.access_key}",
        "-e",
        f"S3_SECRET_KEY={s3_service.secret_key}",
        "-e",
        f"SITE_NAME={frappe_site}",
        "backend",
        python_path,
        "/tmp/_check_backup_files.py",
    )


def test_https(frappe_site: str, compose: Compose):
    compose("-f", "overrides/compose.https.yaml", "up", "-d")
    check_url_content(url="https://127.0.0.1", callback=index_cb, site_name=frappe_site)


@pytest.mark.usefixtures("erpnext_setup")
class TestErpnext:
    @pytest.mark.parametrize(
        ("url", "callback"),
        (
            (
                "/api/method/erpnext.templates.pages.product_search.get_product_list",
                api_cb,
            ),
            ("/assets/erpnext/js/setup_wizard.js", assets_cb),
        ),
    )
    def test_endpoints(self, url: str, callback: Any, erpnext_site: str):
        check_url_content(
            url=f"http://127.0.0.1{url}", callback=callback, site_name=erpnext_site
        )


@pytest.mark.usefixtures("postgres_setup")
class TestPostgres:
    def test_site_creation(self, compose: Compose):
        compose.bench(
            "new-site",
            "test_pg_site",
            "--db-type",
            "postgres",
            "--admin-password",
            "admin",
        )
