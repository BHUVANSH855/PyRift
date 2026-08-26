"""
pyrift.analysis.imports
~~~~~~~~~~~~~~~~~~~~~~~
Shared import detection utilities used by multiple rules.

Instead of every rule walking the AST and checking isinstance(n, ast.Import),
rules can use these helpers to answer common questions:
  - Is module X imported?
  - Is name Y imported from module X?
  - What alias is module X imported as?
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class ImportInfo:
    """Information about a single import statement."""
    module: str           # e.g. "datetime" or "collections.abc"
    name: str | None      # e.g. "datetime" (from import) or None (bare import)
    alias: str | None     # e.g. "dt" if imported as dt
    line: int
    col: int
    node: ast.AST


@dataclass
class ImportMap:
    """All imports found in an AST node."""
    imports: list[ImportInfo] = field(default_factory=list)

    def has_module(self, module: str) -> bool:
        """True if module (or submodule) is imported."""
        return any(
            i.module == module or i.module.startswith(module + ".")
            for i in self.imports
        )

    def has_name_from(self, module: str, name: str) -> bool:
        """True if 'from module import name' is present."""
        return any(
            i.module == module and i.name == name
            for i in self.imports
        )

    def alias_for(self, module: str) -> str | None:
        """Return the alias for a module import, or the module name itself."""
        for i in self.imports:
            if i.module == module and i.name is None:
                return i.alias or module.split(".")[-1]
        return None

    def by_statement(self, module: str | None = None) -> list[ImportInfo]:
        """Return one ImportInfo per import STATEMENT.

        For 'from tomllib import load, loads' this returns ONE entry,
        not two. Use this when you want to report once per import statement.
        """
        seen: set[int] = set()
        result: list[ImportInfo] = []
        for i in self.imports:
            if module is not None and i.module != module:
                continue
            node_id = id(i.node)
            if node_id not in seen:
                seen.add(node_id)
                result.append(i)
        return result

    def get(self, module: str) -> list[ImportInfo]:
        """Return one ImportInfo per import STATEMENT matching module.

        Deduplicates by (node_id, module) so that:
            from tomllib import load, loads
        produces ONE entry, not two.
        """
        seen: set[tuple[int, str]] = set()
        result: list[ImportInfo] = []
        for i in self.imports:
            if i.module != module:
                continue
            key = (id(i.node), i.module)
            if key not in seen:
                seen.add(key)
                result.append(i)
        return result


def collect_imports(node: ast.AST) -> ImportMap:
    """
    Walk an AST and collect all import statements.

    Returns an ImportMap with all imports found.
    Much faster than each rule re-walking for imports independently.
    """
    imp_map = ImportMap()

    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imp_map.imports.append(ImportInfo(
                    module=alias.name,
                    name=None,
                    alias=alias.asname,
                    line=n.lineno,
                    col=n.col_offset,
                    node=n,
                ))
        elif isinstance(n, ast.ImportFrom) and n.module:
            for alias in n.names:
                imp_map.imports.append(ImportInfo(
                    module=n.module,
                    name=alias.name,
                    alias=alias.asname,
                    line=n.lineno,
                    col=n.col_offset,
                    node=n,
                ))

    return imp_map