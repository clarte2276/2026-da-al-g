import os
import subprocess
import sys
import time
from pathlib import Path

src = Path("../data_raw/규정/운전관리규정/운전취급규정/운전취급규정.hwp").resolve()
exe = Path(sys.executable).with_name("hwp5odt.exe")
for label, extra in (("no-embed-image", ["--no-embed-image"]), ("default", [])):
    out = Path(os.environ["TEMP"]) / f"rules-{label}.odt"
    start = time.time()
    done = subprocess.run(
        [str(exe), *extra, "--output", str(out), str(src)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
    )
    print(label, "rc", done.returncode, round(time.time() - start, 1), "s",
          out.stat().st_size if out.exists() else None, flush=True)
