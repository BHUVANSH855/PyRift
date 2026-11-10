"""Convenience re-export of PyRift project-configuration helpers.

The canonical implementation lives in ``pyrift.targets``; this module
re-exports the public API under a stable, purpose-named location so
downstream code and rule authors can import from one place.

Typical usage
-------------
    from pyrift.config import load_pyrift_config

    cfg = load_pyrift_config("/path/to/project")
    if cfg and cfg.fail_on_findings:
        ...

Supported ``[tool.pyrift]`` keys
---------------------------------
    [tool.pyrift]
    # Rule selection (mutually exclusive)
    select = ["CPY055", "CPY022"]   # run only these rules
    ignore = ["CPY001"]             # skip these rules

    # Output
    format = "json"                  # default output format

    # CI behaviour
    fail_on_findings = true          # exit 1 when any finding is produced
    only_documented = true           # filter to documented/deprecated changes

Extended settings (``format``, ``fail_on_findings``, ``only_documented``)
require Python 3.11+ or the ``tomli`` backport; on Python 3.10 without
``tomli``, only ``select``/``ignore`` are read.
"""
from .targets import PyriftConfig, load_pyrift_config

__all__ = ["PyriftConfig", "load_pyrift_config"]
