#!/usr/bin/env python3
"""AutoBangumi entry with the HFZY misc extension."""

import logging
import os
import sys
from pathlib import Path

APP_DIR = Path(os.environ.get("AB_APP_DIR", "/app"))
HFZY_BACKEND = Path("/extensions/hfzy/backend")

os.chdir(APP_DIR)
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if HFZY_BACKEND.is_dir() and str(HFZY_BACKEND) not in sys.path:
    sys.path.insert(0, str(HFZY_BACKEND))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("hfzy.entry")

try:
    from hfzy.bootstrap import install, is_installed

    install()
    if is_installed():
        logger.info("HFZY bootstrap OK — misc feature routes registered")
    else:
        logger.error(
            "HFZY bootstrap did not complete; config save at "
            "/api/v1/extensions/hfzy/config will return 404"
        )
except Exception:
    logger.exception("HFZY bootstrap crashed")

if __name__ == "__main__":
    import runpy

    runpy.run_path(str(APP_DIR / "main.py"), run_name="__main__")
