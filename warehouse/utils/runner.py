#!/usr/bin/env python
import os
import sys

from configurations.management import execute_from_command_line


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse.settings.base")
    os.environ.setdefault("DJANGO_CONFIGURATION", "WarehouseSettings")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
