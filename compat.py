"""Compatibility helpers for older Python versions."""

from __future__ import annotations


def ensure_importlib_metadata_support() -> None:
    """Ensure importlib.metadata has packages_distributions on Python < 3.10."""
    try:
        import importlib.metadata as stdlib_metadata
    except ImportError:
        return

    if hasattr(stdlib_metadata, "packages_distributions"):
        return

    try:
        import importlib_metadata as backport  # type: ignore
    except Exception:
        backport = None

    if backport and hasattr(backport, "packages_distributions"):
        stdlib_metadata.packages_distributions = backport.packages_distributions  # type: ignore[attr-defined]


# Run on import so any module can safely rely on the attribute
ensure_importlib_metadata_support()

