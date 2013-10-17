from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

import flask

from warehouse.packages.models import Project, Version, File


_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


simple = flask.Blueprint("simple",  # pylint: disable=C0103
            __name__,
            subdomain="api",
            url_prefix="/simple",
            template_folder="templates",
        )

restricted = flask.Blueprint("restricted",  # pylint: disable=C0103
            __name__,
            subdomain="api",
            url_prefix="/restricted",
            template_folder="templates",
        )


@simple.route("/")
@restricted.route("/")
def index():
    projects = Project.query.all()
    return flask.render_template("index.html", projects=projects)


@simple.route("/<project>")
@simple.route("/<project>/")
@simple.route("/<project>/<version>")
@simple.route("/<project>/<version>/")
@restricted.route("/<project>", defaults={"restrict": True})
@restricted.route("/<project>/", defaults={"restrict": True})
@restricted.route("/<project>/<version>", defaults={"restrict": True})
@restricted.route("/<project>/<version>/", defaults={"restrict": True})
def detail(project, version=None, restrict=False):
    normalized = _normalize_regex.sub("-", project).lower()
    project = Project.query.filter_by(normalized=normalized).first_or_404()

    if version is None:
        versions = Version.query.filter_by(project=project, yanked=False).all()
        files = File.query.filter(
                    File.version_id.in_([v.id for v in versions])
                ).filter_by(yanked=False).all()
    else:
        versions = Version.query.filter_by(
                                    project=project, version=version).all()
        files = File.query.filter(
                    File.version_id.in_([v.id for v in versions]),
                ).all()

    return flask.render_template("detail.html",
                project=project,
                versions=versions,
                files=files,
                restricted=restrict,
            )


BLUEPRINTS = [simple, restricted]
