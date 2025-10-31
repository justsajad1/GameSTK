"""Entrypoint for Der Kampf des Zwei Könige."""

from __future__ import annotations

import arcade
import os

try:  # Allow running both as script and as package module.
    from . import app, settings  # type: ignore
except ImportError:  # pragma: no cover - script execution path
    import app  # type: ignore
    import settings  # type: ignore


def main() -> None:
    os.chdir(settings.BASE_DIR)
    app.StickmanFighterGame()
    arcade.run()


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
