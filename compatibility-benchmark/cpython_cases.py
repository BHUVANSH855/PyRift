import datetime
import locale
import multiprocessing
import pickle
from pathlib import PurePath

locale.resetlocale()

datetime.datetime.utcnow()

path = PurePath("x")
path.is_reserved()

multiprocessing.get_start_method()

pickle.DEFAULT_PROTOCOL

def locals_probe():
    value = 0
    locals()["value"] = 1
    return value

_CACHE = {}
_CACHE["x"] = 1
