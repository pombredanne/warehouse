import datetime
import os

import mock
import pretend
import pytest

import requests
import xmlrpc2.client

from warehouse import utils
from warehouse.synchronize import fetchers


NOW = datetime.datetime.utcnow()


@pytest.mark.parametrize(("inp", "expected"), [
    ({"a": None}, {}),
    ({"b": "None"}, {}),
    ({"c": "UNKNOWN"}, {}),
    ({"d": 0}, {"d": 0}),
    ({"e": "Wat"}, {"e": "Wat"}),
    ({"f": []}, {}),
])
def test_filter_dict(inp, expected):
    assert fetchers.filter_dict(inp) == expected


@pytest.mark.parametrize(("inp", "expected"), [
    ({"Name": "None", "b": "None"}, {"Name": "None"}),
    ({"Name": "UNKNOWN", "c": "UNKNOWN"}, {"Name": "UNKNOWN"}),
])
def test_filter_dict_required(inp, expected):
    assert fetchers.filter_dict(inp, required=["Name"]) == expected


def test_fetcher_session_initialize(monkeypatch):
    monkeypatch.setattr(requests, "session", mock.Mock(spec_set=["verify"]))

    client = pretend.stub()
    fetcher = fetchers.PyPIFetcher(client=client)
    certificate = os.path.join(os.path.dirname(fetchers.__file__), "PyPI.crt")

    assert fetcher.session.verify == certificate


def test_fetcher_client_initialize(monkeypatch):
    http_transport_stub = pretend.stub()
    https_transport_stub = pretend.stub()

    http_transport = mock.Mock(return_value=http_transport_stub)
    https_transport = mock.Mock(return_value=https_transport_stub)
    client = mock.Mock()

    monkeypatch.setattr(xmlrpc2.client, "HTTPTransport", http_transport)
    monkeypatch.setattr(xmlrpc2.client, "HTTPSTransport", https_transport)
    monkeypatch.setattr(xmlrpc2.client, "Client", client)

    session = pretend.stub(headers={})

    fetchers.PyPIFetcher(session=session)

    http_transport.assert_called_once_with(session=session)
    https_transport.assert_called_once_with(session=session)
    client.assert_called_once_with(
                "https://pypi.python.org/pypi",
                transports=[http_transport_stub, https_transport_stub],
            )


@pytest.mark.parametrize(("user_agent", "headers", "expected"), [
    ("Warehouse Test", {}, {"User-Agent": "Warehouse Test"}),
    ("Warehouse Test", {"Foo": "Bar"},
                            {"Foo": "Bar", "User-Agent": "Warehouse Test"}),
])
def test_fetcher_user_agent(user_agent, headers, expected, monkeypatch):
    monkeypatch.setattr(utils, "user_agent", lambda: user_agent)

    session = pretend.stub(headers=headers)
    client = pretend.stub()

    fetcher = fetchers.PyPIFetcher(session=session, client=client)

    assert fetcher.session.headers == expected


@pytest.mark.parametrize(("inp", "expected"), [
    ("20121220T13:15:29", 1356009329),
])
def test_fetcher_current(inp, expected):
    session = pretend.stub(headers={}, get=lambda x: pretend.stub(text=inp))
    client = pretend.stub()

    fetcher = fetchers.PyPIFetcher(session=session, client=client)

    assert fetcher.current() == expected


@pytest.mark.parametrize(("response_text", "expected"), [
    ("Testing :: Foo\nTesting :: Bar\n", ["Testing :: Foo", "Testing :: Bar"]),
])
def test_fetcher_classifiers(response_text, expected):
    session = pretend.stub(
                headers={},
                get=lambda x: pretend.stub(text=response_text),
            )
    client = pretend.stub()

    fetcher = fetchers.PyPIFetcher(session=session, client=client)

    assert fetcher.classifiers() == expected


@pytest.mark.parametrize(("client_response", "expected"), [
    (["Foo", "bar"], set(["Foo", "bar"])),
])
def test_fetcher_projects(client_response, expected):
    session = pretend.stub(headers={})
    client = pretend.stub(list_packages=lambda: client_response)
    validators = pretend.stub(list_packages=pretend.stub(validate=lambda x: x))

    fetcher = fetchers.PyPIFetcher(
                            session=session,
                            client=client,
                            validators=validators,
                        )

    assert fetcher.projects() == expected


@pytest.mark.parametrize(("project", "client_response", "expected"), [
    ("Test", ["1.0", "2.0"], ["1.0", "2.0"]),
])
def test_fetcher_versions(project, client_response, expected):
    session = pretend.stub(headers={})
    client = pretend.stub(package_releases=lambda _1, _2: client_response)
    validators = pretend.stub(
                    package_releases=pretend.stub(validate=lambda x: x),
                )

    fetcher = fetchers.PyPIFetcher(
                            session=session,
                            client=client,
                            validators=validators,
                        )

    assert fetcher.versions(project) == expected


