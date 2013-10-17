from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

import flask
import stockpile


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


def get_storage(app=None):
    if app is None:
        app = flask.current_app

    storage_kwargs = app.config.get("STORAGE_OPTIONS", {})
    storage_class = stockpile.get_storage(app.config["STORAGE"])
    storage = storage_class(**storage_kwargs)

    return storage
