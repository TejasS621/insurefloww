"""Module runner for the InsureFlow Pipecat voice bot."""

from __future__ import annotations

from voice_bot.bot import bot


def main() -> None:
    """Run the Pipecat bootstrapper against the exported `bot` coroutine."""

    from pipecat.runner.run import main as pipecat_main

    pipecat_main()


if __name__ == "__main__":
    main()
