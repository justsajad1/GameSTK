"""Game configuration constants and shared settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import arcade

try:
    KEY = arcade.key  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - compatibility path
    from pyglet.window import key as KEY  # type: ignore

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
GRAVITY = 0.7
ATTACK_RANGE = 120
DAMAGE = 20
FRAME_SIZE = 162
FIGHTER_WIDTH = 200
FIGHTER_HEIGHT = 300
MIN_FIGHTER_SCALE = 0.9
MAX_FIGHTER_SCALE = 1.4
HIT_FLASH_DURATION = 10
WINS_TO_MATCH = 3  # First to 3 wins the match
WINDOW_TITLE = "The Battle of Empires"
GROUND_Y = 150
ROUND_TIME_LIMIT = 60.0  # Seconds allotted per round
DEFAULT_FRAME_INTERVAL = 5  # Update steps between animation frames when timing is generic
ATTACK_ANIMATION_DURATION = 0.5  # Seconds a basic attack animation (and hit lockout) should last
MIN_PLAYER_DISTANCE = 0  # Baseline horizontal spacing preserved between fighters
VERTICAL_SEPARATION_THRESHOLD = 140  # Vertical gap above which fighters no longer push apart
COLLISION_SCALE = 0.45  # Multiplier applied to a sprite's visible width to determine collision width
COLLISION_MIN_WIDTH = 28  # Minimum collision width used for very narrow sprites
TOUCH_TOLERANCE = 4  # Allowable overlap before fighters are pushed apart
HIT_HORIZONTAL_BUFFER = 14  # Extra reach added to collision span when validating hits
HIT_VERTICAL_TOLERANCE = 120  # Vertical gap within which hits may register
FIGHTER_TEXTURE_UPSCALE = 2.0  # Multiplier applied to sprite frames before textures are created
FIGHTER_TEXTURE_MAX_DIMENSION = 768  # Prevent runaway upscale for large source art (0 disables the guard)

ATTACK_PROFILES = {
    "attack1": {
        "damage": 20,
        "cooldown": 1.0 / 3.0,
        "hit_frame_ratio": 0.4,
    },
    "attack2": {
        "damage": 30,
        "cooldown": 0.5,
        "hit_frame_ratio": 0.5,
    },
    "attack3": {
        "damage": 45,
        "cooldown": 1.0,
        "hit_frame_ratio": 0.6,
    },
}

PLAYER_CONTROLS = {
    "player1": {
        "left": getattr(KEY, "A", ord("A")),
        "right": getattr(KEY, "D", ord("D")),
        "jump": getattr(KEY, "W", ord("W")),
        "punch": getattr(KEY, "F", ord("F")),
        "kick": getattr(KEY, "G", ord("G")),
        "special": getattr(KEY, "H", ord("H")),
    },
    "player2": {
        "left": getattr(KEY, "LEFT", getattr(KEY, "A", ord("A"))),
        "right": getattr(KEY, "RIGHT", getattr(KEY, "D", ord("D"))),
        "jump": getattr(KEY, "UP", getattr(KEY, "W", ord("W"))),
        "punch": getattr(KEY, "NUM_0", getattr(KEY, "NUMPAD_0", getattr(KEY, "KP_0", ord("0")))),
        "kick": getattr(KEY, "NUM_1", getattr(KEY, "NUMPAD_1", getattr(KEY, "KP_1", ord("1")))),
        "special": getattr(KEY, "NUM_2", getattr(KEY, "NUMPAD_2", getattr(KEY, "KP_2", ord("2")))),
    },
}

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GROUND = (34, 139, 34)
HUD_BG = (0, 0, 0, 160)

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
    "ROUND_TIME_LIMIT",
    "DEFAULT_FRAME_INTERVAL",
    "ATTACK_ANIMATION_DURATION",
    "MIN_PLAYER_DISTANCE",
    "VERTICAL_SEPARATION_THRESHOLD",
    "COLLISION_SCALE",
    "COLLISION_MIN_WIDTH",
    "TOUCH_TOLERANCE",
    "HIT_HORIZONTAL_BUFFER",
    "HIT_VERTICAL_TOLERANCE",
    "ATTACK_PROFILES",
    "PLAYER_CONTROLS",
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
]
