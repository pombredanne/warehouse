#!/usr/bin/env python
import sys


def main():
    # @@@ Why is this required?
    sys.path = [""] + sys.path

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
