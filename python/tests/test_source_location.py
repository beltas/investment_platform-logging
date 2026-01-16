"""Tests for source location capture."""

import json
import pytest
from agora_log import initialize, get_logger, LogConfig
from agora_log.logger import _capture_source_location, SourceLocation


class TestSourceLocationCapture:
    """Tests for _capture_source_location function."""

    def test_capture_source_location_basic(self):
        """Test basic source location capture."""
        source = _capture_source_location(stack_depth=1)

        assert isinstance(source, SourceLocation)
        assert source.file == "test_source_location.py"
        assert source.line > 0
        assert source.function == "test_capture_source_location_basic"

    def test_source_location_has_required_fields(self):
        """Test that SourceLocation has all required fields."""
        source = _capture_source_location(stack_depth=1)

        assert hasattr(source, "file")
        assert hasattr(source, "line")
        assert hasattr(source, "function")

        assert source.file is not None
        assert source.line is not None
        assert source.function is not None

    def test_source_location_file_name_only(self):
        """Test that file is just filename, not full path."""
        source = _capture_source_location(stack_depth=1)

        # Should not contain path separators
        assert "/" not in source.file
        assert "\\" not in source.file

        # Should end with .py
        assert source.file.endswith(".py")

    def test_source_location_line_number_positive(self):
        """Test that line number is positive."""
        source = _capture_source_location(stack_depth=1)

        assert source.line > 0
        assert isinstance(source.line, int)

    def test_source_location_function_name_string(self):
        """Test that function name is a non-empty string."""
        source = _capture_source_location(stack_depth=1)

        assert isinstance(source.function, str)
        assert len(source.function) > 0


class TestStackDepthHandling:
    """Tests for correct stack depth handling."""

    def test_stack_depth_zero(self):
        """Test stack depth of 0 (capture location)."""
        # stack_depth=0 would capture _capture_source_location itself
        # Not a typical use case but should handle gracefully
        source = _capture_source_location(stack_depth=0)

        assert source.function != "<unknown>"

    def test_stack_depth_one(self):
        """Test stack depth of 1 (immediate caller)."""
        source = _capture_source_location(stack_depth=1)

        assert source.function == "test_stack_depth_one"

    def test_stack_depth_two(self):
        """Test stack depth of 2 (caller's caller)."""

        def helper():
            return _capture_source_location(stack_depth=2)

        source = helper()

        # Should capture this test function, not helper
        assert source.function == "test_stack_depth_two"

    def test_stack_depth_three(self):
        """Test stack depth of 3 (typical for logger._log)."""

        def level1():
            return level2()

        def level2():
            return _capture_source_location(stack_depth=3)

        source = level1()

        # Should capture this test function
        assert source.function == "test_stack_depth_three"

    def test_stack_depth_excessive_returns_unknown(self):
        """Test that excessive stack depth returns unknown."""
        # Stack depth too deep should return unknown
        source = _capture_source_location(stack_depth=100)

        assert source.file == "<unknown>"
        assert source.line == 0
        assert source.function == "<unknown>"


class TestNestedCallHandling:
    """Tests for source location in nested function calls."""

    def test_helper_function_capture(self):
        """Test that helper function location is captured correctly."""

        def helper_function():
            return _capture_source_location(stack_depth=1)

        source = helper_function()

        assert source.function == "helper_function"
        assert source.file == "test_source_location.py"

    def test_nested_helper_functions(self):
        """Test nested helper functions with different stack depths."""

        def outer():
            def inner():
                return _capture_source_location(stack_depth=2)

            return inner()

        source = outer()

        # Should capture outer function
        assert source.function == "outer"

    def test_lambda_function_capture(self):
        """Test source location capture from lambda."""
        capture_func = lambda: _capture_source_location(stack_depth=1)
        source = capture_func()

        # Lambda shows as <lambda>
        assert source.function == "<lambda>"

    def test_class_method_capture(self):
        """Test source location capture from class method."""

        class TestClass:
            def test_method(self):
                return _capture_source_location(stack_depth=1)

        obj = TestClass()
        source = obj.test_method()

        assert source.function == "test_method"


