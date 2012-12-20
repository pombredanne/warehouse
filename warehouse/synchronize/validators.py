# Even though a lot of these names are "invalid" we do not want them to
#   appear to be constants, but act more like functions.
# pylint: disable=C0103
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from schema import Schema, And, Optional, Use


__all__ = ["list_packages", "package_releases", "release_data"]


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


list_packages = Schema([And(basestring, len)])


package_releases = Schema([And(basestring, len)])


release_data = Schema({
    # PyPI  values
    "_pypi_hidden": bool,
    "package_url": basestring,  # TODO: Validate URI
    "release_url": basestring,  # TODO: Validate URI
    Optional("_pypi_ordering"): And(int, lambda x: x > 0),
    Optional("cheesecake_code_kwalitee_id"): And(int, lambda x: x > 0),
    Optional("cheesecake_documentation_id"): And(int, lambda x: x > 0),
    Optional("cheesecake_installability_id"): And(int, lambda x: x > 0),
    Optional("docs_url"): basestring,  # TODO: Validate URI

    # Meta-data values
    "name": basestring,  # TODO: Can we do any sort of validation?
    "version": basestring,  # TODO: Any sort of validation?
    Optional("author"): basestring,  # TODO: Can we do any sort of validation?
    Optional("author_email"): basestring,  # TODO: Validate email address
    Optional("bugtrack_url"): basestring,  # TODO: Validate URL
    Optional("classifiers"): [basestring],  # TODO: Validate valid classifiers?
    Optional("description"): basestring,  # TODO: Validate valid description?
    Optional("download_url"): basestring,  # TODO: Validate URI
    Optional("home_page"): basestring,  # TODO: Validate URI
    Optional("keywords"): And(Use(_string2list), [basestring]),
    Optional("license"): basestring,
    Optional("maintainer"): basestring,  # Can we do any sort of validation?
    Optional("maintainer_email"): basestring,  # TODO Validate Email
    Optional("obsoletes"): [basestring],  # TODO: What do these look like?
    Optional("obsoletes_dist"): [basestring],  # TODO: What do these look like?
    Optional("platform"): basestring,  # TODO: What do these look like?
    Optional("project_url"): And(Use(_list2dict), {basestring: basestring}),
    Optional("provides"): [basestring],  # TODO: Is this right?
    Optional("provides_dist"): [basestring],  # TODO: Is this right?
    Optional("requires"): [basestring],  # TODO: What does this look like?
    Optional("requires_dist"): [basestring],  # TODO: What does this look like?
    Optional("requires_external"): [basestring],
    Optional("requires_python"): basestring,  # TODO: What does this look like?
    Optional("summary"):  basestring,  # TODO: Any sort of validation?
})


release_urls = Schema([{
    "has_sig": bool,
    "upload_time": datetime.datetime,  # TODO: Validate Oldest
    "python_version": basestring,  # TODO: Validate expected
    "url": basestring,  # TODO: Validate URI
    "md5_digest": basestring,  # TODO: Validate looks like an md5
    "downloads": And(int, lambda x: x >= 0),
    "filename": basestring,
    "packagetype": basestring,  # TODO: Validate expected
    "size": And(int, lambda x: x >= 0),
    Optional("comment_text"): basestring,
}])
