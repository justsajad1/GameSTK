"""Core gameplay primitives: fighters and sprite helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Dict, Optional

import arcade
from arcade.types.rect import XYWH
from PIL import Image, ImageDraw

try:  # Allow running both as a module and as a script alongside the other files.
    from . import settings  # type: ignore
except ImportError:  # pragma: no cover - script execution path
    import settings  # type: ignore


TextureBundle = Dict[str, list[arcade.Texture]]


def make_dummy_sprite(color: tuple[int, int, int, int] = (255, 0, 255, 255)) -> arcade.Texture:
    """Create a plain placeholder texture used whenever an asset is missing."""

    img = Image.new("RGBA", (settings.FRAME_SIZE, settings.FRAME_SIZE), color)
    draw = ImageDraw.Draw(img)
    draw.text((settings.FRAME_SIZE // 3, settings.FRAME_SIZE // 3), "X", fill=(255, 255, 255, 255))
    return arcade.Texture(name="missing", image=img)


DUMMY_FRAME = make_dummy_sprite()


def load_sprite_sheet(
    sheet_path: Path | str,
    frame_size: int = settings.FRAME_SIZE,
) -> tuple[TextureBundle, dict[str, float]]:
    """Load a spritesheet into left/right oriented frames and gather visibility metrics."""

    texture_path = settings.ensure_path(sheet_path)
    if not texture_path.is_file():
        # Fall back to dummy textures when the asset is not present.
        print(f"Missing sprite replaced: {texture_path.name}")
        return (
            {"right": [DUMMY_FRAME], "left": [DUMMY_FRAME]},
            {
                "max_visible_height": float(frame_size),
                "frame_height_for_max": float(frame_size),
                "max_visible_width": float(frame_size),
                "frame_width_for_max": float(frame_size),
                "min_bottom_margin": 0.0,
                "frame_height_for_bottom": float(frame_size),
            },
        )

    frames_right: list[arcade.Texture] = []
    frames_left: list[arcade.Texture] = []
    max_visible_height = 0.0
    frame_height_for_max = float(frame_size)
    max_visible_width = 0.0
    frame_width_for_max = float(frame_size)
    min_bottom_margin = float(frame_size)
    frame_height_for_bottom = float(frame_size)

    with Image.open(texture_path) as sheet_image:
        sheet_img = sheet_image.convert("RGBA")
        sheet_width, sheet_height = sheet_img.size
        num_frames = max(1, sheet_width // frame_size)

        for frame_index in range(num_frames):
            left = frame_index * frame_size
            box = (left, 0, left + frame_size, sheet_height)
            frame_img = sheet_img.crop(box).copy()

            alpha = frame_img.split()[-1]
            bbox = alpha.getbbox()
            if bbox:
                visible_height = max(1, bbox[3] - bbox[1])
                visible_width = max(1, bbox[2] - bbox[0])
                bottom_margin = max(0, sheet_height - bbox[3])
            else:
                visible_height = sheet_height
                visible_width = frame_size
                bottom_margin = 0

            if visible_height > max_visible_height:
                max_visible_height = float(visible_height)
                frame_height_for_max = float(sheet_height)
            if visible_width > max_visible_width:
                max_visible_width = float(visible_width)
                frame_width_for_max = float(frame_size)
            if bottom_margin < min_bottom_margin:
                min_bottom_margin = float(bottom_margin)
                frame_height_for_bottom = float(sheet_height)

            tex_r = arcade.Texture(
                name=f"{texture_path.stem}_{frame_index}_R",
                image=frame_img,
            )
            frames_right.append(tex_r)

            flipped = frame_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            tex_l = arcade.Texture(
                name=f"{texture_path.stem}_{frame_index}_L",
                image=flipped,
            )
            frames_left.append(tex_l)

    if not frames_right:
        frames_right = [DUMMY_FRAME]
        frames_left = [DUMMY_FRAME]

    if max_visible_height <= 0:
        max_visible_height = float(sheet_height)
        frame_height_for_max = float(sheet_height)
    if max_visible_width <= 0:
        max_visible_width = float(frame_size)
        frame_width_for_max = float(frame_size)
    if min_bottom_margin < 0:
        min_bottom_margin = 0.0

    metrics = {
        "max_visible_height": max_visible_height,
        "frame_height_for_max": frame_height_for_max,
        "max_visible_width": max_visible_width,
        "frame_width_for_max": frame_width_for_max,
        "min_bottom_margin": min_bottom_margin,
        "frame_height_for_bottom": frame_height_for_bottom,
    }

    return {"right": frames_right, "left": frames_left}, metrics


class Fighter:
    """Animated character with input handling and combat state."""

    ACTION_FILES = {
        "idle": "Idle.png",
        "run": "Run.png",
        "jump": "Jump.png",
        "fall": "Fall.png",
        "attack1": "Attack1.png",
        "attack2": "Attack2.png",
        "attack3": "Attack3.png",
        "take hit": "Take hit.png",
        "death": "Death.png",
    }

    def __init__(
        self,
        x: float,
        y: float,
        controls: Mapping[str, int],
        name: str,
        sprite_folder: Path | str,
        sounds: Mapping[str, Optional[arcade.Sound]],
        *,
        action_files: Optional[Mapping[str, str]] = None,
        frame_size: int = settings.FRAME_SIZE,
        min_scale: float = settings.MIN_FIGHTER_SCALE,
        max_scale: float = settings.MAX_FIGHTER_SCALE,
    ) -> None:
        self.spawn_x = x
        self.base_ground_y = y
        self.controls = controls
        self.name = name
        self.sprite_folder = settings.ensure_path(sprite_folder)
        self.action_files = {k.lower(): v for k, v in (action_files or {}).items()}
        self.frame_size = frame_size
        self.sounds = sounds
        self.min_scale = min_scale
        self.max_scale = max_scale

        self.animations: Dict[str, TextureBundle] = {}
        self.image: Optional[arcade.Texture] = None
        self._max_visible_height = 0.0
        self._frame_height_for_max = float(frame_size)
        self._max_visible_width = 0.0
        self._frame_width_for_max = float(frame_size)
        self._min_bottom_margin = float("inf")
        self._frame_height_for_bottom = float(frame_size)
        self.w = settings.FIGHTER_WIDTH
        self.h = settings.FIGHTER_HEIGHT
        self.ground_y = self.base_ground_y

        self._load_textures()
        self.reset()

    def _load_textures(self) -> None:
        actions = dict(self.ACTION_FILES)
        actions.update(self.action_files)

        for state, filename in actions.items():
            sheet_path = self.sprite_folder / filename
            textures, metrics = load_sprite_sheet(sheet_path, frame_size=self.frame_size)
            if metrics["max_visible_height"] > self._max_visible_height:
                self._max_visible_height = metrics["max_visible_height"]
                self._frame_height_for_max = metrics["frame_height_for_max"]
            if metrics["max_visible_width"] > self._max_visible_width:
                self._max_visible_width = metrics["max_visible_width"]
                self._frame_width_for_max = metrics["frame_width_for_max"]
            if metrics["min_bottom_margin"] < self._min_bottom_margin:
                self._min_bottom_margin = metrics["min_bottom_margin"]
                self._frame_height_for_bottom = metrics["frame_height_for_bottom"]
            self.animations[state] = textures

        self.image = self.animations["idle"]["right"][0]
        self._update_dimensions()

    def _update_dimensions(self) -> None:
        if self._max_visible_height <= 0:
            self._max_visible_height = float(self.frame_size)
        if self._frame_height_for_max <= 0:
            self._frame_height_for_max = float(self.frame_size)
        if self._max_visible_width <= 0:
            self._max_visible_width = float(self.frame_size)
            self._frame_width_for_max = float(self.frame_size)
        if self._frame_width_for_max <= 0:
            self._frame_width_for_max = float(self.frame_size)
        if self._frame_height_for_bottom <= 0:
            self._frame_height_for_bottom = float(self.frame_size)

        desired_visible_height = settings.FIGHTER_HEIGHT
        raw_scale = desired_visible_height / self._max_visible_height
        scale = max(self.min_scale, min(self.max_scale, raw_scale))

        self.h = self._frame_height_for_max * scale
        width_candidate = self._frame_width_for_max * scale
        width_min = settings.FIGHTER_WIDTH * self.min_scale
        width_max = settings.FIGHTER_WIDTH * self.max_scale
        self.w = max(width_min, min(width_max, width_candidate))

        bottom_margin = 0.0 if self._min_bottom_margin == float("inf") else self._min_bottom_margin
        bottom_margin_scaled = bottom_margin * (self.h / max(1.0, self._frame_height_for_bottom))
        self.ground_y = self.base_ground_y + self.h / 2 - bottom_margin_scaled

    def reset(self) -> None:
        self.x = self.spawn_x
        self.y = self.ground_y
        self.vel_y = 0.0
        self.on_ground = True
        self.facing = 1 if self.spawn_x < settings.WIDTH // 2 else -1
        self.health = 100
        self.is_attacking = False
        self.is_dead = False
        self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.hit_flash_timer = 0
        self.invincible_timer = 0

    def update(self, keys: Mapping[int, bool], opponent: "Fighter") -> None:
        if self.is_dead:
            self.animate()
            return

        was_airborne = not self.on_ground
        moving = False
        if keys.get(self.controls["left"], False):
            self.x -= settings.PLAYER_SPEED
            moving = True
        if keys.get(self.controls["right"], False):
            self.x += settings.PLAYER_SPEED
            moving = True

        if not self.is_attacking:
            self.facing = 1 if self.x < opponent.x else -1
            self.state = "run" if moving else "idle"

        if keys.get(self.controls["jump"], False) and self.on_ground:
            self.vel_y = settings.JUMP_SPEED
            self.on_ground = False
            self.state = "jump"

        self.vel_y -= settings.GRAVITY
        self.y += self.vel_y
        if self.y <= self.ground_y:
            self.y = self.ground_y
            self.vel_y = 0
            self.on_ground = True
            if self.state in ["jump", "fall"]:
                self.state = "idle"
            if was_airborne:
                self.cancel_attack()

        if keys.get(self.controls["punch"], False) and not self.is_attacking:
            self.state = "attack1"
            self.frame_index = 0
            self.is_attacking = True
            self.try_hit(opponent)
        elif keys.get(self.controls["kick"], False) and not self.is_attacking:
            self.state = "attack2"
            self.frame_index = 0
            self.is_attacking = True
            self.try_hit(opponent)

        self.animate()

        if self.health <= 0 and not self.is_dead:
            self.die()

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.x = max(self.w // 2, min(settings.WIDTH - self.w // 2, self.x))

    def try_hit(self, opponent: "Fighter") -> None:
        if abs(self.x - opponent.x) < settings.ATTACK_RANGE and abs(self.y - opponent.y) < 100:
            opponent.take_hit()

    def take_hit(self) -> None:
        if self.is_dead or self.invincible_timer > 0:
            return
        self.cancel_attack()
        self.health -= settings.DAMAGE
        self.state = "take hit"
        self.frame_index = 0
        self.hit_flash_timer = settings.HIT_FLASH_DURATION
        self.invincible_timer = 20
        hit_sound = self.sounds.get("hit") if self.sounds else None
        if hit_sound:
            hit_sound.play()
        if self.health <= 0:
            self.die()

    def die(self) -> None:
        self.cancel_attack()
        self.state = "death"
        self.is_dead = True
        ko_sound = self.sounds.get("ko") if self.sounds else None
        if ko_sound:
            ko_sound.play()

    def cancel_attack(self) -> None:
        if not self.is_attacking:
            return
        self.is_attacking = False
        if self.state.startswith("attack"):
            self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0

    def animate(self) -> None:
        frames_dict = self.animations.get(self.state, {})
        direction = "right" if self.facing == 1 else "left"
        frames = frames_dict.get(direction, [DUMMY_FRAME])

        if not frames:
            frames = [DUMMY_FRAME]

        if self.state == "death":
            self.frame_timer += 1
            if self.frame_timer >= 5 and self.frame_index < len(frames) - 1:
                self.frame_timer = 0
                self.frame_index += 1
            self.image = frames[min(self.frame_index, len(frames) - 1)]
            return

        self.frame_timer += 1
        if self.frame_timer >= 5:
            self.frame_timer = 0
            self.frame_index += 1
            if self.frame_index >= len(frames):
                self.frame_index = 0
                if self.state.startswith("attack"):
                    self.state = "idle"
                    self.is_attacking = False
                elif self.state == "take hit":
                    self.state = "idle"
                    self.is_attacking = False

        self.frame_index = min(self.frame_index, len(frames) - 1)
        self.image = frames[self.frame_index]

    def draw(self) -> None:
        if self.image:
            dest_rect = XYWH(self.x, self.y, self.w, self.h)
            arcade.draw_texture_rect(self.image, dest_rect)
