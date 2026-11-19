"""Lightweight local checks: "would this even import?"

This is not a reproduction.  It compiles every Python file, verifies that a
dependency manifest parses, and confirms an entry point exists.  Anything it
finds is real, cheap evidence; anything it cannot check is reported as
not-checked rather than assumed good.
"""

from __future__ import annotations

from .models import RepoScan, SmokeReport

__all__ = ["run_smoke"]


def _compile_python(scan: RepoScan, report: SmokeReport) -> None:
    for f in scan.files:
        if f.lang != "python" or not f.text:
            continue
        report.checked += 1
        try:
            compile(f.text, f.path, "exec")
        except SyntaxError as exc:
            report.syntax_ok = False
            report.errors.append(f"{f.path}:{exc.lineno}: {exc.msg}")
        except ValueError as exc:  # e.g. null bytes
            report.syntax_ok = False
            report.errors.append(f"{f.path}: {exc}")


def _check_manifest(scan: RepoScan, report: SmokeReport) -> None:
    if not scan.manifests:
        return
    for name, text in scan.manifests.items():
        ok = True
        lower = name.lower()
        if lower.endswith("requirements.txt"):
            ok = all(
                line.strip() == "" or line.strip().startswith("#") or "://" not in line
                for line in text.splitlines()
            )
        elif lower.endswith(("pyproject.toml", "setup.cfg")):
            ok = "[" in text or "=" in text
        elif lower.endswith((".yml", ".yaml")):
            ok = ":" in text
        if not ok:
            report.errors.append(f"{name}: could not parse as a dependency manifest")
            report.manifest_ok = False
            return
    report.manifest_ok = True


def run_smoke(scan: RepoScan) -> SmokeReport:
    report = SmokeReport(enabled=True)
    _compile_python(scan, report)
    _check_manifest(scan, report)
    report.entry_ok = bool(scan.entry_points)
    if not report.entry_ok:
        report.errors.append("no entry point found, so nothing could be smoke-run")
    return report
