"""Check protocol metadata through the public nginx-proxy edge."""

import json
import os
import ssl
import subprocess
from http.cookies import SimpleCookie
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import pytest

from tests.utils import Compose, assert_oauth_return_url, wait_for_url

SITE = "nginx-proxy-tests.localhost"
SSL_OVERRIDE = "overrides/compose.nginxproxy-ssl.yaml"


@pytest.fixture(scope="module", autouse=True)
def frappe_setup(env_file: str, tmp_path_factory: pytest.TempPathFactory):
    # This module owns a separate stack, including its database and proxy volumes.
    root = tmp_path_factory.mktemp("nginx-proxy")
    certs = root / "certs"
    certs.mkdir()
    # Clients use a published loopback port. A default test certificate also
    # permits that TLS handshake without requiring local DNS for the virtual host.
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            f"/CN={SITE}",
            "-keyout",
            str(certs / "default.key"),
            "-out",
            str(certs / "default.crt"),
        ],
        check=True,
        capture_output=True,
    )
    tls_override = root / "tls.json"
    tls_override.write_text(
        json.dumps(
            {
                "services": {
                    "nginx-proxy": {
                        "volumes": [
                            {
                                "type": "bind",
                                "source": str(certs),
                                "target": "/etc/nginx/certs",
                                "read_only": True,
                            }
                        ]
                    }
                }
            }
        )
    )
    with pytest.MonkeyPatch.context() as environment:
        for name, value in {
            "HTTP_PUBLISH_PORT": "127.0.0.1:",
            "HTTPS_PUBLISH_PORT": "127.0.0.1:",
            "NGINX_PROXY_HOSTS": SITE,
            "FORWARDED_ALLOW_IPS": "*",
            "TRUST_UPSTREAM_FORWARDED_PROTO": "on",
        }.items():
            environment.setenv(name, value)
        project = os.getenv("FRAPPE_DOCKER_TEST_PROJECT", "test") + "-nginx-proxy"
        compose = Compose(
            project_name=project,
            env_file=env_file,
            files=(
                "compose.yaml",
                "overrides/compose.mariadb.yaml",
                "overrides/compose.redis.yaml",
                "overrides/compose.nginxproxy.yaml",
            ),
        )
        compose.stop()
        try:
            compose(
                "up",
                "-d",
                "--quiet-pull",
                "db",
                "redis-cache",
                "redis-queue",
                "backend",
                "frontend",
                "nginx-proxy",
            )
            compose.bench(
                "new-site",
                "--mariadb-user-host-login-scope=%",
                "--db-root-password=123",
                "--admin-password=admin",
                SITE,
            )
            compose("restart", "backend")
            yield compose, tls_override
        finally:
            try:
                (root / "containers.log").write_text(
                    compose.output(
                        "logs",
                        "--no-color",
                        "--tail",
                        "100",
                        "nginx-proxy",
                        "frontend",
                        "backend",
                    )
                )
            finally:
                # Also account for volumes introduced when the TLS profile is enabled.
                compose(
                    "-f",
                    SSL_OVERRIDE,
                    "-f",
                    str(tls_override),
                    "down",
                    "-v",
                    "--remove-orphans",
                )


def assert_login_cookie(base_url: str, forwarded_proto: str):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    request = Request(
        f"{base_url}/api/method/login",
        data=urlencode({"usr": "Administrator", "pwd": "admin"}).encode(),
        headers={"Host": SITE, "X-Forwarded-Proto": forwarded_proto},
    )
    with urlopen(request, context=context, timeout=10) as response:
        assert response.status == 200
        assert json.load(response)["message"] == "Logged In"
        cookies = SimpleCookie()
        for value in response.headers.get_all("Set-Cookie", []):
            cookies.load(value)
        assert "sid" in cookies
        assert bool(cookies["sid"]["secure"]) == (urlsplit(base_url).scheme == "https")


def test_public_http_ignores_client_protocol(frappe_setup):
    compose, _ = frappe_setup
    compose("up", "-d", "--no-deps", "frontend", "nginx-proxy")
    url = "http://" + compose.output("port", "nginx-proxy", "80").strip()
    wait_for_url(f"{url}/api/method/ping", SITE).close()
    for value in ("http", "https", "unknown"):
        assert_oauth_return_url(
            url,
            SITE,
            "http",
            {
                "X-Forwarded-Proto": value,
                "X-Forwarded-SSL": "on",
                "X-Forwarded-Protocol": "ssl",
            },
        )
    assert_login_cookie(url, "https")


def test_public_https_ignores_client_protocol(frappe_setup):
    compose, tls_override = frappe_setup
    compose(
        "-f",
        SSL_OVERRIDE,
        "-f",
        str(tls_override),
        "up",
        "-d",
        "--no-deps",
        "frontend",
        "nginx-proxy",
    )
    address = compose.output(
        "-f", SSL_OVERRIDE, "-f", str(tls_override), "port", "nginx-proxy", "443"
    ).strip()
    url = f"https://{address}"
    wait_for_url(f"{url}/api/method/ping", SITE).close()
    for value in ("http", "https", "unknown"):
        assert_oauth_return_url(
            url,
            SITE,
            "https",
            {
                "X-Forwarded-Proto": value,
                "X-Forwarded-SSL": "off",
                "X-Forwarded-Protocol": "http",
            },
        )
    assert_login_cookie(url, "http")
