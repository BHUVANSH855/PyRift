"""
pyrift.analysis.scope
~~~~~~~~~~~~~~~~~~~~~
Lightweight scope utilities for pyrift rules.

Answers:
  - Is this code at module level?
  - Is this code inside a class?
  - Is this code inside a function?
"""
from __future__ import annotations

import ast
from typing import cast


def is_module_level(node: ast.AST,
                    parent_map: dict[int, ast.AST]) -> bool:
    """True if node is a direct child of the module body."""
    parent = parent_map.get(id(node))
    return isinstance(parent, ast.Module)


def is_inside_class(
    node: ast.AST,
    parent_map: dict[int, ast.AST],
) -> bool:
    """True if node is inside a ClassDef."""
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return True
        current = parent_map.get(id(current))
    return False


def is_inside_function(node: ast.AST,
                        parent_map: dict[int, ast.AST]) -> bool:
    """True if node is inside a FunctionDef or AsyncFunctionDef."""
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        current = parent_map.get(id(current))
    return False


def build_parent_map(node: ast.AST) -> dict[int, ast.AST]:
    """Build a child→parent mapping for the entire AST."""
    parent_map: dict[int, ast.AST] = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parent_map[id(child)] = parent
    return parent_map

def is_version_guarded(node: ast.AST,
                        parent_map: dict[int, ast.AST],
                        min_version: tuple[int, ...]) -> bool:
    """Return True if node is inside an `if sys.version_info >= (x, y)` block.

    This suppresses false positives when code is properly guarded:
        if sys.version_info >= (3, 11):
            from typing import Self  # correctly guarded
    """
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, ast.If):
            test = current.test
            # Pattern: sys.version_info >= (x, y)
            if (
                isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], (ast.GtE, ast.Gt))
                and isinstance(test.left, ast.Attribute)
                and test.left.attr == "version_info"
                and isinstance(test.left.value, ast.Name)
                and test.left.value.id == "sys"
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Tuple)
            ):
                # Extract the version tuple.
                elts = test.comparators[0].elts
                if all(
                    isinstance(e, ast.Constant) and isinstance(e.value, int)
                    for e in elts
                ):
                    guard_version = tuple(
                        cast(ast.Constant, e).value for e in elts
                    )
                    if guard_version >= min_version:
                        return True
        current = parent_map.get(id(current))
    return False