import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
    MultiprocessingForkRule,
)
from pyrift.targets import TargetConfig


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src, target_config=None):
    return rule.check(
        parse(src),
        "<test>",
        target_config,
    )


class TestCPY023:
    """CPY023 was narrowed 2026-09-13 (review point 7): a bare
    `import multiprocessing` is no longer sufficient evidence that a
    program relies on fork semantics. The rule now requires an actual
    start-method-sensitive construct (Process/Pool/get_context without
    an explicit method)."""

    rule = MultiprocessingForkRule()

    def test_bare_import_does_not_trigger(self):
        # Importing the module proves nothing about reliance on the
        # default start method.
        findings = run(self.rule, "import multiprocessing")

        assert findings == []

    def test_detects_process_construction_without_target_platform(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            p = multiprocessing.Process(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"
        assert findings[0].severity == Severity.WARNING

    def test_detects_aliased_multiprocessing_module(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp
            p = mp.Process(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_detects_from_import_process(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process
            p = Process(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_detects_aliased_from_import_process(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process as P
            p = P(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_unknown_attribute_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            foo.Process(target=worker)
            """,
        )

        assert findings == []

    def test_shadowed_module_alias_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker(mp):
                mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_assignment_shadowing_before_call_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                mp = something_else
                mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_shadowed_from_import_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process

            def worker(Process):
                Process(target=target)
            """,
        )

        assert findings == []

    def test_assignment_shadowing_after_call_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                mp.Process(target=target)
                mp = something_else
            """,
        )

        assert findings == []

    def test_nested_function_without_shadowing_uses_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                def worker():
                    mp.Process(target=target)

                worker()
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_nested_function_shadowing_does_not_trigger(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                def worker(mp):
                    mp.Process(target=target)

                worker(something_else)
            """,
        )

        assert findings == []

    def test_class_binding_does_not_shadow_module_alias_inside_method(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            class Worker:
                mp = something_else

                def run(self):
                    mp.Process(target=target)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_nested_function_binding_does_not_shadow_outer_function(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                def inner():
                    mp = something_else

                mp.Process(target=target)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_nested_class_binding_does_not_shadow_outer_function(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                class Inner:
                    mp = something_else

                mp.Process(target=target)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_global_declaration_uses_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                global mp
                mp.Process(target=target)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_nonlocal_declaration_preserves_outer_binding(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                def worker():
                    nonlocal mp
                    mp.Process(target=target)

                worker()
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_for_target_shadows_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                for mp in items:
                    mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_with_target_shadows_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                with something() as mp:
                    mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_except_target_shadows_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                try:
                    something()
                except Exception as mp:
                    mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_del_binding_shadows_module_alias(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker():
                del mp
                mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_detects_pool_construction(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            with multiprocessing.Pool() as pool:
                pool.map(worker, items)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_does_not_flag_windows_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="windows"),
        )

        assert findings == []

    def test_does_not_flag_win32_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="win32"),
        )

        assert findings == []

    def test_does_not_flag_macos_target(self):
        # macOS has defaulted to 'spawn' since Python 3.8 -- it was
        # never 'fork' to begin with, so the 3.14 change is a no-op
        # there (review point 27).
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="macos"),
        )

        assert findings == []

    def test_does_not_flag_darwin_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="darwin"),
        )

        assert findings == []

    def test_flags_linux_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="linux"),
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_flags_posix_target(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
            TargetConfig(platform="posix"),
        )

        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import threading")

        assert len(findings) == 0

    def test_does_not_flag_explicit_start_method(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            multiprocessing.set_start_method('fork')
            p = multiprocessing.Process(target=worker)
            """,
        )

        assert findings == []

    def test_does_not_flag_explicit_get_context(self):
        findings = run(
            self.rule,
            """
            import multiprocessing
            ctx = multiprocessing.get_context('fork')
            """,
        )

        assert findings == []

    def test_does_not_flag_start_method_set_before_process(self):
        findings = run(
            self.rule,
            """
            import multiprocessing

            multiprocessing.set_start_method("spawn")
            p = multiprocessing.Process(target=worker)
            """,
        )

        assert findings == []

    def test_flags_start_method_set_after_process(self):
        findings = run(
            self.rule,
            """
            import multiprocessing

            p = multiprocessing.Process(target=worker)
            multiprocessing.set_start_method("spawn")
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_does_not_flag_aliased_start_method_set_before_process(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            mp.set_start_method("spawn")
            p = mp.Process(target=worker)
            """,
        )

        assert findings == []

    def test_flags_aliased_start_method_set_after_process(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            p = mp.Process(target=worker)
            mp.set_start_method("spawn")
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_does_not_flag_from_import_start_method_set_before_process(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process, set_start_method

            set_start_method("spawn")
            p = Process(target=worker)
            """,
        )

        assert findings == []

    def test_flags_from_import_start_method_set_after_process(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process, set_start_method

            p = Process(target=worker)
            set_start_method("spawn")
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_conditional_start_method_does_not_suppress(self):
        findings = run(
            self.rule,
            """
            import multiprocessing

            if condition:
                multiprocessing.set_start_method("spawn")

            p = multiprocessing.Process(target=worker)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_conditional_start_method_after_process_still_flags(self):
        findings = run(
            self.rule,
            """
            import multiprocessing

            p = multiprocessing.Process(target=worker)

            if condition:
                multiprocessing.set_start_method("spawn")
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_flags_bare_get_context(self):
        # get_context() with no argument still defaults to the
        # platform default start method.
        findings = run(
            self.rule,
            """
            import multiprocessing
            ctx = multiprocessing.get_context()
            """,
        )

        assert len(findings) == 1

    def test_suggestion_mentions_set_start_method(self):
        findings = run(
            self.rule,
            "import multiprocessing\nmultiprocessing.Process(target=worker)",
        )

        assert (
            "set_start_method" in findings[0].suggestion.lower()
            or "fork" in findings[0].suggestion.lower()
        )

    def test_function_default_expression_uses_enclosing_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker(
                value=mp.Process(target=target),
            ):
                pass
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_function_body_assignment_does_not_change_default_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker(
                value=mp.Process(target=target),
            ):
                mp = something_else
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_function_decorator_expression_uses_enclosing_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            @decorate(mp.Process(target=target))
            def worker():
                pass
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_function_return_annotation_call_uses_enclosing_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker() -> make_type(mp.Process(target=target)):
                pass
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_nested_function_body_uses_nested_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                def worker():
                    mp = something_else
                    mp.Process(target=target)

                worker()
            """,
        )

        assert findings == []

    def test_nested_class_body_does_not_resolve_as_function_scope(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                class Worker:
                    mp = something_else
                    value = mp.Process(target=target)
            """,
        )

        assert findings == []

    def test_method_does_not_inherit_class_binding(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            class Worker:
                mp = something_else

                def run(self):
                    mp.Process(target=target)
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_vararg_and_kwarg_bindings_are_collected(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker(*args: int, **kwargs: int):
                mp = something_else
                mp.Process(target=target)
            """,
        )
        assert findings == []

    def test_nested_function_metadata_is_traversed(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                @decorate(1)
                def inner(
                    value: int = 1,
                    *args: int,
                    **kwargs: int,
                ) -> int:
                    return 1

                mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_async_function_metadata_and_body_are_traversed(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            async def worker(
                value: int = 1,
                *args: int,
                **kwargs: int,
            ) -> int:
                mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_class_binding_collector_handles_exception_and_nested_metadata(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            @decorate(1)
            class Worker(Base, metaclass=Meta):
                try:
                    value = 1
                except Exception as error:
                    value = error

                @decorate(1)
                def method(
                    self,
                    value: int = 1,
                    *args: int,
                    **kwargs: int,
                ) -> int:
                    return 1

                async def async_method(
                    self,
                    value: int = 1,
                    *args: int,
                    **kwargs: int,
                ) -> int:
                    return 1

                class Nested:
                    pass

                value = mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_class_metadata_in_function_scope_is_traversed(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def outer():
                @decorate(1)
                class Worker(Base, metaclass=Meta):
                    value = 1

                mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_function_argument_annotations_are_traversed(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            def worker(
                value: int,
                *args: int,
                **kwargs: int,
            ) -> int:
                mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_async_function_dispatch_is_supported(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            async def worker():
                mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_class_decorator_base_and_keyword_are_traversed(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            @decorate(1)
            class Worker(Base, metaclass=Meta):
                value = mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_risky_class_decorator_short_circuits_class_body(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            @decorate(mp.Process(target=target))
            class Worker:
                value = something_else()
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_from_import_get_context_with_explicit_method_is_safe(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import get_context

            ctx = get_context("spawn")
            ctx.Process(target=target)
            """,
        )
        assert findings == []

    def test_from_import_set_start_method_is_safe(self):
        findings = run(
            self.rule,
            """
            from multiprocessing import Process, set_start_method

            set_start_method("spawn")
            Process(target=target)
            """,
        )
        assert findings == []

    def test_unrelated_set_start_method_does_not_suppress(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            other.set_start_method("spawn")
            mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"

    def test_unrelated_get_context_does_not_suppress(self):
        findings = run(
            self.rule,
            """
            import multiprocessing as mp

            other.get_context("spawn")
            mp.Process(target=target)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY023"
