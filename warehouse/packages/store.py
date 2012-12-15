from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import os

import flask

from sqlalchemy.orm.exc import NoResultFound

from warehouse import db
from warehouse.packages.models import (
                                    Classifier,
                                    Project,
                                    Version,
                                    File,
                                    FileType,
                                )


def classifier(trove):
    try:
        c = Classifier.query.filter_by(trove=trove).one()
    except NoResultFound:
        c = Classifier(trove)
        db.session.add(c)

    return c


def project(name):
    try:
        project = Project.query.filter_by(name=name).one()
    except NoResultFound:
        project = Project(name)
        db.session.add(project)

    return project


def version(project, release):
    try:
        version = Version.query.filter_by(project=project,
                                          version=release["version"]).one()
    except NoResultFound:
        version = Version(project=project, version=release["version"])

    version.summary = release.get("summary", "")
    version.description = release.get("description", "")

    version.author = release.get("author", "")
    version.author_email = release.get("author_email", "")

    version.maintainer = release.get("maintainer", "")
    version.maintainer_email = release.get("maintainer_email", "")

    version.license = release.get("license", "")

    version.requires_python = release.get("requires_python", "")
    version.requires_external = release.get("requires_external", [])

    # We cannot use the association proxy here because of a bug, and because
    #   of a race condition in multiple green threads.
    #   See: https://github.com/mitsuhiko/flask-sqlalchemy/issues/112
    version._classifiers = [Classifier.query.filter_by(trove=t).one()
                                for t in release.get("classifiers", [])]

    version.keywords = release.get("keywords", [])

    version.uris = release.get("uris", {})

    version.download_uri = release.get("download_uri", "")

    db.session.add(version)

    return version


def distribution(project, version, dist):
    try:
        vfile = File.query.filter_by(version=version,
                                     filename=dist["filename"]).one()
    except NoResultFound:
        vfile = File(version=version, filename=dist["filename"])

        vfile.filesize = dist["filesize"]
        vfile.python_version = dist["python_version"]

        vfile.type = FileType.from_string(dist["type"])

        vfile.comment = dist.get("comment", "")

    db.session.add(vfile)

    return vfile


def distribution_file(project, version, distribution, dist_file):
    def _prefix(project, version, distribution, dist_file):
        # Create a Hash based URL prefix
        # TODO(dstufft): Determine which algo to use
        digest = hashlib.md5(dist_file).hexdigest()
        parts = list(digest[:5])
        parts.append(digest)
        return os.path.join(*parts)

    # TODO(dstufft): Don't hard code this, and make it generic file storage
    directory = flask.current_app.config["WAREHOUSE_STORAGE_DIRECTORY"]

    filename = os.path.join(
                directory,
                _prefix(project, version, distribution, dist_file),
                distribution.filename
            )

    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass

    with open(filename, "w") as fp:
        fp.write(dist_file)

    hashes = {}

    for algorithm in hashlib.algorithms:
        hashes[algorithm] = getattr(hashlib, algorithm)(dist_file).hexdigest()

    distribution.hashes = hashes
    distribution.file = filename
