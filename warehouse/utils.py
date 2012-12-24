from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import platform
import sys
import time

import flask

import warehouse


def user_agent():
    # A lot of the things checked here are platform specific and don't exist
    #   on CPython.
    # pylint: disable=E1101
    _implementation = platform.python_implementation()

    if _implementation == "CPython":
        _implementation_version = platform.python_version()
    elif _implementation == "PyPy":
        _implementation_version = "%s.%s.%s" % (
                                                sys.pypy_version_info.major,
                                                sys.pypy_version_info.minor,
                                                sys.pypy_version_info.micro
                                            )
        if sys.pypy_version_info.releaselevel != "final":
            _pypy_versions = [
                _implementation_version,
                sys.pypy_version_info.releaselevel,
            ]
            _implementation_version = "".join(_pypy_versions)
    elif _implementation == "Jython":
        _implementation_version = platform.python_version()  # Complete Guess
    elif _implementation == "IronPython":
        _implementation_version = platform.python_version()  # Complete Guess
    else:
        _implementation_version = "Unknown"

    return " ".join([
            "warehouse/%s" % warehouse.__version__,
            "%s/%s" % (_implementation, _implementation_version),
            "%s/%s" % (platform.system(), platform.release()),
        ])


def repeat_every(seconds=0, minutes=0, hours=0, initial=False, times=None):
    ran = 0
    seconds = seconds + (minutes * 60) + (hours * 60 * 60)

    if not initial and (times is None or times > 0):
        if not times is None:
            ran += 1
        yield 0

    while times is None or times > ran:
        if not times is None:
            ran += 1
        time.sleep(seconds)
        yield seconds


def ropen(path, mode="r"):
    """
    Redirects the open() call depending on the configured storage.
    """
    app = flask.current_app

    if app.config["STORAGE"].lower() == "filesystem":
        real_path = os.path.join(app.config["STORAGE_DIRECTORY"], path)

        # TODO(dstufft): Detect suspicious paths

        try:
            os.makedirs(os.path.dirname(real_path))
        except OSError:
            # TODO(dstufft): Filter this down to only EEXISTS
            pass

        return open(real_path, mode)
    elif app.config["STORAGE"].lower() == "s3":
        from s3file import s3open

        # Generate the url
        fmt = {"bucket": app.config["STORAGE_BUCKET"], "filename": path}
        url = "http://{bucket}.s3.amazonaws.com/{filename}".format(**fmt)

        return s3open(url,
                    key=app.config["S3_KEY"],
                    secret=app.config["S3_SECRET"],
                    create=False,
                )
    else:
        raise ValueError(
            "Unsupported 'STORAGE' option '{}'".format(app.config["STORAGE"]))