@pytest.mark.parametrize(
    ("project", "version", "client_response", "expected"),
    [
        (
            "Test", "1.0",
            {"name": "Test", "version": "1.0"},
            {"name": "Test", "version": "1.0", "classifiers": [], "uris": {}},
        ),
        (
            "Test", "1.0",
            {
                "name": "Test",
                "version": "1.0",
                "download_url": "http://test.local/Test-1.0.tar.gz",
            },
            {
                "name": "Test",
                "version": "1.0",
                "download_uri": "http://test.local/Test-1.0.tar.gz",
                "classifiers": [],
                "uris": {},
            },
        ),
        (
            "Test", "1.0",
            {
                "name": "Test",
                "version": "1.0",
                "bugtrack_url": "http://test.local/issues/",
            },
            {
                "name": "Test",
                "version": "1.0",
                "classifiers": [],
                "uris": {"bugtracker": "http://test.local/issues/"},
            },
        ),
        (
            "Test", "1.0",
            {
                "name": "Test",
                "version": "1.0",
                "home_page": "http://test.local/",
            },
            {
                "name": "Test",
                "version": "1.0",
                "classifiers": [],
                "uris": {"home page": "http://test.local/"},
            },
        ),
        (
            "Test", "1.0",
            {
                "name": "Test",
                "version": "1.0",
                "project_url": {"testing": "http://test.local/testing/"},
            },
            {
                "name": "Test",
                "version": "1.0",
                "classifiers": [],
                "uris": {"testing": "http://test.local/testing/"},
            },
        ),
    ],
)
def test_fetcher_release(project, version, client_response, expected):
    session = pretend.stub(headers={})
    client = pretend.stub(release_data=lambda _1, _2: client_response)
    validators = pretend.stub(release_data=pretend.stub(validate=lambda x: x))

    fetcher = fetchers.PyPIFetcher(
                            session=session,
                            client=client,
                            validators=validators,
                        )

    assert fetcher.release(project, version) == expected


@pytest.mark.parametrize(
    ("project", "version", "client_response", "expected"),
    [
        (
            "Test", "1.0",
            [{
                "has_sig": False,
                "upload_time": NOW,
                "python_version": "any",
                "url": "http://files.test.local/T/Test/Test-1.0.tar.gz",
                "md5_digest": "aabcd",
                "downloads": 1,
                "filename": "Test-1.0.tar.gz",
                "packagetype": "sdist",
                "size": 100,
                "comment_test": "",
            }],
            [{
                "python_version": "any",
                "created": NOW,
                "url": "http://files.test.local/T/Test/Test-1.0.tar.gz",
                "md5_digest": "aabcd",
                "filename": "Test-1.0.tar.gz",
                "type": "sdist",
                "filesize": 100,
            }],
        ),
        (
            "Test", "1.0",
            [{
                "has_sig": False,
                "upload_time": NOW,
                "python_version": "any",
                "url": "http://files.test.local/T/Test/Test-1.0.tar.gz",
                "md5_digest": "aabcd",
                "downloads": 1,
                "filename": "Test-1.0.tar.gz",
                "packagetype": "sdist",
                "size": 100,
                "comment_text": "This is a comment!",
            }],
            [{
                "python_version": "any",
                "created": NOW,
                "url": "http://files.test.local/T/Test/Test-1.0.tar.gz",
                "md5_digest": "aabcd",
                "filename": "Test-1.0.tar.gz",
                "type": "sdist",
                "filesize": 100,
                "comment": "This is a comment!",
            }],
        ),
    ],
)
def test_fetcher_distributions(project, version, client_response, expected):
    session = pretend.stub(headers={})
    client = pretend.stub(release_urls=lambda _1, _2: client_response)
    validators = pretend.stub(release_urls=pretend.stub(validate=lambda x: x))

    fetcher = fetchers.PyPIFetcher(
                            session=session,
                            client=client,
                            validators=validators,
                        )

    assert list(fetcher.distributions(project, version)) == expected


@pytest.mark.parametrize(("url", "https_url", "content"), [
    (
        "http://files.test.local/T/Test/Test-1.0.tar.gz",
        "https://files.test.local/T/Test/Test-1.0.tar.gz",
        "File Content!",
    ),
    (
        "https://files.test.local/F/Foo/Foo-2.0.tar.gz",
        "https://files.test.local/F/Foo/Foo-2.0.tar.gz",
        "File Content!",
    ),
])
def test_fetcher_files(url, https_url, content):
    session_get = mock.Mock(return_value=pretend.stub(content=content))
    session = pretend.stub(headers={}, get=session_get)
    client = pretend.stub()

    fetcher = fetchers.PyPIFetcher(session=session, client=client)

    assert fetcher.file(url) == content

    session_get.assert_called_once_with(https_url)
