import pytest


@pytest.mark.parametrize("url", ["/v1/", "/v1/projects/", "/v1/versions/", "/v1/files/"])
def test_unauthenticated_access(client, url):
    resp = client.get(url, ACCEPT="application/json")
    assert resp.status_code == 200


def test_fail():
    assert False