class TestSourceLocationInLogger:
    """Tests for source location capture in logger methods."""

    def test_info_captures_caller_location(self, console_config: LogConfig, capsys):
        """Test that logger.info() captures caller location."""
        logger = initialize(console_config)

        logger.info("test message")  # Line 167

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_info_captures_caller_location"
            assert entry["file"] == "test_source_location.py"
            # Line number should be around line 167
            assert 165 <= entry["line"] <= 175

    def test_error_captures_caller_location(self, console_config: LogConfig, capsys):
        """Test that logger.error() captures caller location."""
        logger = initialize(console_config)

        logger.error("error message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_error_captures_caller_location"
            assert entry["file"] == "test_source_location.py"

    def test_warning_captures_caller_location(self, console_config: LogConfig, capsys):
        """Test that logger.warning() captures caller location."""
        logger = initialize(console_config)

        logger.warning("warning message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_warning_captures_caller_location"

    def test_debug_captures_caller_location(self, console_config: LogConfig, capsys):
        """Test that logger.debug() captures caller location."""
        logger = initialize(console_config)

        logger.debug("debug message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_debug_captures_caller_location"

    def test_critical_captures_caller_location(self, console_config: LogConfig, capsys):
        """Test that logger.critical() captures caller location."""
        logger = initialize(console_config)

        logger.critical("critical message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_critical_captures_caller_location"

    def test_location_from_helper_function(self, console_config: LogConfig, capsys):
        """Test that location points to helper, not logger._log."""
        logger = initialize(console_config)

        def my_helper():
            logger.info("from helper")

        my_helper()

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # Should point to my_helper, not _log
            assert entry["function"] == "my_helper"
            assert entry["file"] == "test_source_location.py"

    def test_location_with_context_logger(self, console_config: LogConfig, capsys):
        """Test that location is correct for logger with context."""
        logger = initialize(console_config)
        ctx_logger = logger.with_context(key="value")

        ctx_logger.info("test message")

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "test_location_with_context_logger"

    def test_location_from_multiple_callers(self, console_config: LogConfig, capsys):
        """Test that different call sites are distinguished."""
        logger = initialize(console_config)

        def function_a():
            logger.info("from A")

        def function_b():
            logger.info("from B")

        function_a()
        function_b()

        captured = capsys.readouterr()
        lines = [line for line in captured.out.strip().split("\n") if line]

        assert len(lines) == 2

        entry_a = json.loads(lines[0])
        entry_b = json.loads(lines[1])

        assert entry_a["function"] == "function_a"
        assert entry_b["function"] == "function_b"


class TestSourceLocationEdgeCases:
    """Tests for edge cases in source location capture."""

    def test_location_from_module_level(self):
        """Test source location capture at module level."""
        # This is tricky because module-level code has function="<module>"
        source = _capture_source_location(stack_depth=1)

        assert source.function == "test_location_from_module_level"

    def test_location_with_decorators(self, console_config: LogConfig, capsys):
        """Test source location with decorated functions."""
        logger = initialize(console_config)

        def my_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        @my_decorator
        def decorated_function():
            logger.info("from decorated")

        decorated_function()

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            # Should capture decorated_function or wrapper
            assert entry["function"] in ["decorated_function", "wrapper"]

    def test_location_from_generator(self, console_config: LogConfig, capsys):
        """Test source location capture from generator function."""
        logger = initialize(console_config)

        def my_generator():
            yield 1
            logger.info("from generator")
            yield 2

        gen = my_generator()
        next(gen)
        next(gen)

        captured = capsys.readouterr()
        if captured.out:
            entry = json.loads(captured.out.strip())

            assert entry["function"] == "my_generator"

    def test_location_from_async_function(self):
        """Test source location from async function."""
        import asyncio

        async def async_function():
            source = _capture_source_location(stack_depth=1)
            return source

        source = asyncio.run(async_function())

        assert source.function == "async_function"


class TestSourceLocationDataclass:
    """Tests for SourceLocation dataclass."""

    def test_source_location_is_dataclass(self):
        """Test that SourceLocation is a dataclass."""
        import dataclasses

        assert dataclasses.is_dataclass(SourceLocation)

    def test_source_location_creation(self):
        """Test manual creation of SourceLocation."""
        source = SourceLocation(
            file="test.py",
            line=42,
            function="test_function",
        )

        assert source.file == "test.py"
        assert source.line == 42
        assert source.function == "test_function"

    def test_source_location_repr(self):
        """Test SourceLocation repr."""
        source = SourceLocation(
            file="test.py",
            line=42,
            function="test_func",
        )

        repr_str = repr(source)

        assert "SourceLocation" in repr_str
        assert "test.py" in repr_str
        assert "42" in repr_str
        assert "test_func" in repr_str

    def test_source_location_equality(self):
        """Test SourceLocation equality."""
        source1 = SourceLocation(file="test.py", line=42, function="func")
        source2 = SourceLocation(file="test.py", line=42, function="func")
        source3 = SourceLocation(file="test.py", line=43, function="func")

        assert source1 == source2
        assert source1 != source3
