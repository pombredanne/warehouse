import platform
import sys

import warehouse


def user_agent():
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
