import json
import os
import ssl
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import pytest

from tests.conftest import S3ServiceResult
from tests.utils import Compose, check_url_content, wait_for_url

BACKEND_SERVICES = (
    "backend",
    "queue-short",
    "queue-long",
    "scheduler",
)


def test_wkhtmltopdf_installation(compose: Compose, python_path: str):
    expected = os.getenv("INSTALL_WKHTMLTOPDF", "true") != "false"
    compose.exec(
        "backend",
        python_path,
        "-c",
        f"import shutil; assert bool(shutil.which('wkhtmltopdf')) == {expected}",
    )
    if expected:
        compose.exec("backend", "wkhtmltopdf", "--version")


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
    ("url", "callback"), (("/", index_cb), ("/api/method/ping", api_cb))
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


def test_files_html_security_headers(
    frappe_site: str, tmp_path: Path, compose: Compose
):
    file_path = tmp_path / "testfile.html"
    file_path.write_text(
        "<html><body>This is a Frappe Docker test html file</body></html>"
    )

    compose(
        "cp",
        str(file_path),
        f"backend:/home/frappe/frappe-bench/sites/{frappe_site}/public/files/",
    )

    response = wait_for_url(
        url=f"http://127.0.0.1/files/{file_path.name}",
        site_name=frappe_site,
    )

    assert response.headers["Content-Disposition"] == "attachment"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("service", BACKEND_SERVICES)
@pytest.mark.usefixtures("frappe_site")
def test_frappe_connections_in_backends(
    service: str, python_path: str, compose: Compose
):
    filename = "_ping_frappe_connections.py"
    compose("cp", f"tests/{filename}", f"{service}:/tmp/")
    compose.exec(
        "-w",
        "/home/frappe/frappe-bench/sites",
        service,
        python_path,
        f"/tmp/{filename}",
    )


def test_push_backup(
    frappe_site: str,
    s3_service: S3ServiceResult,
    compose: Compose,
):
    restic_password = "secret"
    compose.bench("--site", frappe_site, "backup", "--with-files")
    restic_args = [
        f"--env=RESTIC_REPOSITORY=s3:{s3_service.endpoint_url}/{s3_service.bucket}",
        f"--env=AWS_ACCESS_KEY_ID={s3_service.access_key}",
        f"--env=AWS_SECRET_ACCESS_KEY={s3_service.secret_key}",
        f"--env=RESTIC_PASSWORD={restic_password}",
    ]
    compose.exec(*restic_args, "backend", "restic", "init")
    compose.exec(*restic_args, "backend", "restic", "backup", "sites")
    compose.exec(*restic_args, "backend", "restic", "snapshots")
    compose.exec(*restic_args, "backend", "restic", "check", "--read-data")


def assert_oauth_return_url(
    base_url: str, site: str, scheme: str, headers: Optional[Dict[str, str]] = None
) -> None:
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    opener = build_opener(NoRedirect, HTTPSHandler(context=context))
    params = {
        "client_id": "proxy-regression-test",
        "redirect_uri": "https://client.example.test/callback",
        "response_type": "code",
        "state": "preserve&query=parameters",
    }
    query = urlencode(params)
    path = "/api/method/frappe.integrations.oauth2.authorize"
    request = Request(
        f"{base_url}{path}?{query}", headers={"Host": site, **(headers or {})}
    )
    with pytest.raises(HTTPError) as redirect:
        opener.open(request, timeout=10)
    with redirect.value as response:
        assert response.code == 302
        login_url = urlsplit(response.headers["Location"])
        assert login_url.path == "/login"
        return_url = urlsplit(parse_qs(login_url.query)["redirect-to"][0])
        assert return_url.scheme == scheme
        assert return_url.netloc == site
        assert return_url.path == path
        assert parse_qs(return_url.query) == {
            key: [value] for key, value in params.items()
        }


