import ast
import textwrap

from pyrift.analysis.scope import (
    build_parent_map,
    is_inside_class,
    is_inside_function,
    is_module_level,
    is_version_guarded,
)


def test_build_parent_map():
    tree = ast.parse(
        textwrap.dedent(
            """
            x = 1
            """
        )
    )

    parent_map = build_parent_map(tree)

    assignment = tree.body[0]
    assert parent_map[id(assignment)] is tree


def test_module_level_detection():
    tree = ast.parse(
        textwrap.dedent(
            """
            x = 1

            def func():
                y = 2
            """
        )
    )

    parent_map = build_parent_map(tree)

    module_assignment = tree.body[0]
    function_assignment = tree.body[1].body[0]

    assert is_module_level(
        module_assignment,
        parent_map,
    )

    assert not is_module_level(
        function_assignment,
        parent_map,
    )


def test_inside_function_detection():
    tree = ast.parse(
        textwrap.dedent(
            """
            def func():
                x = 1
            """
        )
    )

    parent_map = build_parent_map(tree)
    assignment = tree.body[0].body[0]

    assert is_inside_function(
        assignment,
        parent_map,
    )


def test_not_inside_function():
    tree = ast.parse(
        textwrap.dedent(
            """
            x = 1
            """
        )
    )

    parent_map = build_parent_map(tree)
    assignment = tree.body[0]

    assert not is_inside_function(
        assignment,
        parent_map,
    )


def test_not_inside_class_but_inside_function():
    tree = ast.parse(
        textwrap.dedent(
            """
            def outer():
                x = 1
            """
        )
    )

    parent_map = build_parent_map(tree)
    assignment = tree.body[0].body[0]

    # inside a function, but not inside any class.
    assert not is_inside_class(
        assignment,
        parent_map,
    )


def test_inside_class_detection():
    tree = ast.parse(
        textwrap.dedent(
            """
            class Example:
                value = 1

                def method(self):
                    return self.value
            """
        )
    )

    parent_map = build_parent_map(tree)

    class_assignment = tree.body[0].body[0]
    return_node = tree.body[0].body[1].body[0]

    assert is_inside_class(
        class_assignment,
        parent_map,
    )

    assert is_inside_class(
        return_node,
        parent_map,
    )


def test_version_guard_detection():
    tree = ast.parse(
        textwrap.dedent(
            """
            import sys

            if sys.version_info >= (3, 11):
                import tomllib
            """
        )
    )

    parent_map = build_parent_map(tree)

    guarded_import = tree.body[1].body[0]

    assert is_version_guarded(
        guarded_import,
        parent_map,
        (3, 11),
    )

    assert not is_version_guarded(
        guarded_import,
        parent_map,
        (3, 12),
    )


def test_inside_class_nested():
    """Node inside a class inside a class is inside a class."""
    tree = ast.parse(
        textwrap.dedent(
            """
            class Outer:
                class Inner:
                    x = 1
            """
        )
    )
    parent_map = build_parent_map(tree)
    inner_assignment = tree.body[0].body[0].body[0]
    assert is_inside_class(inner_assignment, parent_map)


def test_comprehension_scope():
    """Node inside a list comprehension is inside a function (via listcomp)."""
    tree = ast.parse(
        textwrap.dedent(
            """
            result = [x for x in range(10)]
            """
        )
    )
    parent_map = build_parent_map(tree)
    # The comprehension variable x is inside a ListComp node.
    listcomp = tree.body[0].value  # ListComp
    elt = listcomp.elt  # Name('x')
    # ListComp is not a function, but comprehension variables have their own scope.
    assert not is_module_level(elt, parent_map)


def test_walrus_operator():
    """Walrus operator creates a NamedExpr inside an If's test clause."""
    tree = ast.parse(
        textwrap.dedent(
            """
            if (n := 10) > 5:
                x = n
            """
        )
    )
    parent_map = build_parent_map(tree)
    # The If node is at module level.
    if_node = tree.body[0]
    assert is_module_level(if_node, parent_map)
    # The NamedExpr is inside the If's test, not at module level.
    named_expr = if_node.test.left  # Compare -> left is the NamedExpr
    assert not is_module_level(named_expr, parent_map)


def test_inside_async_function():
    """AsyncFunctionDef is detected as inside a function."""
    tree = ast.parse(
        textwrap.dedent(
            """
            async def coro():
                x = 1
            """
        )
    )
    parent_map = build_parent_map(tree)
    assignment = tree.body[0].body[0]
    assert is_inside_function(assignment, parent_map)


def test_nested_function_not_class():
    """Function inside a function is not inside a class."""
    tree = ast.parse(
        textwrap.dedent(
            """
            def outer():
                def inner():
                    x = 1
            """
        )
    )
    parent_map = build_parent_map(tree)
    inner_assignment = tree.body[0].body[0].body[0]
    assert is_inside_function(inner_assignment, parent_map)
    assert not is_inside_class(inner_assignment, parent_map)