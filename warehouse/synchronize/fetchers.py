from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import calendar
import datetime
import logging
import os
import urlparse

import requests
import xmlrpc2.client

import warehouse

from warehouse.synchronize import validators as warehouse_validators


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
            logger.debug("Using the certificate located at '%s'", certificate)

            session = requests.session()
            session.verify = certificate

        # Patch the headers
        version = warehouse.__version__  # pylint: disable=E1101
        session.headers.update({
            "User-Agent": "warehouse/{version}".format(version=version),
        })

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
        logger.debug("Fetching classifiers from pypi.python.org")
        resp = self.session.get(
                    "https://pypi.python.org/pypi?:action=list_classifiers")
        return [c for c in resp.text.split("\n") if c]

    def file(self, url):
        """
        Fetches the file located at ``url``.
        """
        # TODO(dstufft): Validate File Content?
        parsed = urlparse.urlparse(url)
        url = urlparse.urlunparse(("https",) + parsed[1:])

        logger.debug("Fetching '%s'", url)

        resp = self.session.get(url)
        return resp.content

    def distributions(self, project, version):
        """
        Takes a project and version and it returns the normalized files for
        the release of project with the given version.
        """
        logger.debug(
            "Fetching distributions for '%s' version '%s' "
                "from pypi.python.org",
            project,
            version,
        )

        urls = self.client.release_urls(project, version)
        urls = self.validators.release_urls.validate(urls)

        keys = set([
            "filename", "filesize", "python_version", "type", "comment",
            "md5_digest", "url", "created",
        ])

        for url in urls:
            url = filter_dict(url)

            # Rename size to filesize
            url["filesize"] = url["size"]

            # Rename packagetype to type
            url["type"] = url["packagetype"]

            # Rename upload_time to created
            url["created"] = url["upload_time"]

            # Rename comment_text to comment
            if "comment_text" in url:
                url["comment"] = url["comment_text"]

            yield dict(x for x in url.items() if x[0] in keys)

    def release(self, project, version):
        """
        Takes a project and version and it returns the normalized data for the
        release of project with that version.
        """
        logger.debug(
            "Fetching release data for '%s' version '%s' from pypi.python.org",
            project,
            version,
        )

        data = self.client.release_data(project, version)
        data = filter_dict(data, required=set(["name", "version"]))
        data = self.validators.release_data.validate(data)

        # fix classifiers (dedupe + sort)
        data["classifiers"] = list(set(data.get("classifiers", [])))
        data["classifiers"].sort()

        # rename download_url to download_uri
        if "download_url" in data:
            data["download_uri"] = data["download_url"]

        # Rename current requires/obsoletes/provides
        if "requires" in data:
            data["requires_old"] = data["requires"]
            del data["requires"]

        if "provides" in data:
            data["provides_old"] = data["provides"]
            del data["provides"]

        if "obsoletes" in data:
            data["obsoletes_old"] = data["obsoletes"]
            del data["obsoletes"]

        # Rename the *_dist to be requires/obsoletes/provides
        if "requires_dist" in data:
            data["requires"] = data["requires_dist"]

        if "provides_dist" in data:
            data["provides"] = data["provides_dist"]

        if "obsoletes_dist" in data:
            data["obsoletes"] = data["obsoletes_dist"]

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
            "requires_python", "requires_external", "requires", "provides",
            "obsoletes", "requires_old", "provides_old", "obsoletes_od",
            "uris", "keywords", "download_uri", "classifiers",
        ])

        return dict(x for x in data.items() if x[0] in keys)

    def versions(self, project):
        """
        Returns a list of all the versions for a particular project.
        """
        logger.debug(
            "Fetching versions for '%s' from pypi.python.org",
            project,
        )

        versions = self.client.package_releases(project, True)
        return self.validators.package_releases.validate(versions)

    def projects(self, since=None):
        """
        Returns a list of all project names
        """
        if since is None:
            logger.debug("Fetching all projects from pypi.python.org")
            packages = self.client.list_packages()
            return set(self.validators.list_packages.validate(packages))
        else:
            since = since - 1

            logger.debug(
                "Fetching all changes since %s from pypi.python.org",
                since,
            )

            changes = self.client.changelog(since)
            changes = self.validators.changelog.validate(changes)

            updated = set()

            for name, version, _timestamp, action in changes:
                if not (action.lower() == "remove" and version is None):
                    updated.add(name)

            return updated

    def deletions(self, since=None):
        if since is None:
            # With no point of reference we must assume there has been
            #   deletions
            logger.debug(
                "Assuming there have been deletions since there is no point "
                "of reference"
            )
            return True
        else:
            since = since - 1
            changes = self.client.changelog(since)
            changes = self.validators.changelog.validate(changes)

            for _name, version, _timestamp, action in changes:
                if action.lower() == "remove" and version is None:
                    # If we find *any* project deletions we know there was
                    #   at least one and can say True
                    logger.debug(
                        "Found deletions that have occurred since %s",
                        since,
                    )
                    return True

            logger.debug(
                "Found no deletions that have occurred since %s",
                since,
            )

            # We've found no deletions, so False
            return False

    def current(self):
        logger.debug("Fetching the current time from pypi.python.org")
        current_string = self.session.get("https://pypi.python.org/daytime")
        current = datetime.datetime.strptime(
                        current_string.text.strip(),
                        "%Y%m%dT%H:%M:%S"
                    )
        return int(calendar.timegm(current.timetuple()))
