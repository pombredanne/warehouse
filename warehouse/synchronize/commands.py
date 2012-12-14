from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet
import flask
import requests
import xmlrpc2.client

from progress.bar import ShadyBar
from sqlalchemy.orm.exc import NoResultFound

from warehouse import create_app, db, script
from warehouse.packages import store
from warehouse.packages.models import Project, Version, FileType, File
from warehouse.synchronize import validators


eventlet.monkey_patch()


def filter_dict(d, required=None):
    if required is None:
        required = set()

    data = {}
    for key, value in d.items():
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

    def __init__(self):
        # TODO(dstufft): Switch this to using verified SSL
        self.client = xmlrpc2.client.Client("http://pypi.python.org/pypi")

    def file(self, url):
        """
        Fetches the file located at ``url``.
        """
        resp = requests.get(url, prefetch=True)
        return resp.content

    def distributions(self, project, version):
        """
        Takes a project and version and it returns the normalized files for
        the release of project with the given version.
        """
        urls = self.client.release_urls(project, version)

        # TODO(dstufft): Validate incoming data

        keys = {
            "filename", "filesize", "python_version", "type", "comment",
            "md5_digest", "url",
        }

        for url in urls:
            url = filter_dict(url)

            # Rename size to filesize
            url["filesize"] = url["size"]

            # Rename packagetype to type
            url["type"] = url["packagetype"]

            # Rename comment_text to comment
            if "comment_text" in url:
                url["comment"] = url["comment_text"]

            yield {key: value for key, value in url.items() if key in keys}

    def release(self, project, version):
        """
        Takes a project and version and it returns the normalized data for the
        release of project with that version.
        """
        data = self.client.release_data(project, version)
        data = filter_dict(data, required=set(["name", "version"]))
        data = validators.release_data.validate(data)

        # fix classifiers (dedupe + sort)
        data["classifiers"] = list(set(data.get("classifiers", [])))
        data["classifiers"].sort()

        # rename download_url to download_uri
        if "download_url" in data:
            data["download_uri"] = data["download_url"]

        # Collapse project_url, bugtrack_url, and home_page into uris
        data["uris"] = {}

        if "project_url" in data:
            data["uris"].update(data["project_url"])

        if "bugtrack_url" in data:
            data["uris"]["bugtracker"] = data["bugtrack_url"]

        if "home_page" in data:
            data["uris"]["home page"] = data["home_page"]

        # Filter resulting dictionary down to only the required keys
        keys = {
            "name", "version", "summary", "description", "author",
            "author_email", "maintainer", "maintainer_email", "license",
            "requires_python", "requires_external", "uris", "keywords",
            "download_uri",
        }

        return {key: value for key, value in data.items() if key in keys}

    def versions(self, project):
        """
        Returns a list of all the versions for a particular project.
        """
        versions = self.client.package_releases(project, True)
        return validators.package_releases.validate(versions)

    def projects(self):
        """
        Returns a list of all project names
        """
        return validators.list_packages.validate(self.client.list_packages())


def synchronize_project(app, project, fetcher):
    with app.test_request_context():
        project = store.project(project)

        for v in fetcher.versions(project.name):
            version = store.version(project, fetcher.release(project.name, v))

            for dist in fetcher.distributions(project.name, version.version):
                distribution = store.distribution(project, version, dist)

                # Check if the stored hash matches what the fetcher says
                if (distribution.hashes is None or
                        dist["md5_digest"] != distribution.hashes.get("md5")):
                    # The fetcher has a different file
                    # TODO(dstufft): Verify that this url is HTTPS
                    store.distribution_file(project, version, distribution,
                                            fetcher.file(dist["url"]))

        # Commit our changes
        db.session.commit()


def syncer(projects=None, fetcher=None, app=None, pool=None):
    if pool is None:
        pool = eventlet.GreenPool(10)

    if app is None:
        app = create_app()

    if fetcher is None:
        fetcher = PyPIFetcher()

    if projects is None:
        # TODO(dstufft): Determine how to make this do the "since last sync"
        projects = fetcher.projects()

    with app.app_context():
        for project in ShadyBar("Syncing", max=len(projects)).iter(projects):
            pool.spawn_n(synchronize_project, app, project, fetcher)


@script.command
def synchronize():
    syncer()
