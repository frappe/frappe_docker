import os
import ssl
import subprocess
import sys
import time
from contextlib import suppress
from http.client import HTTPResponse
from typing import Callable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
        return subprocess.check_output(
            self.base_cmd + self.file_args + cmd, text=True, stderr=subprocess.STDOUT
        )

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

    for _ in range(attempts):
        try:
            return urlopen(request, context=ctx)
        except HTTPError as exc:
            if exc.code not in (404, 502):
                raise
        except URLError:
            pass

        time.sleep(0.1)

    raise RuntimeError(f"Couldn't ping {url}")
