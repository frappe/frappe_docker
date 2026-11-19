import os
import ssl
import subprocess
import sys
import time
from contextlib import suppress
from http.client import HTTPResponse
from typing import Callable, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
    urlopen,
)

CI = os.getenv("CI")


class Compose:
    def __init__(
        self,
        project_name: str,
        env_file: str,
        files: Tuple[str, ...] = (
            "compose.yaml",
            "overrides/compose.proxy.yaml",
            "overrides/compose.mariadb.yaml",
            "overrides/compose.redis.yaml",
        ),
    ):
        self.project_name = project_name
        self.base_cmd = (
            "docker",
            "compose",
            "-p",
            project_name,
            "--env-file",
            env_file,
        )

        self.file_args = tuple(arg for filename in files for arg in ("-f", filename))
        if CI:
            self.file_args += ("-f", "tests/compose.ci.yaml")

    def __call__(self, *cmd: str) -> None:
        subprocess.check_call(self.base_cmd + self.file_args + cmd)

    def output(self, *cmd: str) -> str:
        return subprocess.run(
            self.base_cmd + self.file_args + cmd,
            text=True,
            capture_output=True,
            check=True,
        ).stdout

    def exec(self, *cmd: str) -> None:
        if sys.stdout.isatty():
            self("exec", *cmd)
        else:
            self("exec", "-T", *cmd)

    def stop(self) -> None:
        # Include the configured files so their named volumes are removed too.
        with suppress(subprocess.CalledProcessError):
            self("down", "-v", "--remove-orphans")

    def bench(self, *cmd: str) -> None:
        self.exec("backend", "bench", *cmd)


def check_url_content(
    url: str, callback: Callable[[str], Optional[str]], site_name: str
):
    for _ in range(100):
        try:
            response = wait_for_url(url=url, site_name=site_name, attempts=1)
        except RuntimeError:
            pass
        else:
            text: str = response.read().decode()
            ret = callback(text)
            if ret:
                print(ret)
                return

        time.sleep(0.1)

    raise RuntimeError(f"Couldn't verify expected content from {url}")


def wait_for_url(url: str, site_name: str, attempts: int = 100) -> HTTPResponse:
    request = Request(url, headers={"Host": site_name})

    # This is needed to check https override
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    last_error = None
    for _ in range(attempts):
        try:
            return urlopen(request, context=ctx)
        except HTTPError as exc:
            if exc.code not in (404, 502, 503):
                raise
            last_error = exc
            exc.close()
        except URLError as exc:
            last_error = exc

        time.sleep(0.1)

    raise RuntimeError(f"Couldn't ping {url}") from last_error


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
    try:
        response = opener.open(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == 302
        login_url = urlsplit(response.headers["Location"])
        assert login_url.path == "/login"
        return_url = urlsplit(parse_qs(login_url.query)["redirect-to"][0])
        assert return_url.scheme == scheme
        assert return_url.netloc == site
        assert return_url.path == path
        assert parse_qs(return_url.query) == {
            key: [value] for key, value in params.items()
        }
