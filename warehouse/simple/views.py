from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

import flask

from warehouse.packages.models import Project


_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")

simple = flask.Blueprint("simple",
            __name__,
            subdomain="api",
            url_prefix="/simple",
            template_folder="templates",
        )

restricted = flask.Blueprint("restricted",
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
@restricted.route("/<project>", defaults={"restricted": True})
@restricted.route("/<project>/", defaults={"restricted": True})
def detail(project, restricted=False):
    normalized = _normalize_regex.sub("-", project).lower()
    project = Project.query.filter_by(normalized=normalized).first_or_404()
    return flask.render_template("detail.html",
                project=project,
                restricted=restricted
            )


BLUEPRINTS = [simple, restricted]
