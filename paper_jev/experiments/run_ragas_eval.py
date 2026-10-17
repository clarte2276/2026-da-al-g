from __future__ import annotations

import runpy
from pathlib import Path

from tracking_openai import install

install()
runpy.run_path(str(Path(__file__).with_name("ragas_eval.py")), run_name="__main__")
