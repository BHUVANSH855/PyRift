#!/usr/bin/env python3
"""
Rule-robustness fuzz harness.

Generates a broad set of syntactically valid Python snippets across
version-conditional syntax and exotic AST constructs, then runs every
rule against each parse. The harness fails if any rule *crashes* on
valid source (rule_errors), because a crash on valid Python is always
a bug regardless of the finding outcome.

This complements the golden benchmark (precision) and corpus (real
packages) by hammering rules with diverse constructs to flush out
unhandled AST node types.

Run:
    python benchmark/fuzz_harness.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrift import ALL_RULES

# A curated corpus of constructs exercising many AST node kinds:
# comprehensions, generators, match, async, walrus, type aliases,
# exception groups, decorators, annotations, complex subscripts, etc.
SNIPPETS: list[str] = [
    # comprehensions and generators
    "[x for x in range(10) if x % 2]",
    "{k: v for k, v in items}",
    "{x * 2 for x in data}",
    "sum(x * x for x in values)",
    "[(a, b) async for a, b in pairs]",
    "{key: val async for key, val in mapping.items()}",
    # assignment and walrus
    "def f():\n    if (n := len(items)) > 3:\n        return n",
    "total = sum([(s := 0), s])",
    "while (chunk := stream.read()) :\n    process(chunk)",
    # match statement (3.10+)
    "match value:\n    case [x]:\n        pass\n    case {'k': v}:\n        pass\n    case str() | int():\n        pass",
    "match point:\n    case (0, 0):\n        pass\n    case _:\n        pass",
    # async / await
    "async def fetch(url):\n    async with session.get(url) as r:\n        return await r.text()",
    "async def main():\n    await asyncio.gather(*[task(i) for i in range(5)])",
    # generators / yield
    "def gen():\n    yield from source()\n    val = yield 42",
    "def double(n):\n    yield n * 2",
    # decorators
    "@property\ndef name(self):\n    return self._name",
    "@app.route('/x', methods=['GET'])\ndef handler():\n    return jsonify({})",
    "@dataclass\nclass Point:\n    x: int\n    y: int = 0",
    # exceptions
    "def f():\n    try:\n        risky()\n    except (ValueError, TypeError) as exc:\n        raise RuntimeError('bad') from exc\n    finally:\n        cleanup()",
    "try:\n    x = 1\nexcept* ValueError as eg:\n    handle(eg)",
    # with
    "with open('f') as f, open('g', 'w') as g:\n    g.write(f.read())",
    "with contextlib.ExitStack() as stack:\n    f = stack.enter_context(open('x'))",
    # type annotations / modern typing
    "def f(a: list[int], b: dict[str, tuple[int, ...]]) -> set[float]: ...",
    "x: int | None = None",
    "type Alias = list[str]",
    "type Point = tuple[int, int]",
    "def f(arg: Annotated[int, GT(0)]) -> Never: ...",
    "class C(Generic[T]):\n    def m(self, x: T) -> T:\n        return x",
    # lambda / nested
    "apply = lambda x, y=1: x + y if x else y",
    "def outer():\n    def inner():\n        return 1\n    return inner()",
    # dict / set ops
    "merged = a | b",
    "d = {1: 2}\nother = {**base, 'x': 1}",
    "assert x in {1, 2, 3}",
    # subscripts / slices
    "a = matrix[0][1]",
    "b = values[1:10:2]",
    "c = obj[Ellipsis]",
    "d = data['key']",
    "e = items[:]",
    # attributes / star
    "from math import *",
    "import os, sys as system",
    "def f(*args, **kwargs):\n    return args, kwargs",
    "target = (*a, *b)",
    "def f(x, /, y, *, z):\n    return x + y + z",
    # bool / numeric ops
    "result = ~flags",
    "value = 10 ** 3 // 2 % 5",
    "ok = a is None or b is not None",
    # for / while / break / continue
    "for i, item in enumerate(items):\n    if not item:\n        continue\n    if i > 10:\n        break",
    "while True:\n    if done:\n        break",
    "else_clause = 1\nfor x in data:\n    pass\nelse:\n    pass",
    # strings / f-strings
    "s = f'value={x!r:} - {y:>10} - {z!s}'",
    "t = '''multiline\nstring'''",
    "raw = r'\\n'",
    "b = b'bytes'",
    # wants / global / nonlocal
    "count = 0\ndef inc():\n    global count\n    count += 1",
    "def outer():\n    x = 0\n    def inner():\n        nonlocal x\n        x += 1\n    return inner",
    # del / augassign variants
    "del items[0]",
    "x += 1\nx -= 2\nx *= 3\nx <<= 1\nx @= y",
    # class features
    "class Meta(type):\n    pass\nclass C(metaclass=Meta):\n    __slots__ = ('a', 'b')\n    def __init__(self, a):\n        self.a = a",
    "class ReadOnly:\n    __match_args__ = ('x', 'y')\n    @classmethod\n    def create(cls):\n        return cls()",
    "class Base(Exception):\n    pass",
    # await in comprehension and star in call
    "await asyncio.sleep(0)",
    "func(*args, **kwargs)",
]


def run() -> int:
    rules = len(ALL_RULES)
    failures: list[str] = []

    for i, src in enumerate(SNIPPETS, start=1):
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            print(
                f"  [WARN] snippet {i} did not parse on this "
                f"Python: {exc.msg}"
            )
            continue

        for rule in ALL_RULES:
            try:
                # A rule must never crash on valid source.
                rule.check(tree, f"<fuzz-{i}>")
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"  {rule.rule_id} crashed on snippet {i}: "
                    f"{type(exc).__name__}: {exc}"
                )

    print(f"Fuzz harness: {len(SNIPPETS)} snippets x {rules} rules "
          f"({len(SNIPPETS) * rules} executions)")

    if failures:
        print(f"\n{len(failures)} rule crash(es) detected:")
        for line in failures:
            print(line)
        print("\n[FAIL] Fuzz harness failed -- a rule crashed on valid source.")
        return 1

    print("[OK] No rule crashes on any generated construct.")
    return 0


if __name__ == "__main__":
    sys.exit(run())