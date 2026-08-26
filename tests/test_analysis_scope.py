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