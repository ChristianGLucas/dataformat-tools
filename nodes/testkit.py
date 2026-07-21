"""Shared test helpers for christiangeorgelucas/dataformat-tools."""


class TestContext:
    """Minimal AxiomContext implementation for unit tests."""

    class _Logger:
        def debug(self, msg: str, **attrs) -> None: pass
        def info(self, msg: str, **attrs) -> None: pass
        def warn(self, msg: str, **attrs) -> None: pass
        def error(self, msg: str, **attrs) -> None: pass

    class _Secrets:
        def __init__(self, m: dict) -> None:
            self._m = m or {}

        def get(self, name: str):
            v = self._m.get(name)
            return (v, True) if v is not None else ("", False)

    def __init__(self, secrets_map: dict | None = None) -> None:
        self.log = self._Logger()
        self.secrets = self._Secrets(secrets_map or {})
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"


def ax() -> TestContext:
    return TestContext()


def assert_ok(result) -> None:
    """Fail loudly, with the message, when a node returned an error."""
    assert not result.error.code, f"unexpected error: {result.error.code}: {result.error.message}"


def assert_error(result, code: str) -> None:
    assert result.error.code == code, (
        f"expected error {code}, got {result.error.code or '<none>'}: "
        f"{result.error.message}"
    )
    assert result.error.message, "an error must carry a human-readable message"


def assert_valid(result) -> None:
    assert result.valid, f"expected valid, got invalid: {result.error_message}"


def assert_invalid(result) -> None:
    assert not result.valid, "expected invalid, got valid"
    assert result.error_message, "an invalid ValidateResult must carry error_message"
