"""Launch Clockface as a module or packaged application."""

from clockface import main
import asyncio


def run() -> None:
	asyncio.run(main())


if __name__ == "__main__":
	run()