@pytest.fixture
def proxy_frontend(compose: Compose, frappe_site: str, tmp_path: Path, request):
    mode, allowed_ips = request.param
    config = {
        "services": {
            "frontend": {
                "environment": {"TRUST_UPSTREAM_FORWARDED_PROTO": mode},
                "ports": [{"target": 8080, "host_ip": "127.0.0.1"}],
            },
        }
    }
    override = tmp_path / "proxy-headers.json"
    override.write_text(json.dumps(config))
    try:
        compose(
            "-f",
            str(override),
            "up",
            "-d",
            "--no-deps",
            "--force-recreate",
            "frontend",
        )
        if allowed_ips == "frontend":
            allowed_ips = compose.output(
                "exec", "-T", "frontend", "getent", "ahostsv4", "frontend"
            ).split()[0]
        config["services"]["backend"] = {
            "environment": {"FORWARDED_ALLOW_IPS": allowed_ips}
        }
        override.write_text(json.dumps(config))
        compose("-f", str(override), "up", "-d", "--no-deps", "backend")
        # Refresh Nginx's upstream DNS after backend recreation without changing
        # the frontend address that the explicit allowlist just selected.
        compose("restart", "frontend")
        address = compose.output(
            "-f", str(override), "port", "frontend", "8080"
        ).strip()
        url = f"http://{address}"
        wait_for_url(f"{url}/api/method/ping", frappe_site).close()
        yield url
    finally:
        compose("up", "-d", "--no-deps", "--force-recreate", "backend", "frontend")


@pytest.mark.parametrize(
    ("proxy_frontend", "https_scheme"),
    [
        (("off", "*"), "http"),
        (("on", "*"), "https"),
        (("on", "127.0.0.1,::1"), "http"),
        (("on", "frontend"), "https"),
    ],
    indirect=["proxy_frontend"],
    ids=["direct", "wildcard", "loopback-only", "explicit-frontend-ip"],
)
def test_proxy_headers(proxy_frontend: str, https_scheme: str, frappe_site: str):
    for headers, scheme in (
        ({"X-Forwarded-Proto": "https"}, https_scheme),
        ({"X-Forwarded-Proto": "http"}, "http"),
        ({"X-Forwarded-Proto": "unknown"}, "http"),
        ({}, "http"),
        (
            {
                "X-Forwarded-Proto": "https",
                "X-Forwarded-SSL": "off",
                "X-Forwarded-Protocol": "http",
            },
            https_scheme,
        ),
    ):
        assert_oauth_return_url(proxy_frontend, frappe_site, scheme, headers)


def test_invalid_proxy_mode(compose: Compose):
    with pytest.raises(subprocess.CalledProcessError) as invalid:
        compose.output(
            "run",
            "--rm",
            "--no-deps",
            "--entrypoint",
            "nginx-entrypoint.sh",
            "-e",
            "TRUST_UPSTREAM_FORWARDED_PROTO=invalid",
            "frontend",
        )
    assert "must be on or off" in invalid.value.output


@pytest.mark.parametrize("host_caddy", [False, True], ids=["direct", "host-caddy"])
def test_proxy_configuration(tmp_path: Path, host_caddy: bool, monkeypatch):
    for name in (
        "HTTP_PUBLISH_PORT",
        "TRUST_UPSTREAM_FORWARDED_PROTO",
        "FORWARDED_ALLOW_IPS",
    ):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    settings = Path("example.env").read_text()
    if host_caddy:
        settings += "\nTRUST_UPSTREAM_FORWARDED_PROTO=on\nFORWARDED_ALLOW_IPS=*\nHTTP_PUBLISH_PORT=127.0.0.1:8080\n"
    env_file.write_text(settings)
    compose = Compose(
        project_name="proxy-config-test",
        env_file=str(env_file),
        files=(
            "compose.yaml",
            "overrides/compose.mariadb.yaml",
            "overrides/compose.redis.yaml",
            "overrides/compose.noproxy.yaml",
        ),
    )
    services = json.loads(compose.output("config", "--format", "json"))["services"]
    assert services["frontend"]["environment"]["TRUST_UPSTREAM_FORWARDED_PROTO"] == (
        "on" if host_caddy else "off"
    )
    assert services["backend"]["environment"]["FORWARDED_ALLOW_IPS"] == (
        "*" if host_caddy else "127.0.0.1,::1"
    )
    assert not services["backend"].get("ports")
    if host_caddy:
        ports = services["frontend"]["ports"]
        assert len(ports) == 1
        assert ports[0]["host_ip"] == "127.0.0.1"
        assert ports[0]["published"] == "8080"
        assert ports[0]["target"] == 8080


