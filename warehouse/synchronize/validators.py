# Even though a lot of these names are "invalid" we do not want them to
#   appear to be constants, but act more like functions.
# pylint: disable=C0103
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

import markerlib

from schema import Schema, And, Optional, Use, Or

from warehouse.utils import version


__all__ = [
    "list_packages", "package_releases", "release_data", "release_urls",
    "changelog",
]


_dist_file_types = set([
    "sdist",
    "bdist_dumb",
    "bdist_rpm",
    "bdist_wininst",
    "bdist_msi",
    "bdist_egg",
    "bdist_dmg",
    "bdist_wheel",
])


def _string2list(s):
    if not isinstance(s, basestring):
        return s

    if "," in s:
        split = s.split(",")
    else:
        split = s.split()

    return [x.strip() for x in split]


def _list2dict(l):
    d = {}
    for item in l:
        key, value = item.split(",", 1)
        key, value = key.strip(), value.strip()

        d[key] = value

    return d


def _pyversion(ver):
    if ver.lower() in set(["any", "source"]):
        return True
    elif ver.split(".", 1)[0] in ["2", "3"] and int(ver.split(".", 1)[1]) >= 0:
        return True

    return False


def _pred_validate(pred):
    if not ";" in pred:
        version.VersionPredicate(pred)
        return True

    pred, marker = [x.strip() for x in pred.split(";", 1)]
    version.VersionPredicate(pred)

    markerlib.interpret(marker)

    return True


_no_slashes = Schema(lambda x: not "/" in x, error="Cannot contain a '/'")


_classifiers = Schema(
        lambda x: len(x.split("::")) > 1,
        error="Must be a valid classifier",
    )


_md5 = Schema(And(
            lambda x: not set(c.lower() for c in x) - set("0123456789abcdef"),
            lambda x: len(x) == 32,
        ),
        error="Must be a valid MD5 hash",
    )


_package_type = Schema(lambda x: x in _dist_file_types,
                    error="Invalid type of package",
                )


_python_version = Schema(_pyversion, error="Invalid python version")


_requires_python = Schema(
        lambda x: version.VersionPredicate("python (%s)" % x),
        error="Invalid requires_python,"
    )


_version_predicate = Schema(_pred_validate, error="Invalid version predicate")


_name = And(basestring, len, _no_slashes)


_version = And(basestring, len)


_action = Schema(And(basestring, len, Or(
        "new release",
        "remove",
        "create",
        "docupdate",
        "update",
        lambda x: bool(
                    x.split(" ", 1)[0] == "update" and
                    [y.strip() for y in x.split(" ", 1)[1].split(",") if y],
                ),
        lambda x: len(x.split(" ", 2)) == 3 and x.startswith("add Owner"),
        lambda x: len(x.split(" ", 2)) == 3 and x.startswith("add Maintainer"),
        lambda x: len(x.split(" ", 2)) == 3 and x.startswith("remove Owner"),
        lambda x: (len(x.split(" ", 2)) == 3
                                        and x.startswith("remove Maintainer")),
        lambda x: x.startswith("rename from") and len(x.split()),
        Schema(And(
            Use(lambda x: x.split()),
            lambda x: x[0] == "add",
            lambda x: _python_version.validate(x[1]),
            lambda x: x[2] == "file",
            lambda x: bool(x[3]),
        )),
        Schema(And(
            Use(lambda x: x.split()),
            lambda x: x[0] == "remove",
            lambda x: x[1] == "file",
            lambda x: bool(x[2]),
        )),
    )),
)


list_packages = Schema([And(basestring, len, _no_slashes)])


package_releases = Schema([And(basestring, len)])


release_data = Schema({
    # PyPI  values
    "_pypi_hidden": bool,
    "package_url": basestring,
    "release_url": basestring,
    Optional("_pypi_ordering"): And(int, lambda x: x > 0),
    Optional("cheesecake_code_kwalitee_id"): And(int, lambda x: x > 0),
    Optional("cheesecake_documentation_id"): And(int, lambda x: x > 0),
    Optional("cheesecake_installability_id"): And(int, lambda x: x > 0),
    Optional("docs_url"): basestring,

    # Meta-data values
    "name": _name,
    "version": _version,
    Optional("author"): basestring,
    Optional("author_email"): basestring,
    Optional("bugtrack_url"): basestring,
    Optional("classifiers"): [And(basestring, _classifiers)],
    Optional("description"): basestring,
    Optional("download_url"): basestring,
    Optional("home_page"): basestring,
    Optional("keywords"): And(Use(_string2list), [basestring]),
    Optional("license"): basestring,
    Optional("maintainer"): basestring,
    Optional("maintainer_email"): basestring,
    Optional("obsoletes"): [basestring],
    Optional("obsoletes_dist"): [And(basestring, _version_predicate)],
    Optional("platform"): basestring,
    Optional("project_url"): And(Use(_list2dict), {
            And(basestring, lambda x: len(x) <= 32): basestring,
        }),
    Optional("provides"): [basestring],
    Optional("provides_dist"): [And(basestring, _version_predicate)],
    Optional("requires"): [basestring],
    Optional("requires_dist"): [And(basestring, _version_predicate)],
    Optional("requires_external"): [basestring],
    Optional("requires_python"): _requires_python,
    Optional("summary"): basestring,
})


release_urls = Schema([{
    "has_sig": bool,
    "upload_time": datetime.datetime,
    "python_version": And(basestring, _python_version),
    "url": basestring,
    "md5_digest": And(basestring, _md5),
    "downloads": And(int, lambda x: x >= 0),
    "filename": basestring,
    "packagetype": And(basestring, _package_type),
    "size": And(int, lambda x: x >= 0),
    Optional("comment_text"): basestring,
}])


changelog = Schema([
    lambda x: (
        _name.validate(x[0]),
        Or(_version, None).validate(x[1]),
        And(int, lambda y: y > 0).validate(x[2]),
        _action.validate(x[3])
    ),
])
