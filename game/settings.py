"""Game configuration constants and shared settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import arcade

BASE_DIR = Path(__file__).resolve().parent.parent


def base_path(*parts: str | Path) -> Path:
    """Return an absolute path rooted at the repository base directory."""

    resolved = [part if isinstance(part, Path) else Path(part) for part in parts]
    return BASE_DIR.joinpath(*resolved)


ASSETS_DIR = base_path("assets")


def asset_path(*parts: str | Path) -> Path:
    """Return an absolute path within the project's assets directory."""

    resolved = [part if isinstance(part, Path) else Path(part) for part in parts]
    return ASSETS_DIR.joinpath(*resolved)


def ensure_path(value: str | Path) -> Path:
    """Coerce a string or Path into an absolute Path instance."""

    candidate = value if isinstance(value, Path) else Path(value)
    return candidate if candidate.is_absolute() else base_path(candidate)


WIDTH, HEIGHT = 1280, 720
FPS = 60
PLAYER_SPEED = 6
JUMP_SPEED = 15
GRAVITY = 0.9
ATTACK_RANGE = 120
DAMAGE = 20
FRAME_SIZE = 162
FIGHTER_WIDTH = 200
FIGHTER_HEIGHT = 300
MIN_FIGHTER_SCALE = 0.9
MAX_FIGHTER_SCALE = 1.4
HIT_FLASH_DURATION = 10
WINS_TO_MATCH = 3  # First to 3 wins the match
WINDOW_TITLE = "Der Kampf der Zwei Koenige"
GROUND_Y = 150

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GROUND = (34, 139, 34)
HUD_BG = (0, 0, 0, 160)

try:
    KEY = arcade.key  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - compatibility path
    from pyglet.window import key as KEY  # type: ignore


def key_code(*names: str, default: int | None = None) -> int:
    """Resolve a key code with graceful fallbacks for pyglet naming changes."""

    for name in names:
        candidate = getattr(KEY, name, None)
        if candidate is not None:
            return candidate
    if default is not None:
        return default
    if names:
        fallback = names[0]
        # Allow simple ASCII fallback if provided, e.g. "A" -> ord("A")
        if len(fallback) == 1:
            return getattr(KEY, fallback.upper(), ord(fallback))
    raise AttributeError(f"Key code not available for any of: {', '.join(names)}")


SOUND_FILES = {
    "music": asset_path("sounds", "music.mp3"),
    "hit": asset_path("sounds", "hit.wav"),
    "ko": asset_path("sounds", "ko.wav"),
}

FIGHTERS: dict[str, dict[str, Any]] = {
    "tutankhamun": {
        "name": "Tutankhamun",
        "sprite_dir": asset_path("Sprites", "Fighter1"),
        "frame_size": FRAME_SIZE,
        "action_files": {},
        "max_scale": 1.8,
    },
    "charlemagne": {
        "name": "Charlemagne",
        "sprite_dir": asset_path("Sprites", "Fighter2"),
        "frame_size": 200,
        "action_files": {
            "take hit": "Take Hit.png",
            "attack3": "Attack2.png",
        },
        "max_scale": 1.8,
    },
    "knight_2": {
        "name": "Knight II",
        "sprite_dir": asset_path("Sprites", "Knight_2"),
        "frame_size": 128,
        "action_files": {
            "idle": "Idle.png",
            "run": "Run.png",
            "jump": "Jump.png",
            "fall": "Jump.png",
            "attack1": "Attack 1.png",
            "attack2": "Attack 2.png",
            "attack3": "Attack 3.png",
            "take hit": "Hurt.png",
            "death": "Dead.png",
        },
    },
    "knight_3": {
        "name": "Knight III",
        "sprite_dir": asset_path("Sprites", "Knight_3"),
        "frame_size": 128,
        "action_files": {
            "idle": "Idle.png",
            "run": "Run.png",
            "jump": "Jump.png",
            "fall": "Jump.png",
            "attack1": "Attack 1.png",
            "attack2": "Attack 2.png",
            "attack3": "Attack 3.png",
            "take hit": "Hurt.png",
            "death": "Dead.png",
        },
    },
    "samurai": {
        "name": "Samurai",
        "sprite_dir": asset_path("Sprites", "Samurai"),
        "frame_size": 128,
        "action_files": {
            "idle": "Idle.png",
            "run": "Run.png",
            "jump": "Jump.png",
            "fall": "Jump.png",
            "attack1": "Attack_1.png",
            "attack2": "Attack_2.png",
            "attack3": "Attack_3.png",
            "take hit": "Hurt.png",
            "death": "Dead.png",
        },
    },
    "samurai_archer": {
        "name": "Samurai Archer",
        "sprite_dir": asset_path("Sprites", "Samurai_Archer"),
        "frame_size": 128,
        "action_files": {
            "idle": "Idle.png",
            "run": "Run.png",
            "jump": "Jump.png",
            "fall": "Jump.png",
            "attack1": "Attack_1.png",
            "attack2": "Attack_2.png",
            "attack3": "Shot.png",
            "take hit": "Hurt.png",
            "death": "Dead.png",
        },
    },
    "samurai_commander": {
        "name": "Samurai Commander",
        "sprite_dir": asset_path("Sprites", "Samurai_Commander"),
        "frame_size": 128,
        "action_files": {
            "idle": "Idle.png",
            "run": "Run.png",
            "jump": "Jump.png",
            "fall": "Jump.png",
            "attack1": "Attack_1.png",
            "attack2": "Attack_2.png",
            "attack3": "Attack_3.png",
            "take hit": "Hurt.png",
            "death": "Dead.png",
        },
    },
}

DEFAULT_FIGHTER_SELECTION = {
    "player1": "tutankhamun",
    "player2": "charlemagne",
}


__all__ = [
    "BASE_DIR",
    "WIDTH",
    "HEIGHT",
    "FPS",
    "PLAYER_SPEED",
    "JUMP_SPEED",
    "GRAVITY",
    "ATTACK_RANGE",
    "DAMAGE",
    "FRAME_SIZE",
    "FIGHTER_WIDTH",
    "FIGHTER_HEIGHT",
    "MIN_FIGHTER_SCALE",
    "MAX_FIGHTER_SCALE",
    "GROUND_Y",
    "HIT_FLASH_DURATION",
    "WINS_TO_MATCH",
    "WINDOW_TITLE",
    "ASSETS_DIR",
    "WHITE",
    "RED",
    "GREEN",
    "GROUND",
    "HUD_BG",
    "KEY",
    "SOUND_FILES",
    "FIGHTERS",
    "DEFAULT_FIGHTER_SELECTION",
    "base_path",
    "asset_path",
    "ensure_path",
    "key_code",
]
