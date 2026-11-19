"""Single source of truth for the package version.

Kept in its own module so that internal modules can import it without creating a
circular import through the package ``__init__``.
"""

__version__ = "0.3.1"
