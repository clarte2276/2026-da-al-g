"""Load the 행로표 and every monthly 근무계획 under data/근무계획 into the local DB::

    uv run python -m scripts.load_duty [folder]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.duty import parse_duty_xlsx, parse_route_xlsx
from app.management import save_duty_route
from app.models import DutySchedule


def main() -> None:
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "data" / "근무계획")
    init_db()
    with SessionLocal() as db:
        for path in sorted(folder.glob("*.xlsx")):
            if "행로표" in path.name:
                parsed = parse_route_xlsx(path.read_bytes(), path.name)
                save_duty_route(db, parsed, path.name)
                print(f"행로표 {parsed['effective']}: {len(parsed['turns'])} turns")
            elif m := re.search(r"(\d{4})년 (\d{1,2})월", path.name):
                month = f"{m[1]}-{int(m[2]):02d}"
                parsed = parse_duty_xlsx(path.read_bytes(), month, path.name)
                row = db.scalar(select(DutySchedule).where(DutySchedule.month == month))
                if not row:
                    row = DutySchedule(month=month, data=parsed, source_filename=path.name)
                    db.add(row)
                row.data, row.source_filename = parsed, path.name
                print(f"근무계획 {month}: {len(parsed['drivers'])} drivers")
        db.commit()


if __name__ == "__main__":
    main()
