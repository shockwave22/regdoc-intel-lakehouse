"""Smoke tests for repository scaffolding."""


def test_scaffold_import_path() -> None:
    """Ensure the package scaffold is importable."""
    import regdoc_intel  # noqa: F401
