"""Copy generator CSVs into Airbyte CSV source path."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "data" / "output"
DEST = REPO / "ingest" / "airbyte" / "csv_source"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    if not SRC.exists():
        raise SystemExit("Run python -m data.generator first")
    count = 0
    for path in SRC.glob("*.csv"):
        shutil.copy2(path, DEST / path.name)
        count += 1
    print(f"Copied {count} CSVs → {DEST}")


if __name__ == "__main__":
    main()
