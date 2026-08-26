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


def is_module_level(node: ast.AST,
                    parent_map: dict[int, ast.AST]) -> bool:
    """True if node is a direct child of the module body."""
    parent = parent_map.get(id(node))
    return isinstance(parent, ast.Module)


def is_inside_class(node: ast.AST,
                    parent_map: dict[int, ast.AST]) -> bool:
    """True if node is inside a ClassDef."""
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return True
        if isinstance(current, ast.FunctionDef):
            break
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