import os

from .base import *

if "WAREHOUSE_CONF" in os.environ:
    import imp

    mod = imp.new_module("config")
    mod.__file__ = os.environ["WAREHOUSE_CONF"]

    try:
        execfile(os.environ["WAREHOUSE_CONF"], mod.__dict__)
    except IOError, e:
        e.strerror = "Unable to load configuration file (%s)" % e.strerror
        raise

    extras = {}

    for setting in dir(mod):
        if setting == setting.upper():
            setting_value = getattr(mod, setting)

            if setting in ("INSTALLED_APPS", "TEMPLATE_DIRS") and type(setting_value) == str:
                setting_value = (setting_value,)  # In case the user forgot the comma.

            # Any setting that starts with EXTRA_ and matches a setting that is a list or tuple
            # will automatically append the values to the current setting.
            # It might make sense to make this less magical
            if setting.startswith("EXTRA_"):
                base_setting = setting.split("EXTRA_", 1)[-1]
                if isinstance(globals().get(base_setting), (list, tuple)):
                    extras[base_setting] = setting_value
                    continue

            globals()[setting] = setting_value

    for key, value in extras.iteritems():
        curval = globals()[key]
        globals()[key] = curval + type(curval)(value)
