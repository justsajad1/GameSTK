"""Game configuration constants and shared settings."""

from __future__ import annotations

import os

import arcade
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WIDTH, HEIGHT = 1280, 720
FPS = 60
PLAYER_SPEED = 6
JUMP_SPEED = 22
GRAVITY = 1.2
ATTACK_RANGE = 80
DAMAGE = 25
FRAME_SIZE = 162
FIGHTER_WIDTH = 200
FIGHTER_HEIGHT = 300
HIT_FLASH_DURATION = 10
WINS_TO_MATCH = 3  # First to 3 wins the match

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GROUND = (34, 139, 34)
HUD_BG = (0, 0, 0, 160)

try:
    KEY = arcade.key  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - compatibility path
    from pyglet.window import key as KEY  # type: ignore

SOUND_FILES = {
    "music": os.path.join("assets", "sounds", "music.mp3"),
    "hit": os.path.join("assets", "sounds", "hit.wav"),
    "ko": os.path.join("assets", "sounds", "ko.wav"),
}
FIGHTER_SPRITE_DIRS = {
    "fighter1": os.path.join("assets", "Sprites", "Fighter1"),
    "fighter2": os.path.join("assets", "Sprites", "Fighter2"),
}
FIGHTER_OVERRIDES = {
    "fighter1": {
        "action_files": {},
        "frame_size": FRAME_SIZE,
    },
    "fighter2": {
        "action_files": {
            "take hit": "Take Hit.png",
            "attack3": "Attack2.png",
        },
        "frame_size": 200,
    },
}
