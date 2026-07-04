from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
PUBLIC_STATIC_DIR = ROOT / "public" / "static"


def main() -> None:
    if PUBLIC_STATIC_DIR.exists():
        shutil.rmtree(PUBLIC_STATIC_DIR)
    shutil.copytree(STATIC_DIR, PUBLIC_STATIC_DIR)
    print(f"Copied {STATIC_DIR.relative_to(ROOT)} to {PUBLIC_STATIC_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