def test_https(frappe_site: str, compose: Compose):
    compose("-f", "overrides/compose.https.yaml", "up", "-d")
    address = compose.output(
        "-f", "overrides/compose.https.yaml", "port", "proxy", "443"
    ).strip()
    url = f"https://{address}"
    check_url_content(url=url, callback=index_cb, site_name=frappe_site)
    assert_oauth_return_url(url, frappe_site, "https")


@pytest.mark.usefixtures("erpnext_setup")
class TestErpnext:
    @pytest.mark.parametrize(
        ("url", "callback"),
        (
            (
                "/api/method/erpnext.templates.pages.search_help.get_help_results_sections?text=help",
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
            "test-pg-site.localhost",
            "--db-type",
            "postgres",
            "--admin-password",
            "admin",
        )


def test_arbitrary_uid_execution(compose: Compose):
    """Verify backend and frontend containers start and run under arbitrary UID with GID 0 (OpenShift restricted-v2).

    Executes the entrypoints directly to verify:
    - Container startup with arbitrary non-root UID (1000680000) and GID 0
    - Effective runtime umask (0002)
    - Writability of runtime paths, the bench root, and installed app directories/files
    - Frontend nginx configuration test under arbitrary UID
    """
    check_script = (
        "import os\n"
        "import tempfile\n"
        "uid = os.getuid()\n"
        "gid = os.getgid()\n"
        "assert uid == 1000680000, f'Expected UID 1000680000, got {uid}'\n"
        "assert gid == 0, f'Expected GID 0, got {gid}'\n"
        "with open('/etc/passwd') as f:\n"
        "    frappe_lines = [line for line in f if line.startswith('frappe:')]\n"
        "assert len(frappe_lines) == 1, f'Expected exactly 1 frappe user, found {len(frappe_lines)}'\n"
        "assert not os.access('/etc/passwd', os.W_OK), '/etc/passwd must not be writable'\n"
        "old_umask = os.umask(0)\n"
        "os.umask(old_umask)\n"
        "assert old_umask == 0o002, f'Expected umask 0002, got {oct(old_umask)}'\n"
        "bench_path = '/home/frappe/frappe-bench'\n"
        "for directory in ('/tmp', '/home/frappe', bench_path, f'{bench_path}/sites'):\n"
        "    with tempfile.NamedTemporaryFile(dir=directory) as f:\n"
        "        f.write(b'ok')\n"
        "for app in ('frappe', 'erpnext'):\n"
        "    app_path = f'{bench_path}/apps/{app}'\n"
        "    if not os.path.isdir(app_path):\n"
        "        continue\n"
        "    with tempfile.NamedTemporaryFile(dir=app_path) as f:\n"
        "        f.write(b'ok')\n"
        "    with open(f'{app_path}/{app}/__init__.py', 'r+b'):\n"
        "        pass\n"
        "print(f'VERIFIED:{uid}:{gid}')\n"
    )

    compose(
        "run",
        "--rm",
        "--no-deps",
        "--user",
        "1000680000:0",
        "backend",
        "/home/frappe/frappe-bench/env/bin/python",
        "-c",
        check_script,
    )

    compose(
        "run",
        "--rm",
        "--no-deps",
        "--user",
        "1000680000:0",
        "frontend",
        "nginx",
        "-t",
    )
