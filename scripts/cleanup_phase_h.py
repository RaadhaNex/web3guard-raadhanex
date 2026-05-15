from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUPLICATE_ROOT_APP = ROOT / "app"
BACKEND_APP = ROOT / "backend" / "app"

if not BACKEND_APP.exists():
    raise SystemExit("Refusing cleanup: backend/app not found.")

if DUPLICATE_ROOT_APP.exists():
    shutil.rmtree(DUPLICATE_ROOT_APP)
    print("Removed duplicate root app/ folder. backend/app remains source of truth.")
else:
    print("No duplicate root app/ folder found.")
