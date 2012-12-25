from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from flask.ext.script import InvalidCommand  # pylint: disable=E0611,F0401

from warehouse import script


def main():
    # This is copied over from script.run and modified for Warehouse
    try:
        try:
            command = sys.argv[1]
        except IndexError:
            raise InvalidCommand("Please provide a command:")

        return script.handle("warehouse", command, sys.argv[2:])
    except InvalidCommand as exc:
        print exc
        script.print_usage()

    return 1


if __name__ == "__main__":
    sys.exit(main())
