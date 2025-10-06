"""Business Unit: execution | Status: current.

Test for execution_v2.config module initialization.

Verifies that the config module exports the correct public API and maintains
import idempotency for the ExecutionProviders DI container.
"""


class TestConfigModuleInit:
    """Test execution_v2.config.__init__ module."""

    def test_exports_execution_providers(self) -> None:
        """Test that ExecutionProviders is exported in __all__."""
        from the_alchemiser.execution_v2 import config

        assert hasattr(config, "__all__")
        assert isinstance(config.__all__, list)
        assert "ExecutionProviders" in config.__all__

    def test_can_import_execution_providers(self) -> None:
        """Test that ExecutionProviders can be imported from config module."""
        from the_alchemiser.execution_v2.config import ExecutionProviders

        assert ExecutionProviders is not None
        assert hasattr(ExecutionProviders, "__name__")

    def test_import_is_idempotent(self) -> None:
        """Test that importing the module multiple times returns same reference."""
        from the_alchemiser.execution_v2.config import ExecutionProviders as EP1
        from the_alchemiser.execution_v2.config import ExecutionProviders as EP2

        assert EP1 is EP2

    def test_all_exports_are_importable(self) -> None:
        """Test that all items in __all__ can actually be imported."""
        from the_alchemiser.execution_v2 import config

        for export_name in config.__all__:
            assert hasattr(config, export_name), f"{export_name} not found in module"
            export_obj = getattr(config, export_name)
            assert export_obj is not None, f"{export_name} is None"
