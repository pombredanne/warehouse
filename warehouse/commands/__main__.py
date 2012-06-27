import importlib
import os.path
import pkgutil

import warehouse.commands


def main():
    pkgpath = os.path.dirname(warehouse.commands.__file__)
    packages = [name for _, name, _ in pkgutil.iter_modules([pkgpath]) if name not in ["__main__"]]

    for package in packages:
        importlib.import_module("warehouse.commands.{command}".format(command=package))

    warehouse.commands.manager.run()


if __name__ == "__main__":
    main()
