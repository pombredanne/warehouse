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
from warehouse.utils import ropen


def classifier(trove):
    # This method is so short that we don't really care about the bad name "c"
    # pylint: disable=c0103
    try:
        c = Classifier.query.filter_by(trove=trove).one()
    except NoResultFound:
        c = Classifier(trove)
        db.session.add(c)

    return c


def project(name):
    try:
        proj = Project.query.filter_by(name=name).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if proj.yanked:
            db.session.delete(proj)
            db.session.flush()
            proj = None
    except NoResultFound:
        proj = None

    if proj is None:
        proj = Project(name)

    # Explicitly set yanked to False. If somehow we are un-yanking instead of
    #   creating a new object the Database will cause an error.
    proj.yanked = False

    db.session.add(proj)

    return proj


def version(proj, release):
    try:
        vers = Version.query.filter_by(project=proj,
                                          version=release["version"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if vers.yanked:
            db.session.delete(vers)
            db.session.flush()
            vers = None
    except NoResultFound:
        vers = None

    if vers is None:
        vers = Version(project=proj, version=release["version"])

    # Explicitly set yanked to False. If somehow we are un-yanking instead of
    #   creating a new object the Database will cause an error.
    vers.yanked = False

    vers.summary = release.get("summary", "")
    vers.description = release.get("description", "")

    vers.author = release.get("author", "")
    vers.author_email = release.get("author_email", "")

    vers.maintainer = release.get("maintainer", "")
    vers.maintainer_email = release.get("maintainer_email", "")

    vers.license = release.get("license", "")

    vers.requires_python = release.get("requires_python", "")
    vers.requires_external = release.get("requires_external", [])

    # We cannot use the association proxy here because of a bug, and because
    #   of a race condition in multiple green threads.
    #   See: https://github.com/mitsuhiko/flask-sqlalchemy/issues/112
    # It's fine to use _classifiers here, the association_proxy isn't useful
    #   in this use.
    # pylint: disable=W0212
    vers._classifiers = [Classifier.query.filter_by(trove=t).one()
                                for t in release.get("classifiers", [])]

    vers.keywords = release.get("keywords", [])

    vers.uris = release.get("uris", {})

    vers.download_uri = release.get("download_uri", "")

    db.session.add(vers)

    return vers


def distribution(vers, dist):
    try:
        vfile = File.query.filter_by(version=vers,
                                     filename=dist["filename"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if vfile.yanked:
            db.session.delete(vfile)
            db.session.flush()
            vfile = None
    except NoResultFound:
        vfile = None

    if vfile is None:
        vfile = File(version=vers, filename=dist["filename"])

    # Explicitly set yanked to False. If somehow we are un-yanking instead of
    #   creating a new object the Database will cause an error.
    vfile.yanked = False

    vfile.filesize = dist["filesize"]
    vfile.python_version = dist["python_version"]

    vfile.type = FileType.from_string(dist["type"])

    vfile.comment = dist.get("comment", "")

    db.session.add(vfile)

    return vfile


def distribution_file(dist, dist_file):
    app = flask.current_app

    # Generate all the hashes for this file
    hashes = {}
    for algorithm in hashlib.algorithms:
        hashes[algorithm] = getattr(hashlib, algorithm)(dist_file).hexdigest()

    parts = []
    # If we have a hash selected include it in the filename parts
    if app.config.get("STORAGE_HASH"):
        parts += list(hashes[app.config["STORAGE_HASH"]][:5])
        parts += [hashes[app.config["STORAGE_HASH"]]]
    # Finally end the filename parts with the actual filename
    parts += [dist.filename]

    # Join together the parts to get the final filename
    filename = os.path.join(*parts)

    # Open the file with the redirected open (ropen) and save the contents
    with ropen(filename, "w") as fp:
        fp.write(dist_file)

    # Set the hashes and filename for the distribution
    dist.hashes = hashes
    dist.file = filename
