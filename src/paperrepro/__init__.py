"""paperrepro - evidence-traceable reproducibility assessment.

Given a paper and the repository that claims to implement it, paperrepro builds a
ledger of quantitative claims, links every claim to concrete code evidence, runs
deterministic risk rules, and reports a graded verdict (R0 through R3) in which
every sentence can be traced back to a page, a table, or a ``path:line``.

The public entry point is :func:`assess`; the command line wrapper lives in
:mod:`paperrepro.cli`.
"""

from __future__ import annotations

from .api import Assessment, assess
from .version import __version__

__all__ = ["Assessment", "assess", "__version__"]
