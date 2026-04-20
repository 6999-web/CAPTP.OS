from __future__ import annotations

from pathlib import Path

from tools.acceptance_audit import run_static_audit


def test_acceptance_static_audit_passes_key_requirements():
    backend_root = Path(__file__).resolve().parents[1]
    checks = run_static_audit(backend_root)
    assert all(checks.values()), checks
