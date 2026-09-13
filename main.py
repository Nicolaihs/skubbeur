"""Pygbag entrypoint for the browser build."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from clockface import main


asyncio.run(main())