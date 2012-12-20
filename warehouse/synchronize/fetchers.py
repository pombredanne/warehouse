from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import calendar
import datetime
import os
import urlparse

import requests
import xmlrpc2.client

from warehouse.synchronize import validators as warehouse_validators
from warehouse import utils


def filter_dict(unfiltered, required=None):
    if required is None:
        required = set()

    data = {}
    for key, value in unfiltered.items():
        if value is None:
            continue
        elif not key in required and value in ["None", "UNKNOWN"]:
            continue
        elif isinstance(value, (basestring, list, tuple, set)) and not value:
            continue
        else:
            data[key] = value
    return data


class PyPIFetcher(object):

    def __init__(self, client=None, session=None, validators=None):
        if session is None:
            certificate = os.path.join(os.path.dirname(__file__), "PyPI.crt")

            session = requests.session()
            session.verify = certificate

        # Patch the headers
        session.headers.update({"User-Agent": utils.user_agent()})

        # Store the session
        self.session = session

        if client is None:
            transports = [
                xmlrpc2.client.HTTPTransport(session=self.session),
                xmlrpc2.client.HTTPSTransport(session=self.session),
            ]
            client = xmlrpc2.client.Client("https://pypi.python.org/pypi",
                                            transports=transports)

        self.client = client

        if validators is None:
            validators = warehouse_validators

        self.validators = validators

    def classifiers(self):
        resp = self.session.get(
                    "https://pypi.python.org/pypi?:action=list_classifiers")
        return [c for c in resp.text.split("\n") if c]

    def file(self, url):
        """
        Fetches the file located at ``url``.
        """
        parsed = urlparse.urlparse(url)
        url = urlparse.urlunparse(("https",) + parsed[1:])

        resp = self.session.get(url)
        return resp.content

    def distributions(self, project, version):
        """
        Takes a project and version and it returns the normalized files for
        the release of project with the given version.
        """
        urls = self.client.release_urls(project, version)
        urls = self.validators.release_urls.validate(urls)

        keys = set([
            "filename", "filesize", "python_version", "type", "comment",
            "md5_digest", "url",
        ])

        for url in urls:
            url = filter_dict(url)

            # Rename size to filesize
            url["filesize"] = url["size"]

            # Rename packagetype to type
            url["type"] = url["packagetype"]

            # Rename comment_text to comment
            if "comment_text" in url:
                url["comment"] = url["comment_text"]

            yield dict(x for x in url.items() if x[0] in keys)

    def release(self, project, version):
        """
        Takes a project and version and it returns the normalized data for the
        release of project with that version.
        """
        data = self.client.release_data(project, version)
        data = filter_dict(data, required=set(["name", "version"]))
        data = self.validators.release_data.validate(data)

        # fix classifiers (dedupe + sort)
        data["classifiers"] = list(set(data.get("classifiers", [])))
        data["classifiers"].sort()

        # rename download_url to download_uri
        if "download_url" in data:
            data["download_uri"] = data["download_url"]

        # Collapse project_url, bugtrack_url, and home_page into uris
        data["uris"] = {}

        if "bugtrack_url" in data:
            data["uris"]["bugtracker"] = data["bugtrack_url"]

        if "home_page" in data:
            data["uris"]["home page"] = data["home_page"]

        if "project_url" in data:
            data["uris"].update(data["project_url"])

        # Filter resulting dictionary down to only the required keys
        keys = set([
            "name", "version", "summary", "description", "author",
            "author_email", "maintainer", "maintainer_email", "license",
            "requires_python", "requires_external", "uris", "keywords",
            "download_uri", "classifiers",
        ])

        return dict(x for x in data.items() if x[0] in keys)

    def versions(self, project):
        """
        Returns a list of all the versions for a particular project.
        """
        versions = self.client.package_releases(project, True)
        return self.validators.package_releases.validate(versions)

    def projects(self, since=None):
        """
        Returns a list of all project names
        """
        if since is None:
            packages = self.client.list_packages()
            return set(self.validators.list_packages.validate(packages))
        else:
            since = since - 1
            changes = self.client.changelog(since)

            # TODO(dstufft): validate output

            updated = set()

            for name, version, _timestamp, action in changes:
                if not (action.lower() == "remove" and version is None):
                    updated.add(name)

            return updated

    def deletions(self, since=None):
        if since is None:
            # With no point of reference we must assume there has been
            #   deletions
            return True
        else:
            since = since - 1
            changes = self.client.changelog(since)

            # TODO(dstufft): validate output

            for _name, version, _timestamp, action in changes:
                if action.lower() == "remove" and version is None:
                    # If we find *any* project deletions we know there was
                    #   at least one and can say True
                    return True

            # We've found no deletions, so False
            return False

    def current(self):
        current_string = self.session.get("https://pypi.python.org/daytime")
        current = datetime.datetime.strptime(
                        current_string.text.strip(),
                        "%Y%m%dT%H:%M:%S"
                    )
        return int(calendar.timegm(current.timetuple()))
