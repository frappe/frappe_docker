import pytest

from tests import conftest


@pytest.fixture(autouse=True, scope="session")
def frappe_setup():
    yield


class FakeCompose:
    def __init__(self):
        self.bench_calls = []
        self.compose_calls = []

    def __call__(self, *cmd):
        self.compose_calls.append(cmd)

    def bench(self, *cmd):
        self.bench_calls.append(cmd)


@pytest.mark.parametrize("fixture", (conftest.frappe_site, conftest.erpnext_site))
def test_mariadb_site_creation_allows_all_container_hosts(fixture):
    compose = FakeCompose()
    site = fixture.__wrapped__(compose)

    next(site)

    assert "--mariadb-user-host-login-scope=%" in compose.bench_calls[0]
