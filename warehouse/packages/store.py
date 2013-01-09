from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import fnmatch
import hashlib
import io
import os
import re
import tarfile
import zipfile

import flask
import pkg_resources

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


_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


def _delete(obj):
    db.session.delete(obj)
    db.session.flush()
    obj = None
    return obj


def _handle_require(requires, model, approximate=None):
    collected = []

    for req in requires:
        if ";" in req:
            predicate, environment = [x.strip() for x in req.split(";", 1)]
        else:
            predicate, environment = req.strip(), None

        vpred = VersionPredicate(predicate)

        name = vpred.name
        rversions = ["".join([str(y) for y in x])
                        for x in sorted(vpred.predicates, key=lambda z: z[1])]

        kwargs = {
            "name": name,
            "versions": rversions,
            "environment": environment,
        }

        if approximate is not None:
            kwargs.update({"approximate": approximate})

        collected += [model(**kwargs)]

    return collected


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
        normalized = _normalize_regex.sub("-", name).lower()
        proj = Project.query.filter_by(normalized=normalized).one()

        # This object already exists, so if yanked is True we need to make it
        #   "new"
        if proj.yanked:
            proj = _delete(proj)
    except NoResultFound:
        proj = None

    if proj is None:
        proj = Project(name)

    # Assert that our project name matches what we expect
    assert proj.name == name

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
    approximate_requirements = [x for x in vers.requirements if x.approximate]

    if approximate_requirements:
        if release.get("requires", []):
            # We have approximate requirements, and hard requirements
            #   we're going to assume the hard requirements overwrite the
            #   approximate
            requirements = []
        else:
            # We have approximate requirements and no hard requirements
            #   we're going to only keep the approximate requirements
            requirements = approximate_requirements
    else:
        # We have no approximate requirements so we can assume we are
        #   overwriting with the current, even if it's empty
        requirements = []

    # Add our current requires to whatever our starting base is
    requirements += _handle_require(release.get("requires", []),
                        model=Requirement,
                        approximate=False,
                    )
    vers.requirements = requirements

    # Process Provides
    vers.provides = _handle_require(release.get("provides", []), model=Provide)

    # Process Obsoletes
    vers.obsoletes = _handle_require(release.get("obsoletes", []),
                        model=Obsolete,
                    )

    # Deprecated requires-like fields, stored only for completeness
    vers.requires_old = release.get("requires_old", [])
    vers.provides_old = release.get("provides_old", [])
    vers.obsoletes_old = release.get("obsoletes_old", [])

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


def setuptools_requires(vers, filename, file_data):
    hard_requirements = [x for x in vers.requirements if not x.approximate]
    if hard_requirements:
        # We have hard requirements, we assume they take precedence over
        #   approximate requirements
        return

    # Determine the type of compression to use
    compression = os.path.splitext(filename)[1][1:]

    # Normalize tgz to just gz
    if compression == "tgz":
        compression = "gz"

    # short circuit on some invalid sdist types that PyPI somehow has
    if compression in set(["rpm", "egg", "deb"]):
        return

    if compression not in set(["gz", "bz2", "zip"]):
        raise ValueError(
                "Invalid compression type %s for %s" % (compression, filename)
            )

    # Shove our file_data into a BytesIO so we can treat it like a file
    archive = io.BytesIO(file_data)

    # Normalize requirements, provides, and obsoletes back to empty
    vers.requirements = []
    vers.provides = []
    vers.obsoletes = []

    # Extract the requires.txt from the file_data
    if compression == "zip":
        try:
            zipf = zipfile.ZipFile(archive)
        except zipfile.BadZipfile:
            # invalid archive
            return

        try:
            files = fnmatch.filter(zipf.namelist(), "*.egg-info/requires.txt")
        except IOError:
            return

        if not files:
            # requires.txt doesn't exist
            return

        # Figure out which requires.txt is closest to the root
        files.sort(key=lambda x: len(x.split("/")))

        # Grab the first requires.txt
        rfilename = files.pop(0)

        # Extract the requires.txt from the zip archive
        requires = zipf.open(rfilename)
    elif compression in set(["gz", "bz2"]):
        try:
            mode = "r:%s" % compression
            tar = tarfile.open(filename, mode=mode, fileobj=archive)
        except tarfile.ReadError:
            # Invalid archive
            return

        try:
            files = fnmatch.filter(tar.getnames(), "*.egg-info/requires.txt")
        except IOError:
            return

        if not files:
            # requires.txt doesn't exist
            return

        # Figure out which requires.txt is closest to the root
        files.sort(key=lambda x: len(x.split("/")))

        # Grab the first requires.txt
        rfilename = files.pop(0)

        # Extract the requires.txt from the tar archive
        requires = tar.extractfile(rfilename)

    for section, reqs in pkg_resources.split_sections(requires):
        for req in pkg_resources.parse_requirements(reqs):
            requirement = Requirement(name=req.project_name, approximate=True)

            # If we have any version modifiers, add them
            if req.specs:
                requirement.versions = ["".join(x) for x in req.specs]

            # If we have any section add is as an extras
            if section is not None:
                requirement.environment = "extra = '%s'" % section

            # Add this Requirement to the version
            vers.requirements.append(requirement)
