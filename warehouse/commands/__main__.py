import importlib
import os.path
import pkgutil

from flaskext.script import Manager

from warehouse.core import app

manager = Manager(app)


def main():
    import warehouse.commands

    pkgpath = os.path.dirname(warehouse.commands.__file__)
    packages = [name for _, name, _ in pkgutil.iter_modules([pkgpath]) if name not in ["__main__"]]

    for package in packages:
        importlib.import_module("warehouse.commands.{command}".format(command=package))

    manager.run()


if __name__ == "__main__":
    main()
