#!/usr/bin/env python
import os
import sys


def main():
    # @@@ Why is this required?
    sys.path = [""] + sys.path

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse.settings.base")
    os.environ.setdefault("DJANGO_CONFIGURATION", "WarehouseSettings")

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
