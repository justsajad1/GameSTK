"""Core gameplay primitives: fighters and sprite helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import arcade
from arcade.types.rect import XYWH
from PIL import Image, ImageDraw, ImageFilter

try:  # Allow running both as a module and as a script alongside the other files.
    from . import settings  # type: ignore
except ImportError:  # pragma: no cover - script execution path
    import settings  # type: ignore


TextureBundle = Dict[str, list[arcade.Texture]]

_SPRITE_CACHE: Dict[tuple[Path, int], tuple[TextureBundle, dict[str, float]]] = {}


@dataclass
class AttackSpec:
    name: str
    damage: int
    cooldown_frames: int
    hit_frame_ratio: float = 0.5
    effect: Optional[str] = None


@dataclass
class ActiveEffect:
    name: str
    frames: list[arcade.Texture]
    interval: float
    width: float
    height: float
    offset: float
    facing: int
    x: float = 0.0
    y: float = 0.0
    frame_index: int = 0
    timer: float = 0.0
    anchor: str = "front"


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
    cache_key = (texture_path.resolve(), frame_size)
    cached = _SPRITE_CACHE.get(cache_key)
    if cached:
        textures_cached, metrics_cached = cached
        textures_copy = {side: frames[:] for side, frames in textures_cached.items()}
        return textures_copy, dict(metrics_cached)

    if not texture_path.is_file():
        # Fall back to dummy textures when the asset is not present.
        print(f"Missing sprite replaced: {texture_path.name}")
        textures = {"right": [DUMMY_FRAME], "left": [DUMMY_FRAME]}
        metrics = {
            "max_visible_height": float(frame_size),
            "frame_height_for_max": float(frame_size),
            "max_visible_width": float(frame_size),
            "frame_width_for_max": float(frame_size),
            "min_bottom_margin": 0.0,
            "frame_height_for_bottom": float(frame_size),
        }
        _SPRITE_CACHE[cache_key] = (textures, metrics)
        textures_copy = {side: frames[:] for side, frames in textures.items()}
        return textures_copy, dict(metrics)

    frames_right: list[arcade.Texture] = []
    frames_left: list[arcade.Texture] = []
    max_visible_height = 0.0
    frame_height_for_max = float(frame_size)
    max_visible_width = 0.0
    frame_width_for_max = float(frame_size)
    min_bottom_margin = float(frame_size)
    frame_height_for_bottom = float(frame_size)

    upscale_factor = float(getattr(settings, "FIGHTER_TEXTURE_UPSCALE", 1.0))
    max_dimension = float(getattr(settings, "FIGHTER_TEXTURE_MAX_DIMENSION", 0.0))
    sharpen_percent = float(getattr(settings, "FIGHTER_TEXTURE_SHARPEN_PERCENT", 0.0))
    sharpen_radius = float(getattr(settings, "FIGHTER_TEXTURE_SHARPEN_RADIUS", 0.0))
    sharpen_threshold = int(getattr(settings, "FIGHTER_TEXTURE_SHARPEN_THRESHOLD", 0))

    try:
        resample_high = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - Pillow < 9 compatibility
        resample_high = getattr(Image, "LANCZOS", Image.BICUBIC)

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

            processed_frame = frame_img
            target_scale = max(1.0, upscale_factor)
            if max_dimension > 0:
                max_edge = max(processed_frame.size)
                if max_edge > 0:
                    max_scale_allowed = max_dimension / max_edge
                    max_scale_allowed = max(1.0, max_scale_allowed)
                    target_scale = min(target_scale, max_scale_allowed)
            if target_scale > 1.001:
                new_width = max(1, int(round(processed_frame.width * target_scale)))
                new_height = max(1, int(round(processed_frame.height * target_scale)))
                processed_frame = processed_frame.resize((new_width, new_height), resample=resample_high)
            if sharpen_percent > 0 and processed_frame.width > 1 and processed_frame.height > 1:
                processed_frame = processed_frame.filter(
                    ImageFilter.UnsharpMask(
                        radius=max(0.0, float(sharpen_radius)),
                        percent=max(0, int(round(sharpen_percent))),
                        threshold=max(0, int(sharpen_threshold)),
                    )
                )
            frame_img = processed_frame

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

    textures = {"right": frames_right, "left": frames_left}
    _SPRITE_CACHE[cache_key] = (textures, metrics)
    textures_copy = {side: frames[:] for side, frames in textures.items()}
    return textures_copy, dict(metrics)


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
    ATTACK_INPUT_PRIORITY: tuple[tuple[str, str], ...] = (
        ("attack1", "punch"),
        ("attack2", "kick"),
        ("attack3", "special"),
    )

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
        attack_specs: Optional[Mapping[str, Mapping[str, Any]]] = None,
        attack_effects: Optional[Mapping[str, str]] = None,
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
        self.attack_effect_files = {k.lower(): v for k, v in (attack_effects or {}).items()}
        self.frame_size = frame_size
        self.sounds = sounds
        self.min_scale = min_scale
        self.max_scale = max_scale

        self.attack_specs = self._build_attack_specs(attack_specs)
        self.attack_cooldowns: Dict[str, int] = {key: 0 for key in self.attack_specs}
        self.current_attack_state: Optional[str] = None
        self.current_attack_spec: Optional[AttackSpec] = None
        self.current_attack_hit_done = False
        self.attack_hit_frames: Dict[str, int] = {}
        self.state_frame_counts: Dict[str, int] = {}
        self.attack_effect_textures: Dict[str, TextureBundle] = {}
        self.attack_effect_dimensions: Dict[str, tuple[float, float]] = {}
        self.effect_intervals: Dict[str, float] = {}
        self.active_effects: list[ActiveEffect] = []

        self.animations: Dict[str, TextureBundle] = {}
        self.frame_intervals: Dict[str, float] = {}
        self.image: Optional[arcade.Texture] = None
        self._scale_factor = 1.0
        self.collision_half_width = settings.FIGHTER_WIDTH / 2
        self._max_visible_height = 0.0
        self._frame_height_for_max = float(frame_size)
        self._max_visible_width = 0.0
        self._frame_width_for_max = float(frame_size)
        self._min_bottom_margin = float("inf")
        self._frame_height_for_bottom = float(frame_size)
        self.w = settings.FIGHTER_WIDTH
        self.h = settings.FIGHTER_HEIGHT
        self.ground_y = self.base_ground_y
        
        self._was_jump_pressed = False  # Track previous jump key state for edge detection

        self._load_textures()
        self.reset()

    def _build_attack_specs(
        self, overrides: Optional[Mapping[str, Mapping[str, Any]]]
    ) -> Dict[str, AttackSpec]:
        base_profiles: Dict[str, Dict[str, Any]] = {
            key: dict(value) for key, value in settings.ATTACK_PROFILES.items()
        }
        if overrides:
            for key, custom in overrides.items():
                key_lower = key.lower()
                merged = base_profiles.get(key_lower, {}).copy()
                merged.update(dict(custom))
                base_profiles[key_lower] = merged

        specs: Dict[str, AttackSpec] = {}
        fallback = base_profiles.get("attack1", {"damage": 20, "cooldown": 0.5, "hit_frame_ratio": 0.5})

        for key, data in base_profiles.items():
            damage = int(data.get("damage", fallback.get("damage", 20)))
            cooldown = float(data.get("cooldown", fallback.get("cooldown", 0.5)))
            ratio = float(data.get("hit_frame_ratio", fallback.get("hit_frame_ratio", 0.5)))
            cooldown_frames = max(1, int(round(cooldown * settings.FPS)))
            effect_name = data.get("effect")
            specs[key] = AttackSpec(
                name=key,
                damage=damage,
                cooldown_frames=cooldown_frames,
                hit_frame_ratio=max(0.0, min(1.0, ratio)),
                effect=effect_name if isinstance(effect_name, str) else None,
            )

        for key, spec in specs.items():
            if spec.effect is None and key in self.attack_effect_files:
                spec.effect = self.attack_effect_files[key]

        return specs

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
            self._register_frame_interval(state, textures)

        self._load_attack_effects()
        self.image = self.animations["idle"]["right"][0]
        self._update_dimensions()

    def _load_attack_effects(self) -> None:
        if not self.attack_effect_files:
            return

        for state, filename in self.attack_effect_files.items():
            path = self.sprite_folder / filename
            spec = self.attack_specs.get(state)
            if not path.is_file():
                continue

            try:
                with Image.open(path) as effect_img:
                    frame_size = effect_img.size[1] or effect_img.size[0] or self.frame_size
            except FileNotFoundError:
                continue

            textures, metrics = load_sprite_sheet(path, frame_size=frame_size)
            self.attack_effect_textures[state] = textures
            width = metrics.get("max_visible_width", float(frame_size))
            height = metrics.get("max_visible_height", float(frame_size))
            self.attack_effect_dimensions[state] = (width, height)

            frame_counts = [len(frames) for frames in textures.values() if frames]
            frame_count = max(frame_counts) if frame_counts else 1
            total_updates = float(spec.cooldown_frames) if spec else settings.DEFAULT_FRAME_INTERVAL * frame_count
            interval = max(1.0, total_updates / max(1, frame_count))
            self.effect_intervals[state] = float(interval)

            if spec and spec.effect is None:
                spec.effect = filename

    def _register_frame_interval(self, state: str, textures: TextureBundle) -> None:
        frame_counts = [len(frames) for frames in textures.values() if frames]
        frame_count = max(frame_counts, default=1)
        self.state_frame_counts[state] = frame_count

        if state.startswith("attack"):
            spec = self.attack_specs.get(state)
            if spec:
                total_updates = float(spec.cooldown_frames)
                hit_frame = int(round((frame_count - 1) * spec.hit_frame_ratio))
                self.attack_hit_frames[state] = max(0, min(frame_count - 1, hit_frame))
            else:
                total_updates = max(1.0, settings.ATTACK_PROFILES.get("attack1", {}).get("cooldown", 0.5) * settings.FPS)
                self.attack_hit_frames[state] = max(0, min(frame_count - 1, frame_count // 2))
            interval = max(1.0, total_updates / max(1, frame_count))
        else:
            interval = float(settings.DEFAULT_FRAME_INTERVAL)

        self.frame_intervals[state] = interval

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
        self._scale_factor = scale

        visible_width = self._max_visible_width * scale if self._max_visible_width > 0 else self.w
        collision_width = max(settings.COLLISION_MIN_WIDTH, visible_width * settings.COLLISION_SCALE)
        collision_half = collision_width / 2 if collision_width > 0 else self.w / 2
        self.collision_half_width = max(8.0, min(self.w / 2, collision_half))

        bottom_margin = 0.0 if self._min_bottom_margin == float("inf") else self._min_bottom_margin
        bottom_margin_scaled = bottom_margin * (self.h / max(1.0, self._frame_height_for_bottom))
        self.ground_y = self.base_ground_y + self.h / 2 - bottom_margin_scaled

    def reset(self) -> None:
        self.x = self.spawn_x
        self.y = self.ground_y
        self.vel_y = 0.0
        self.on_ground = True
        self.jumps_remaining = 2  # Allow double jump
        self.facing = 1 if self.spawn_x < settings.WIDTH // 2 else -1
        self.health = 100
        self.is_attacking = False
        self.is_dead = False
        self.state = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.hit_flash_timer = 0
        self.invincible_timer = 0
        self._was_jump_pressed = False
        self.current_attack_state = None
        self.current_attack_spec = None
        self.current_attack_hit_done = False
        for key in self.attack_cooldowns:
            self.attack_cooldowns[key] = 0
        self.active_effects.clear()

    def update(self, keys: Mapping[int, bool], opponent: "Fighter") -> None:
        if self.is_dead:
            self.animate()
            self._update_effects()
            return

        self._decrement_attack_cooldowns()

        was_airborne = not self.on_ground
        moving = False
        if self._control_pressed("left", keys):
            self.x -= settings.PLAYER_SPEED
            moving = True
        if self._control_pressed("right", keys):
            self.x += settings.PLAYER_SPEED
            moving = True

        if not self.is_attacking:
            self.facing = 1 if self.x < opponent.x else -1
            if self.on_ground:
                self.state = "run" if moving else "idle"

        # Check for jump key press (edge detection - only trigger on press, not while held)
        jump_pressed = self._control_pressed("jump", keys)
        if jump_pressed and not self._was_jump_pressed and self.jumps_remaining > 0:
            self.vel_y = settings.JUMP_SPEED
            self.on_ground = False
            self.state = "jump"
            self.jumps_remaining -= 1
        self._was_jump_pressed = jump_pressed

        self.vel_y -= settings.GRAVITY
        self.y += self.vel_y
        if self.y <= self.ground_y:
            self.y = self.ground_y
            self.vel_y = 0
            self.on_ground = True
            self.jumps_remaining = 2  # Reset jumps when landing
            if self.state in ["jump", "fall"]:
                self.state = "idle"
            if was_airborne:
                self.cancel_attack()
        elif (
            self.vel_y < 0
            and not self.is_attacking
            and self.state not in ("take hit", "death")
        ):
            self.state = "fall"

        if not self.is_attacking:
            for attack_state, control_name in self.ATTACK_INPUT_PRIORITY:
                if not self._control_pressed(control_name, keys):
                    continue
                if not self._can_execute_attack(attack_state):
                    continue
                self._start_attack(attack_state)
                break

        self.animate()
        self._resolve_attack_hit(opponent)
        self._update_effects()

        if self.health <= 0 and not self.is_dead:
            self.die()

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        half_width = self.w / 2
        self.x = max(half_width, min(settings.WIDTH - half_width, self.x))

    def _decrement_attack_cooldowns(self) -> None:
        for key, remaining in self.attack_cooldowns.items():
            if remaining > 0:
                self.attack_cooldowns[key] = max(0, remaining - 1)

    def _control_pressed(self, control: str, keys: Mapping[int, bool]) -> bool:
        code = self.controls.get(control)
        if code is None:
            return False
        return bool(keys.get(code, False))

    def _can_execute_attack(self, state: str) -> bool:
        if state not in self.animations:
            return False
        return self.attack_cooldowns.get(state, 0) <= 0

    def _start_attack(self, state: str) -> None:
        spec = self.attack_specs.get(state)
        if spec is None:
            return

        self.state = state
        self.frame_index = 0
        self.frame_timer = 0
        self.is_attacking = True
        self.current_attack_state = state
        self.current_attack_spec = spec
        self.current_attack_hit_done = False
        self.attack_cooldowns[state] = spec.cooldown_frames

        if spec.effect:
            self._spawn_attack_effect(state)

        if state == "attack3" and self.sounds:
            special_sound = self.sounds.get("hit")
            if special_sound:
                try:
                    special_sound.play()
                except Exception:  # pragma: no cover - audio backend safety
                    pass

    def _resolve_attack_hit(self, opponent: "Fighter") -> None:
        if not self.current_attack_spec or self.current_attack_hit_done:
            return

        attack_state = self.current_attack_state
        if not attack_state:
            return

        hit_frame = self.attack_hit_frames.get(attack_state, 0)
        if self.frame_index < hit_frame:
            return

        spec = self.current_attack_spec
        self.current_attack_hit_done = True
        self.try_hit(opponent, spec.damage, spec)

    def _spawn_attack_effect(self, state: str) -> None:
        textures = self.attack_effect_textures.get(state)
        if not textures:
            return

        direction = "right" if self.facing == 1 else "left"
        frames = textures.get(direction)
        if not frames:
            frames = textures.get("right") or textures.get("left") or []
        if not frames:
            return

        width_px, height_px = self.attack_effect_dimensions.get(state, (self.frame_size, self.frame_size))
        if state == "attack3":
            effect_width = max(1.0, width_px * self._scale_factor * 2.5)
        else:
            effect_width = max(1.0, width_px * self._scale_factor)
        effect_height = max(1.0, height_px * self._scale_factor)
        interval = self.effect_intervals.get(state, float(settings.DEFAULT_FRAME_INTERVAL))
        offset = self.collision_half_width + effect_width / 2 + 8

        effect = ActiveEffect(
            name=state,
            frames=list(frames),
            interval=interval,
            width=effect_width,
            height=effect_height,
            offset=offset,
            facing=self.facing,
        )
        effect.x = self.x + self.facing * offset
        effect.y = self.y + self.h * 0.1
        self.active_effects.append(effect)

    def _update_effects(self) -> None:
        if not self.active_effects:
            return

        base_y = self.y + self.h * 0.1
        for effect in list(self.active_effects):
            effect.timer += 1
            if effect.timer >= effect.interval:
                effect.timer -= effect.interval
                effect.frame_index += 1
                if effect.frame_index >= len(effect.frames):
                    self.active_effects.remove(effect)
                    continue

            if effect.anchor == "front":
                effect.facing = self.facing
            effect.x = self.x + effect.facing * effect.offset
            effect.y = base_y

    def _reset_current_attack(self) -> None:
        self.current_attack_state = None
        self.current_attack_spec = None
        self.current_attack_hit_done = False

    def try_hit(
        self,
        opponent: "Fighter",
        damage: int,
        attack_spec: Optional[AttackSpec] = None,
    ) -> bool:
        horizontal_gap = abs(self.x - opponent.x)
        vertical_gap = abs(self.y - opponent.y)
        collision_span = self.collision_half_width + opponent.collision_half_width
        allowed_range = max(settings.MIN_PLAYER_DISTANCE, collision_span) + settings.HIT_HORIZONTAL_BUFFER
        if horizontal_gap <= allowed_range and vertical_gap <= settings.HIT_VERTICAL_TOLERANCE:
            opponent.take_hit(damage, attack_spec=attack_spec)
            return True
        return False

    def take_hit(self, damage: int, *, attack_spec: Optional[AttackSpec] = None) -> None:
        if self.is_dead or self.invincible_timer > 0:
            return
        self.cancel_attack()
        self.health -= max(0, damage)
        self.state = "take hit"
        self.frame_index = 0
        self.frame_timer = 0
        self.hit_flash_timer = settings.HIT_FLASH_DURATION
        if attack_spec:
            invuln = max(6, min(30, attack_spec.cooldown_frames // 2 or 6))
        else:
            invuln = 20
        self.invincible_timer = invuln
        hit_sound = self.sounds.get("hit") if self.sounds else None
        if hit_sound:
            hit_sound.play()
        if self.health <= 0:
            self.die()

    def die(self) -> None:
        self.cancel_attack()
        self.state = "death"
        self.is_dead = True
        self.frame_timer = 0
        ko_sound = self.sounds.get("ko") if self.sounds else None
        if ko_sound:
            ko_sound.play()

    def cancel_attack(self) -> None:
        if self.is_attacking and self.state.startswith("attack"):
            self.state = "idle"
        self.is_attacking = False
        self._reset_current_attack()
        self.frame_index = 0
        self.frame_timer = 0

    def animate(self) -> None:
        frames_dict = self.animations.get(self.state, {})
        direction = "right" if self.facing == 1 else "left"
        frames = frames_dict.get(direction, [DUMMY_FRAME])
        interval = self.frame_intervals.get(self.state, settings.DEFAULT_FRAME_INTERVAL)

        if not frames:
            frames = [DUMMY_FRAME]

        if self.state == "death":
            self.frame_timer += 1
            if self.frame_timer >= interval and self.frame_index < len(frames) - 1:
                self.frame_timer -= interval
                if self.frame_timer < 0:
                    self.frame_timer = 0
                self.frame_index += 1
            self.image = frames[min(self.frame_index, len(frames) - 1)]
            return

        self.frame_timer += 1
        if self.frame_timer >= interval:
            self.frame_timer -= interval
            if self.frame_timer < 0:
                self.frame_timer = 0
            self.frame_index += 1
            if self.frame_index >= len(frames):
                self.frame_index = 0
                if self.state.startswith("attack"):
                    self.state = "idle"
                    self.is_attacking = False
                    self._reset_current_attack()
                elif self.state == "take hit":
                    self.state = "idle"
                    self.is_attacking = False

        self.frame_index = min(self.frame_index, len(frames) - 1)
        self.image = frames[self.frame_index]

    def draw(self) -> None:
        for effect in self.active_effects:
            if not effect.frames:
                continue
            frame_list = effect.frames
            texture = frame_list[min(effect.frame_index, len(frame_list) - 1)]
            dest_effect = XYWH(effect.x, effect.y, effect.width, effect.height)
            arcade.draw_texture_rect(texture, dest_effect)

        if self.image:
            dest_rect = XYWH(self.x, self.y, self.w, self.h)
            arcade.draw_texture_rect(self.image, dest_rect)
