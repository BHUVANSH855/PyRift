"""
pyrift.analysis.symbols
~~~~~~~~~~~~~~~~~~~~~~~~
Lightweight, module-level symbol resolution: import aliasing and local
name shadowing.

Why this exists
----------------
The 2026-09 architecture review (points 7-8, 126-134) identified that
PyRift's next major false-positive/false-negative frontier is *symbol
resolution*: rules that match `asyncio.get_event_loop()` syntactically
miss `import asyncio as aio; aio.get_event_loop()` (a false negative --
this exact case is recorded as "not detected" in
``benchmark/run_benchmark.py``'s CPY038 golden cases), and rules that
match `open(...)` syntactically can misfire on `open = my_wrapper;
open(...)` (a false positive from shadowing a builtin/import).

This module is intentionally NOT a type checker or full binding graph.
It answers two narrow, static, conservative questions for a single
module:

  1. If I see ``name.attr`` or a bare ``name``, does ``name`` refer to
     something imported (through direct or aliased import)?
  2. Is ``name`` ever *reassigned* elsewhere in the file, such that
     attributing a use of it to the import would be unsafe?

When in doubt (shadowing detected, or resolution is ambiguous), this
module refuses to resolve rather than guessing -- consistent with
PyRift's stated preference for missing a case over reporting a false
positive (see ``pyrift.analysis.guards`` for the same philosophy
applied to version/implementation guards).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class SymbolTable:
    """Resolves a locally-used name back to the module/attribute it was
    imported from, aware of ``import X as Y`` / ``from X import Y as Z``
    aliasing, and conservatively refusing to resolve names that are
    shadowed (reassigned) anywhere else in the module.
    """

    # local name -> canonical dotted module for `import X` / `import X as Y`
    module_aliases: dict[str, str] = field(default_factory=dict)
    # local name -> (module, original_name) for `from X import Y as Z`
    name_aliases: dict[str, tuple[str, str]] = field(default_factory=dict)
    # names that are rebound somewhere else in the module (assignment
    # targets, function/class defs, parameters, for/with targets, ...)
    # other than the import statement itself. Resolution is refused for
    # these to avoid misattributing a call made through the shadowed
    # name to the original import.
    shadowed: set[str] = field(default_factory=set)

    def resolve_attribute(self, node: ast.Attribute) -> tuple[str, str] | None:
        """If *node* is ``<name>.<attr>`` where ``<name>`` resolves
        (through import aliasing) to a known module and isn't shadowed,
        return ``(canonical_module, attr)``. Otherwise ``None``.
        """
        if not isinstance(node.value, ast.Name):
            return None
        name = node.value.id
        if name in self.shadowed:
            return None
        module = self.module_aliases.get(name)
        if module is None:
            return None
        return module, node.attr

    def resolve_name(self, node: ast.Name) -> tuple[str, str] | None:
        """If *node* is a bare name that resolves (through
        ``from X import Y as Z`` aliasing) to a known
        ``(module, original_name)`` and isn't shadowed, return it.
        Otherwise ``None``.
        """
        if node.id in self.shadowed:
            return None
        return self.name_aliases.get(node.id)

    def is_shadowed(self, name: str) -> bool:
        return name in self.shadowed


def _assign_target_names(target: ast.expr) -> list[str]:
    names: list[str] = []
    if isinstance(target, ast.Name):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            names.extend(_assign_target_names(elt))
    elif isinstance(target, ast.Starred):
        names.extend(_assign_target_names(target.value))
    return names


def _arg_names(args: ast.arguments) -> list[str]:
    names = [a.arg for a in getattr(args, "posonlyargs", [])]
    names += [a.arg for a in args.args]
    if args.vararg:
        names.append(args.vararg.arg)
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append(args.kwarg.arg)
    return names


def build_symbol_table(tree: ast.AST) -> SymbolTable:
    """Build a :class:`SymbolTable` for an entire module AST.

    Deliberately module-level and flow-insensitive: it does not try to
    determine whether a rebinding happens *before* or *after* a
    particular use, or whether it's in a different function scope. If a
    name is ever rebound anywhere in the file, every use of that name is
    treated as unresolved. This trades some recall for the same
    conservative-by-default posture the rest of PyRift's analysis layer
    uses (see module docstring).
    """
    table = SymbolTable()
    import_bound_names: set[str] = set()

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                local = alias.asname or alias.name.split(".")[0]
                # A bare `import a.b.c` binds the top-level name `a`,
                # not the full dotted path -- only record a resolvable
                # alias for the (common) case that matters for
                # attribute-call resolution: `import x` / `import x as y`.
                if alias.asname or "." not in alias.name:
                    table.module_aliases[local] = alias.name
                import_bound_names.add(local)
        elif isinstance(n, ast.ImportFrom) and n.module:
            for alias in n.names:
                local = alias.asname or alias.name
                table.name_aliases[local] = (n.module, alias.name)
                import_bound_names.add(local)

    if not import_bound_names:
        return table

    for n in ast.walk(tree):
        target_names: list[str] = []

        if isinstance(n, ast.Assign):
            for t in n.targets:
                target_names.extend(_assign_target_names(t))
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.target is not None or isinstance(n, (ast.For, ast.AsyncFor)):
            target_names.extend(_assign_target_names(n.target))
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for item in n.items:
                if item.optional_vars is not None:
                    target_names.extend(_assign_target_names(item.optional_vars))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            target_names.append(n.name)
            target_names.extend(_arg_names(n.args))
        elif isinstance(n, ast.ClassDef):
            target_names.append(n.name)
        elif isinstance(n, ast.Lambda):
            target_names.extend(_arg_names(n.args))
        elif isinstance(n, ast.NamedExpr):
            target_names.extend(_assign_target_names(n.target))
        elif isinstance(n, ast.ExceptHandler) and n.name:
            target_names.append(n.name)

        for name in target_names:
            if name in import_bound_names:
                table.shadowed.add(name)

    return table
