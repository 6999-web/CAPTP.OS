from __future__ import annotations

from pathlib import Path


REQUIRED_PATHS = [
    "dataset",
    "configs/profiles.yaml",
    "reports/workflow_chain.mmd",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [item for item in REQUIRED_PATHS if not (root / item).exists()]
    if missing:
        print("MISSING:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("OK: training pipeline layout is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
