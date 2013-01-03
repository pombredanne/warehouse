from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import io

import flask

from sqlalchemy.orm.exc import NoResultFound

from warehouse import db
from warehouse.packages.models import (
                                    Classifier,
                                    Project,
                                    Version,
                                    Requirement,
                                    Provide,
                                    Obsolete,
                                    File,
                                    FileType,
                                )
from warehouse.utils import get_storage
from warehouse.utils.version import VersionPredicate


def _delete(obj):
    db.session.delete(obj)
    db.session.flush()
    obj = None
    return obj


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
            proj = _delete(proj)
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
    def _handle_require(requires, model, approximate=None):
        collected = []

        for req in requires:
            if ";" in req:
                predicate, environment = [x.strip() for x in req.split(";", 1)]
            else:
                predicate, environment = req.strip(), None

            vp = VersionPredicate(predicate)

            name = vp.name
            rversions = ["".join([str(y) for y in x])
                            for x in sorted(vp.predicates, key=lambda z: z[1])]

            kw = {
                "name": name,
                "versions": rversions,
                "environment": environment,
            }

            if approximate is not None:
                kw.update({"approximate": approximate})

            collected += [model(**kw)]

        return collected
    try:
        vers = Version.query.filter_by(project=proj,
                                          version=release["version"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if vers.yanked:
            vers = _delete(vers)
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

    vers.keywords = release.get("keywords", [])

    vers.uris = release.get("uris", {})

    vers.download_uri = release.get("download_uri", "")

    # Process Requirements
    vers.requirements = _handle_require(release.get("requires", []),
                        model=Requirement,
                        approximate=False,
                    )

    # Process Provides
    vers.provides = _handle_require(release.get("provides", []), model=Provide)

    # Process Obsoletes
    vers.obsoletes = _handle_require(release.get("obsoletes", []),
                        model=Obsolete,
                    )

    # We cannot use the association proxy here because of a bug, and because
    #   of a race condition in multiple green threads.
    #   See: https://github.com/mitsuhiko/flask-sqlalchemy/issues/112
    # It's fine to use _classifiers here, the association_proxy isn't useful
    #   in this use.
    # pylint: disable=W0212
    vers._classifiers = [Classifier.query.filter_by(trove=t).one()
                                for t in release.get("classifiers", [])]

    db.session.add(vers)

    return vers


def distribution(vers, dist):
    try:
        vfile = File.query.filter_by(filename=dist["filename"]).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if vfile.yanked:
            vfile = _delete(vfile)
        # We need to check to make sure that the version on the file matches
        #   the one we expect.
        elif vfile.version != vers:
            vfile = _delete(vfile)
    except NoResultFound:
        vfile = None

    if vfile is None:
        vfile = File(version=vers, filename=dist["filename"])

    # Explicitly set yanked to False. If somehow we are un-yanking instead of
    #   creating a new object the Database will cause an error.
    vfile.yanked = False

    vfile.created = dist["created"]

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

    # Save our file
    storage = get_storage(app=app)
    filename = storage.save(dist.filename, io.BytesIO(dist_file))

    # Store our information on the model
    dist.hashes = hashes
    dist.file = filename
