import asyncio
import datetime
import json
import locale
import multiprocessing
import pickle
import sys
from pathlib import PurePath


def _bool_inversion_probe():
    """CPY022 - bitwise inversion on bool emits DeprecationWarning (3.12+)."""
    import warnings

    def invert_flag(flag):
        # Do not constant-fold: pass through a function so the interpreter
        # evaluates ~ on a runtime bool rather than folding a literal.
        return ~flag

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            _ = invert_flag(True)
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"
        return [type(w.message).__name__ for w in caught]


def _get_event_loop_probe():
    """CPY038 - asyncio.get_event_loop() may warn/raise on 3.12+."""
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            asyncio.get_event_loop()
            return {
                "raised": None,
                "warnings": [type(w.message).__name__ for w in caught],
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "raised": type(exc).__name__,
                "warnings": [type(w.message).__name__ for w in caught],
            }


def run_probe():
    results = {
        "python": sys.version,
        "version_info": list(sys.version_info[:3]),
    }

    # CPY023 - multiprocessing default
    try:
        results["multiprocessing_start_method"] = (
            multiprocessing.get_start_method()
        )
    except Exception as exc:
        results["multiprocessing_start_method"] = (
            f"{type(exc).__name__}: {exc}"
        )

    # CPY027 - locale.resetlocale()
    try:
        locale.resetlocale()
        results["locale_resetlocale"] = "available"
    except Exception as exc:
        results["locale_resetlocale"] = (
            f"{type(exc).__name__}: {exc}"
        )

    # CPY036 - datetime.utcnow()
    try:
        with __import__("warnings").catch_warnings(record=True) as warnings:
            __import__("warnings").simplefilter("always")
            value = datetime.datetime.utcnow()
            results["datetime_utcnow"] = {
                "result": type(value).__name__,
                "warnings": [type(w.message).__name__ for w in warnings],
            }
    except Exception as exc:
        results["datetime_utcnow"] = (
            f"{type(exc).__name__}: {exc}"
        )

    # CPY050 - PurePath.is_reserved()
    try:
        results["purepath_is_reserved"] = PurePath("x").is_reserved()
    except Exception as exc:
        results["purepath_is_reserved"] = (
            f"{type(exc).__name__}: {exc}"
        )

    # CPY057 - pickle default protocol
    try:
        results["pickle_default_protocol"] = pickle.DEFAULT_PROTOCOL
    except Exception as exc:
        results["pickle_default_protocol"] = (
            f"{type(exc).__name__}: {exc}"
        )

# CPY029 - locals() mutation behavior
    def locals_probe():
        value = 0
        locals()["value"] = 1
        return value

    try:
        results["locals_mutation"] = locals_probe()
    except Exception as exc:
        results["locals_mutation"] = (
            f"{type(exc).__name__}: {exc}"
        )

    # CPY022 - bool bitwise inversion deprecation (3.12+)
    results["bool_inversion"] = _bool_inversion_probe()

    # CPY038 - asyncio.get_event_loop() behaviour (3.12+)
    results["asyncio_get_event_loop"] = _get_event_loop_probe()

    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    run_probe()
