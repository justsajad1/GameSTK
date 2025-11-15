"""Game window and UI flows."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional

import arcade
from arcade.types.rect import XYWH

try:  # Python 3.11+ ships StrEnum; keep a fallback for older interpreters.
    from enum import StrEnum
except ImportError:  # pragma: no cover - legacy compatibility
    from enum import Enum

    class StrEnum(str, Enum):
        """Minimal StrEnum stand-in for older Python versions."""

        pass

try:  # Support both package and script-style imports.
    from . import core, settings  # type: ignore
except ImportError:  # pragma: no cover - script execution path
    import core  # type: ignore
    import settings  # type: ignore

SoundMap = Dict[str, Optional[arcade.Sound]]


class GameMode(StrEnum):
    DAY = "day"
    NIGHT = "night"


class GameState(StrEnum):
    MENU = "menu"
    OPTIONS = "options"
    CHARACTER_SELECT = "character_select"
    PLAYING = "playing"
    ROUND_OVER = "round_over"
    MATCH_OVER = "match_over"
    PAUSED = "paused"


MODE_DISPLAY_LABELS = {
    GameMode.DAY: "TAG",
    GameMode.NIGHT: "NACHT",
}


@dataclass(frozen=True)
class ButtonDescriptor:
    identifier: str
    label: str
    center_x: float
    center_y: float
    width: float
    height: float

    def contains(self, x: float, y: float) -> bool:
        half_w = self.width / 2
        half_h = self.height / 2
        return (
            self.center_x - half_w <= x <= self.center_x + half_w
            and self.center_y - half_h <= y <= self.center_y + half_h
        )


def _load_sounds() -> SoundMap:
    """Load all configured sounds and return them keyed by identifier."""

    sounds: SoundMap = {}
    for key, configured_path in settings.SOUND_FILES.items():
        file_path = settings.ensure_path(configured_path)
        if file_path.is_file():
            print(f"{file_path.name} found")
            # Stream long-form tracks (e.g. background music) to avoid decoding issues on some systems.
            stream = key == "music"
            sounds[key] = arcade.load_sound(str(file_path), streaming=stream)
        else:
            print(f"{file_path.name} missing")
            sounds[key] = None

    return sounds


class StickmanFighterGame(arcade.Window):
    """Main game window managing menu, match flow, and rendering."""

    CONTROL_ACTIONS = ("left", "right", "jump", "punch", "kick", "special")

    def __init__(self) -> None:
        super().__init__(
            settings.WIDTH,
            settings.HEIGHT,
            settings.WINDOW_TITLE,
            resizable=False,
            update_rate=1 / settings.FPS,
        )

        self.state = GameState.MENU
        self.mode: Optional[GameMode] = None
        self.round_restart_timer = 0
        self.match_restart_timer = 0
        self.camera_offset = 0.0
        self.round_time_remaining = float(settings.ROUND_TIME_LIMIT)
        self.round_message = ""

        self.background: Optional[arcade.Texture] = None
        self.menu_background: Optional[arcade.Texture] = self._load_menu_background()
        self.sounds = _load_sounds()
        self.music_player: Optional[object] = None
        self._start_music_loop()
        self._background_cache: Dict[GameMode, Optional[arcade.Texture]] = {}

        default_controls = {player: dict(bindings) for player, bindings in settings.PLAYER_CONTROLS.items()}
        configured = getattr(settings, "PLAYER_CONTROLS", {})
        self.controls1 = self._normalize_player_controls(
            configured.get("player1", {}),
            default_controls.get("player1", {}),
        )
        self.controls2 = self._normalize_player_controls(
            configured.get("player2", {}),
            default_controls.get("player2", {}),
        )

        self.fighter_catalog = settings.FIGHTERS
        self.fighter_keys = list(self.fighter_catalog.keys())
        self.player_selection = dict(settings.DEFAULT_FIGHTER_SELECTION)

        self.fighter1 = self._create_fighter("player1")
        self.fighter2 = self._create_fighter("player2")

        self.keys: Dict[int, bool] = {}
        self.winner: Optional[str] = None
        self.score1 = 0
        self.score2 = 0
        self._text_objects: Dict[str, arcade.Text] = {}
        self._key_press_handlers: Dict[GameState, Callable[[int], bool]] = {
            GameState.MENU: self._handle_key_press_menu,
            GameState.OPTIONS: self._handle_key_press_options,
            GameState.CHARACTER_SELECT: self._handle_key_press_character_select,
            GameState.ROUND_OVER: self._handle_key_press_round_over,
            GameState.MATCH_OVER: self._handle_key_press_match_over,
            GameState.PAUSED: self._handle_key_press_paused,
            GameState.PLAYING: self._handle_key_press_playing,
        }

    def _ensure_mode(self) -> GameMode:
        """Return the currently selected mode, defaulting to night if unset."""

        if self.mode is None:
            self.mode = GameMode.NIGHT
        return self.mode

    def _normalize_player_controls(
        self,
        configured: Mapping[str, int],
        defaults: Mapping[str, int],
    ) -> Dict[str, int]:
        normalized: Dict[str, int] = {}
        used_keys: Dict[int, str] = {}
        default_sequence = [defaults[action] for action in self.CONTROL_ACTIONS]

        for action in self.CONTROL_ACTIONS:
            desired = configured.get(action, defaults[action])
            candidates = [desired] + default_sequence
            chosen = desired
            for candidate in candidates:
                if candidate not in used_keys:
                    chosen = candidate
                    break
            normalized[action] = chosen
            used_keys[chosen] = action

        return normalized

    def _start_music_loop(self) -> None:
        """Begin background music playback if an asset is available."""

        if self.music_player:
            return

        music = self.sounds.get("music")
        if not music:
            return

        try:
            self.music_player = music.play(volume=0.3, loop=True)
        except TypeError:  # pragma: no cover - legacy fallback
            self.music_player = music.play(volume=0.3)

    def _stop_music(self) -> None:
        """Stop any running background music."""

        if not self.music_player:
            return

        pause = getattr(self.music_player, "pause", None)
        if callable(pause):
            pause()
        delete = getattr(self.music_player, "delete", None)
        if callable(delete):
            delete()
        self.music_player = None

    def pause_game(self) -> None:
        """Suspend gameplay while preserving the current round state."""

        if self.state is not GameState.PLAYING:
            return

        self.state = GameState.PAUSED
        self.keys.clear()

    def resume_game(self) -> None:
        """Return to active gameplay from a paused state."""

        if self.state is not GameState.PAUSED:
            return

        self.state = GameState.PLAYING

    def _handle_round_timeout(self) -> None:
        """Resolve the round outcome when the time limit expires."""

        if self.state is not GameState.PLAYING:
            return

        self.round_time_remaining = 0.0
        health1 = max(0, self.fighter1.health)
        health2 = max(0, self.fighter2.health)
        if health1 == health2:
            self._finish_draw_round(reason="timeout")
            return

        round_winner = self.fighter1 if health1 > health2 else self.fighter2
        self.finish_round(round_winner, reason="timeout")

    def _finish_draw_round(self, *, reason: str = "timeout") -> None:
        """Resolve round flow when neither player wins."""

        both_on_match_point = (
            self.score1 == settings.WINS_TO_MATCH - 1 and self.score2 == settings.WINS_TO_MATCH - 1
        )
        message_prefix = "Zeit abgelaufen! " if reason == "timeout" else ""

        if both_on_match_point:
            self.round_message = f"{message_prefix}Unentschieden – keine Punkte vergeben."
        else:
            self.score1 += 1
            self.score2 += 1
            self.round_message = f"{message_prefix}Unentschieden – beide Spieler erhalten einen Punkt."

        self.round_time_remaining = max(0.0, self.round_time_remaining)

        if not both_on_match_point and (
            self.score1 >= settings.WINS_TO_MATCH or self.score2 >= settings.WINS_TO_MATCH
        ):
            self.state = GameState.MATCH_OVER
            if self.score1 == self.score2:
                self.winner = "Gleichstand"
            else:
                self.winner = self.fighter1.name if self.score1 > self.score2 else self.fighter2.name
            self.match_restart_timer = int(4 * settings.FPS)
            return

        self.state = GameState.ROUND_OVER
        self.winner = None
        self.round_restart_timer = int(3 * settings.FPS)

    def _resolve_player_overlap(self) -> None:
        """Prevent fighters from clipping through each other by enforcing minimum spacing."""

        fighter1 = self.fighter1
        fighter2 = self.fighter2

        if fighter1.is_dead or fighter2.is_dead:
            return

        if abs(fighter1.y - fighter2.y) > settings.VERTICAL_SEPARATION_THRESHOLD:
            return

        left, right = (fighter1, fighter2) if fighter1.x <= fighter2.x else (fighter2, fighter1)
        collision_span = left.collision_half_width + right.collision_half_width
        min_distance = max(settings.MIN_PLAYER_DISTANCE, collision_span)
        current_distance = right.x - left.x

        if current_distance >= min_distance - settings.TOUCH_TOLERANCE:
            return

        target_distance = min_distance
        overlap = target_distance - current_distance
        if overlap <= 0:
            return

        left_min = left.w / 2
        right_max = settings.WIDTH - right.w / 2
        left_available = max(0.0, left.x - left_min)
        right_available = max(0.0, right_max - right.x)

        half_overlap = overlap / 2
        left_shift = min(half_overlap, left_available)
        right_shift = min(half_overlap, right_available)

        remaining = overlap - (left_shift + right_shift)

        if remaining > 0 and left_available > left_shift:
            extra_left = min(remaining, left_available - left_shift)
            left_shift += extra_left
            remaining -= extra_left

        if remaining > 0 and right_available > right_shift:
            extra_right = min(remaining, right_available - right_shift)
            right_shift += extra_right
            remaining -= extra_right

        left.x -= left_shift
        right.x += right_shift

        for fighter in (left, right):
            half_width = fighter.w / 2
            fighter.x = max(half_width, min(settings.WIDTH - half_width, fighter.x))

    def _create_fighter(self, slot: str) -> core.Fighter:
        """Instantiate a fighter for the given player slot based on the current selection."""

        selection = self.player_selection.get(slot)
        if selection not in self.fighter_catalog:
            fallback = next(iter(self.fighter_catalog))
            self.player_selection[slot] = fallback
            selection = fallback

        config = self.fighter_catalog[selection]
        controls = self.controls1 if slot == "player1" else self.controls2
        spawn_x = 400 if slot == "player1" else 900
        action_files = config.get("action_files", {})
        frame_size = config.get("frame_size", settings.FRAME_SIZE)
        sprite_dir = settings.ensure_path(config["sprite_dir"])
        display_name = config.get("name", selection.title())
        return core.Fighter(
            spawn_x,
            settings.GROUND_Y,
            controls,
            display_name,
            sprite_dir,
            self.sounds,
            action_files=action_files,
            attack_specs=config.get("attack_specs"),
            attack_effects=config.get("attack_effects", {}),
            frame_size=frame_size,
            min_scale=config.get("min_scale", settings.MIN_FIGHTER_SCALE),
            max_scale=config.get("max_scale", settings.MAX_FIGHTER_SCALE),
        )

    def _refresh_fighter(self, slot: str) -> None:
        if slot == "player1":
            self.fighter1 = self._create_fighter(slot)
        else:
            self.fighter2 = self._create_fighter(slot)

    def _refresh_fighters(self) -> None:
        self._refresh_fighter("player1")
        self._refresh_fighter("player2")

    def _draw_text(
        self,
        key: str,
        text: str,
        x: float,
        y: float,
        color: tuple[int, int, int] | tuple[int, int, int, int],
        font_size: int,
        *,
        anchor_x: str = "left",
        anchor_y: str = "baseline",
        bold: bool = False,
    ) -> None:
        text_obj = self._text_objects.get(key)
        if text_obj is None:
            text_obj = arcade.Text(
                text,
                x,
                y,
                color,
                font_size,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                bold=bold,
            )
            self._text_objects[key] = text_obj
        else:
            text_obj.text = text
            text_obj.x = x
            text_obj.y = y
            text_obj.color = color
            text_obj.font_size = font_size
            text_obj.anchor_x = anchor_x
            text_obj.anchor_y = anchor_y
            text_obj.bold = bold
        text_obj.draw()

    def _character_select_layout(self) -> dict[str, object]:
        """Return layout metrics for rendering and hit testing the character select screen."""

        row_gap = 70
        cell_height = 56
        top_margin = 200
        top_y = settings.HEIGHT - top_margin

        rows: list[dict[str, object]] = []
        for index, key in enumerate(self.fighter_keys):
            config = self.fighter_catalog[key]
            display_name = config.get("name", key.title())
            y_center = top_y - index * row_gap
            rows.append(
                {
                    "key": key,
                    "name": display_name,
                    "y_center": y_center,
                    "y0": y_center - cell_height / 2,
                    "y1": y_center + cell_height / 2,
                }
            )

        column_width = 320
        column_gap = 80
        left_x = settings.WIDTH / 2 - column_width - column_gap / 2
        right_x = settings.WIDTH / 2 + column_gap / 2

        return {
            "rows": rows,
            "column_width": column_width,
            "left_x": left_x,
            "right_x": right_x,
        }

    def _draw_character_select(self) -> None:
        layout = self._character_select_layout()
        left_x = layout["left_x"]  # type: ignore[assignment]
        right_x = layout["right_x"]  # type: ignore[assignment]
        column_width = layout["column_width"]  # type: ignore[assignment]

        self._draw_menu_background((18, 18, 18))
        self._draw_title_banner("char_select_title", "Charakter Auswahl", settings.HEIGHT - 120, 44)

        header_y = settings.HEIGHT - 160
        for label, center_x in [
            ("Spieler 1", float(left_x) + column_width / 2),
            ("Spieler 2", float(right_x) + column_width / 2),
        ]:
            self._draw_text(
                f"char_select_header_{label}",
                label,
                center_x,
                header_y,
                (255, 245, 230),
                24,
                anchor_x="center",
                bold=True,
            )

        for row in layout["rows"]:  # type: ignore[assignment]
            row_key = row["key"]
            y0 = row["y0"]
            y1 = row["y1"]
            y_center = row["y_center"]
            name = row["name"]
            height = y1 - y0
            for player, x0 in (("player1", left_x), ("player2", right_x)):
                selected = self.player_selection[player] == row_key
                self._draw_menu_button(
                    center_x=x0 + column_width / 2,
                    center_y=y_center,
                    width=column_width,
                    height=height,
                    label=str(name),
                    identifier=f"char_select_row_{row_key}_{player}",
                    drop_shadow=False,
                    font_size=20,
                    highlight=selected,
                )

    def _load_menu_background(self) -> Optional[arcade.Texture]:
        """Load the static menu background texture if available."""

        candidates = ("backroundmenu.jpg", "backgroundmenu.jpg")
        for filename in candidates:
            background_path = settings.asset_path("image_files", filename)
            if background_path.is_file():
                print(f"Loaded menu background: {filename}")
                return arcade.load_texture(str(background_path))

        print("Menu background image not found in assets/image_files.")
        return None

    def _draw_menu_background(self, fallback_color=(20, 20, 20)) -> None:
        """Render the shared menu background texture or fall back to a flat color."""

        if self.menu_background:
            menu_bg_rect = XYWH(settings.WIDTH / 2, settings.HEIGHT / 2, settings.WIDTH, settings.HEIGHT)
            arcade.draw_texture_rect(self.menu_background, menu_bg_rect)
        else:
            arcade.draw_lrbt_rectangle_filled(0, settings.WIDTH, 0, settings.HEIGHT, fallback_color)

    def _draw_title_banner(self, key: str, text: str, y: float, font_size: int = 48) -> None:
        """Draw a stylized title banner with glow, outline, and drop shadow text."""

        center_x = settings.WIDTH / 2
        try:
            measurement = arcade.Text(
                text,
                start_x=0,
                start_y=0,
                color=settings.WHITE,
                font_size=font_size,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )
        except TypeError:
            measurement = arcade.Text(
                text,
                0,
                0,
                settings.WHITE,
                font_size,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )
        text_width = getattr(
            measurement,
            "content_width",
            getattr(measurement, "width", font_size * max(1, len(text)) * 0.6),
        )
        accent_half = min(
            settings.WIDTH * 0.35,
            max(text_width / 2 + 30, font_size * 2),
        )
        accent_thickness = max(4, font_size * 0.1)
        accent_y0 = y - font_size * 0.9
        accent_y1 = accent_y0 + accent_thickness
        accent_color = (255, 210, 120, 180)
        glow_color = (80, 60, 35, 120)

        arcade.draw_lrbt_rectangle_filled(
            center_x - accent_half,
            center_x + accent_half,
            accent_y0,
            accent_y1,
            glow_color,
        )
        arcade.draw_lrbt_rectangle_filled(
            center_x - accent_half + 6,
            center_x + accent_half - 6,
            accent_y0 + 2,
            accent_y1 - 2,
            accent_color,
        )

        self._draw_text(
            f"{key}_shadow",
            text,
            center_x + 3,
            y - 3,
            (0, 0, 0, 220),
            font_size,
            anchor_x="center",
            bold=True,
        )
        self._draw_text(
            f"{key}_main",
            text,
            center_x,
            y,
            (255, 245, 230),
            font_size,
            anchor_x="center",
            bold=True,
        )

    def _draw_menu_button(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        label: str,
        identifier: str,
        *,
        highlight: bool = False,
        drop_shadow: bool = True,
        font_size: int = 28,
        colors: Optional[Mapping[str, tuple[int, int, int]]] = None,
    ) -> None:
        """Render a stylized menu button with optional highlighting and custom colors."""

        def draw_rect(cx: float, cy: float, w: float, h: float, color: tuple[int, ...]) -> None:
            half_w = w / 2
            half_h = h / 2
            arcade.draw_lrbt_rectangle_filled(cx - half_w, cx + half_w, cy - half_h, cy + half_h, color)

        def draw_rect_outline(
            cx: float,
            cy: float,
            w: float,
            h: float,
            color: tuple[int, ...],
            border_width: float,
        ) -> None:
            half_w = w / 2
            half_h = h / 2
            arcade.draw_lrbt_rectangle_outline(
                cx - half_w,
                cx + half_w,
                cy - half_h,
                cy + half_h,
                color,
                border_width,
            )

        palette = {
            "base": (45, 45, 64),
            "glow": (70, 70, 100),
            "accent": (250, 210, 120),
            "text": (255, 245, 230),
        }
        if highlight and colors is None:
            palette.update(
                {
                    "base": (120, 90, 45),
                    "glow": (175, 125, 60),
                    "accent": (255, 232, 170),
                    "text": (255, 245, 230),
                }
            )
        if colors:
            palette.update(dict(colors))

        shadow_offset = 8
        if drop_shadow:
            draw_rect(center_x + shadow_offset, center_y - shadow_offset, width, height, (0, 0, 0, 140))

        draw_rect(center_x, center_y, width, height, palette["base"])
        draw_rect(center_x, center_y + height * 0.2, width, height * 0.5, palette["glow"])

        accent_height = max(6, height * 0.08)
        accent_rgba = palette["accent"] + (160,)
        draw_rect(center_x, center_y - height / 2 + accent_height / 2, width - 24, accent_height, accent_rgba)

        inner_margin = 12
        draw_rect_outline(center_x, center_y, width, height, (230, 230, 230), 3)
        draw_rect_outline(center_x, center_y, width - inner_margin, height - inner_margin, palette["accent"], 2)

        self._draw_text(
            f"{identifier}_label",
            label,
            center_x,
            center_y,
            palette.get("text", settings.WHITE),
            font_size,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )


    def load_background(self, mode: GameMode) -> None:
        if mode in self._background_cache:
            self.background = self._background_cache[mode]
            return

        bg_filename = "arena_day.jpg" if mode is GameMode.DAY else "arena_night.jpg"
        background_path = settings.asset_path("image_files", bg_filename)
        if background_path.is_file():
            texture = arcade.load_texture(str(background_path))
            self._background_cache[mode] = texture
            self.background = texture
            print(f"Loaded {mode.value} background: {bg_filename}")
        else:
            self._background_cache[mode] = None
            self.background = None
            print("Background image not found:", background_path)

    def start_match(self) -> None:
        """Called after the player chooses mode on the menu."""

        self._refresh_fighters()
        self.score1 = 0
        self.score2 = 0
        self.winner = None
        current_mode = self._ensure_mode()
        self.load_background(current_mode)
        self.start_round()

    def start_round(self) -> None:
        self.fighter1.reset()
        self.fighter2.reset()
        self.state = GameState.PLAYING
        self.winner = None
        self.round_restart_timer = 0
        self.round_time_remaining = float(settings.ROUND_TIME_LIMIT)
        self.round_message = ""

    def finish_round(self, round_winner: core.Fighter, *, reason: str = "knockout") -> None:
        """Update scores, move to next round or mark the match finished."""
        self.round_time_remaining = max(0.0, self.round_time_remaining)
        if round_winner is self.fighter1:
            self.score1 += 1
        else:
            self.score2 += 1

        winner_name = round_winner.name
        if reason == "timeout":
            self.round_message = f"{winner_name} gewinnt durch Zeitablauf!"
        else:
            self.round_message = f"{winner_name} hat die Runde gewonnen!"

        if self.score1 >= settings.WINS_TO_MATCH or self.score2 >= settings.WINS_TO_MATCH:
            self.state = GameState.MATCH_OVER
            self.winner = self.fighter1.name if self.score1 > self.score2 else self.fighter2.name
            self.match_restart_timer = int(4 * settings.FPS)
        else:
            self.state = GameState.ROUND_OVER
            self.winner = winner_name
            self.round_restart_timer = int(3 * settings.FPS)

    def restart_round(self) -> None:
        self.start_round()

    def back_to_menu(self) -> None:
        self.state = GameState.MENU
        self.mode = None
        self.winner = None
        self.background = None

    def draw_hud(self) -> None:
        arcade.draw_lrbt_rectangle_filled(
            left=0,
            right=settings.WIDTH,
            bottom=settings.HEIGHT - 80,
            top=settings.HEIGHT,
            color=settings.HUD_BG,
        )

        bar_w = 400
        top_y = settings.HEIGHT - 40
        pad = 20

        x1_left = pad
        x1_right = pad + bar_w
        arcade.draw_lrbt_rectangle_filled(
            left=x1_left,
            right=x1_right,
            bottom=top_y - 10,
            top=top_y + 10,
            color=settings.RED,
        )
        f1_green_w = (max(0, self.fighter1.health) / 100) * bar_w
        arcade.draw_lrbt_rectangle_filled(
            left=x1_left,
            right=x1_left + f1_green_w,
            bottom=top_y - 10,
            top=top_y + 10,
            color=settings.GREEN,
        )
        self._draw_text("hud_player1_name", f"{self.fighter1.name}", x1_left, top_y + 16, settings.WHITE, 14)

        x2_right = settings.WIDTH - pad
        x2_left = settings.WIDTH - pad - bar_w
        arcade.draw_lrbt_rectangle_filled(
            left=x2_left,
            right=x2_right,
            bottom=top_y - 10,
            top=top_y + 10,
            color=settings.RED,
        )
        f2_green_w = (max(0, self.fighter2.health) / 100) * bar_w
        arcade.draw_lrbt_rectangle_filled(
            left=x2_right - f2_green_w,
            right=x2_right,
            bottom=top_y - 10,
            top=top_y + 10,
            color=settings.GREEN,
        )
        self._draw_text(
            "hud_player2_name",
            f"{self.fighter2.name}",
            x2_right,
            top_y + 16,
            settings.WHITE,
            14,
            anchor_x="right",
        )

        pip_r = 8
        for i in range(settings.WINS_TO_MATCH):
            cx = x1_left + i * (pip_r * 2 + 6)
            cy = settings.HEIGHT - 70
            color = settings.WHITE if i < self.score1 else (150, 150, 150)
            arcade.draw_circle_filled(cx, cy, pip_r, color)
        for i in range(settings.WINS_TO_MATCH):
            cx = x2_right - i * (pip_r * 2 + 6)
            cy = settings.HEIGHT - 70
            color = settings.WHITE if i < self.score2 else (150, 150, 150)
            arcade.draw_circle_filled(cx, cy, pip_r, color)

        remaining = max(0.0, self.round_time_remaining)
        seconds_left = max(0, int(math.ceil(remaining)))
        timer_text = f"{seconds_left}"
        self._draw_text(
            "hud_timer",
            timer_text,
            settings.WIDTH / 2,
            settings.HEIGHT - 38,
            settings.WHITE,
            28,
            anchor_x="center",
            bold=True,
        )

        if self.mode:
            mode_text = MODE_DISPLAY_LABELS.get(self.mode, "")
            if mode_text:
                self._draw_text(
                    "hud_mode",
                    mode_text,
                    settings.WIDTH / 2,
                    settings.HEIGHT - 60,
                    settings.WHITE,
                    14,
                    anchor_x="center",
                )

    def on_draw(self) -> None:
        self.clear()
        self.camera_offset += 0.5

        if self.state is GameState.MENU:
            self._draw_menu()
            return

        if self.state is GameState.OPTIONS:
            self._draw_options()
            return

        if self.state is GameState.CHARACTER_SELECT:
            self._draw_character_select()
            return

        if self.background:
            offset_x = 20 * math.sin(self.camera_offset / 60)
            cx = settings.WIDTH // 2 + offset_x
            cy = settings.HEIGHT // 2
            bg_rect = XYWH(cx, cy, settings.WIDTH, settings.HEIGHT)
            arcade.draw_texture_rect(self.background, bg_rect)
        else:
            arcade.draw_lrbt_rectangle_filled(0, settings.WIDTH, 0, 200, settings.GROUND)

        self.fighter1.draw()
        self.fighter2.draw()
        self.draw_hud()

        if self.state is GameState.ROUND_OVER:
            message = self.round_message or "Runde beendet!"
            self._draw_text(
                "round_over_title",
                message,
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 40,
                settings.WHITE,
                36,
                anchor_x="center",
                bold=True,
            )
            self._draw_text(
                "round_over_hint",
                "Naechste Runde...",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 5,
                settings.WHITE,
                18,
                anchor_x="center",
            )
        elif self.state is GameState.MATCH_OVER:
            self._draw_text(
                "match_over_title",
                f"{self.winner} GEWINNT DAS DUELL!",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 40,
                settings.WHITE,
                40,
                anchor_x="center",
                bold=True,
            )
            self._draw_text(
                "match_over_hint",
                "Zurueck zum Menue...  (R = Wiederspielen, M = Menue)",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 5,
                settings.WHITE,
                18,
                anchor_x="center",
            )
        elif self.state is GameState.PAUSED:
            arcade.draw_lrbt_rectangle_filled(
                0,
                settings.WIDTH,
                0,
                settings.HEIGHT,
                (0, 0, 0, 160),
            )
            self._draw_text(
                "paused_title",
                "PAUSE",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 60,
                settings.WHITE,
                48,
                anchor_x="center",
                bold=True,
            )
            self._draw_text(
                "paused_resume_hint",
                "ESC oder P = Fortsetzen",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 10,
                settings.WHITE,
                22,
                anchor_x="center",
            )
            self._draw_text(
                "paused_restart_hint",
                "R = Runde neu starten",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 30,
                settings.WHITE,
                18,
                anchor_x="center",
            )
            self._draw_text(
                "paused_menu_hint",
                "M = Hauptmenue",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 60,
                settings.WHITE,
                18,
                anchor_x="center",
            )

    def on_update(self, delta_time: float) -> None:  # noqa: D401 - Arcade signature
        if self.state is GameState.PLAYING:
            self.fighter1.update(self.keys, self.fighter2)
            self.fighter2.update(self.keys, self.fighter1)
            self._resolve_player_overlap()

            if self.fighter1.is_dead or self.fighter2.is_dead:
                death_ready = True
                if self.fighter1.is_dead and not getattr(self.fighter1, "death_animation_done", False):
                    death_ready = False
                if self.fighter2.is_dead and not getattr(self.fighter2, "death_animation_done", False):
                    death_ready = False

                if death_ready:
                    round_winner = self.fighter2 if self.fighter1.is_dead else self.fighter1
                    self.finish_round(round_winner)
                    return

            self.round_time_remaining = max(0.0, self.round_time_remaining - delta_time)
            if self.round_time_remaining <= 0:
                self._handle_round_timeout()
            return

        if self.state is GameState.ROUND_OVER and self.round_restart_timer > 0:
            self.round_restart_timer -= 1
            if self.round_restart_timer <= 0:
                self.restart_round()
        elif self.state is GameState.MATCH_OVER and self.match_restart_timer > 0:
            self.match_restart_timer -= 1
            if self.match_restart_timer <= 0:
                self.back_to_menu()

    def on_key_press(self, symbol: int, modifiers: int) -> None:  # noqa: D401 - Arcade signature
        if symbol == settings.KEY.ESCAPE:
            self._handle_escape_key()
            return

        handler = self._key_press_handlers.get(self.state)
        if handler and handler(symbol):
            return

        if self.state is GameState.PLAYING:
            self.keys[symbol] = True

    def on_key_release(self, symbol: int, modifiers: int) -> None:  # noqa: D401 - Arcade signature
        if symbol in self.keys:
            self.keys[symbol] = False

    def _enter_keys(self) -> tuple[int, int]:
        return (settings.KEY.ENTER, getattr(settings.KEY, "RETURN", settings.KEY.ENTER))

    def _handle_escape_key(self) -> None:
        if self.state is GameState.MENU:
            self._stop_music()
            arcade.close_window()
        elif self.state in {GameState.OPTIONS, GameState.CHARACTER_SELECT}:
            self.state = GameState.MENU
        elif self.state is GameState.PLAYING:
            self.pause_game()
        elif self.state is GameState.PAUSED:
            self.resume_game()
        else:
            self.back_to_menu()

    def _handle_key_press_paused(self, symbol: int) -> bool:
        enter_keys = self._enter_keys()
        if symbol in enter_keys or symbol == settings.KEY.P:
            self.resume_game()
            return True
        if symbol == settings.KEY.R:
            self.restart_round()
            return True
        if symbol == settings.KEY.M:
            self.back_to_menu()
            return True
        return False

    def _handle_key_press_menu(self, symbol: int) -> bool:
        enter_keys = self._enter_keys()
        if symbol in enter_keys:
            self._ensure_mode()
            self.start_match()
            return True
        if symbol == settings.KEY.C:
            self.state = GameState.CHARACTER_SELECT
            return True
        if symbol == settings.KEY.O:
            self.state = GameState.OPTIONS
            return True
        if symbol == settings.KEY.X:
            self._stop_music()
            arcade.close_window()
            return True
        return False

    def _handle_key_press_character_select(self, symbol: int) -> bool:
        enter_keys = self._enter_keys()
        if symbol in enter_keys or symbol == settings.KEY.M:
            self.state = GameState.MENU
            return True
        return False

    def _handle_key_press_options(self, symbol: int) -> bool:
        if symbol == settings.KEY.M:
            self.state = GameState.MENU
            return True
        if symbol == settings.KEY.D:
            self.mode = GameMode.DAY
            return True
        if symbol == settings.KEY.N:
            self.mode = GameMode.NIGHT
            return True
        return False

    def _handle_key_press_round_over(self, symbol: int) -> bool:
        if symbol == settings.KEY.R:
            self.restart_round()
            return True
        return False

    def _handle_key_press_match_over(self, symbol: int) -> bool:
        if symbol == settings.KEY.R:
            self.start_match()
            return True
        if symbol == settings.KEY.M:
            self.back_to_menu()
            return True
        return False

    def _handle_key_press_playing(self, symbol: int) -> bool:
        if symbol == settings.KEY.P:
            self.pause_game()
            return True
        return False

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:  # noqa: D401
        if self.state is GameState.MENU:
            for spec, action in self._menu_buttons():
                if not spec.contains(x, y):
                    continue
                if action == "start":
                    self._ensure_mode()
                    self.start_match()
                elif action == "characters":
                    self.state = GameState.CHARACTER_SELECT
                elif action == "options":
                    self.state = GameState.OPTIONS
                elif action == "exit":
                    self._stop_music()
                    arcade.close_window()
                return

        if self.state is GameState.CHARACTER_SELECT:
            layout = self._character_select_layout()
            left_x = layout["left_x"]  # type: ignore[assignment]
            right_x = layout["right_x"]  # type: ignore[assignment]
            column_width = layout["column_width"]  # type: ignore[assignment]

            for row in layout["rows"]:  # type: ignore[assignment]
                y0 = row["y0"]
                y1 = row["y1"]
                if y0 <= y <= y1:
                    if left_x <= x <= left_x + column_width:
                        self.player_selection["player1"] = row["key"]
                        self._refresh_fighter("player1")
                        return
                    if right_x <= x <= right_x + column_width:
                        self.player_selection["player2"] = row["key"]
                        self._refresh_fighter("player2")
                        return
            return

        if self.state is GameState.OPTIONS:
            for spec, mode_value in self._mode_buttons():
                if spec.contains(x, y):
                    self.mode = mode_value
                    return

    def _menu_buttons(self) -> list[tuple[ButtonDescriptor, str]]:
        """Return layout + action pairs for the main menu buttons."""

        btn_w = 360
        btn_h = 80
        gap = 30
        start_y = settings.HEIGHT / 2 + btn_h + gap
        center_x = settings.WIDTH / 2

        actions = [
            ("STARTEN", "start"),
            ("CHARAKTERE", "characters"),
            ("OPTIONEN", "options"),
            ("VERLASSEN", "exit"),
        ]
        specs: list[tuple[ButtonDescriptor, str]] = []
        for index, (label, action) in enumerate(actions):
            center_y = start_y - index * (btn_h + gap)
            spec = ButtonDescriptor(
                identifier=f"menu_button_{index}",
                label=label,
                center_x=center_x,
                center_y=center_y,
                width=btn_w,
                height=btn_h,
            )
            specs.append((spec, action))
        return specs

    def _mode_buttons(self) -> list[tuple[ButtonDescriptor, GameMode]]:
        """Return layout + mode pairs for the options screen."""

        btn_w = 300
        btn_h = 100
        gap = 80
        y_center = settings.HEIGHT / 2
        day_x = settings.WIDTH / 2 - gap / 2 - btn_w
        night_x = settings.WIDTH / 2 + gap / 2

        specs: list[tuple[ButtonDescriptor, GameMode]] = []
        for mode_value, offset_x in (
            (GameMode.DAY, day_x),
            (GameMode.NIGHT, night_x),
        ):
            spec = ButtonDescriptor(
                identifier=f"options_button_{mode_value.value}",
                label=MODE_DISPLAY_LABELS[mode_value],
                center_x=offset_x + btn_w / 2,
                center_y=y_center,
                width=btn_w,
                height=btn_h,
            )
            specs.append((spec, mode_value))
        return specs

    def _draw_menu(self) -> None:
        self._draw_menu_background((20, 20, 20))
        self._draw_title_banner("menu_title", settings.WINDOW_TITLE, settings.HEIGHT - 140, 48)

        for spec, _action in self._menu_buttons():
            self._draw_menu_button(
                center_x=spec.center_x,
                center_y=spec.center_y,
                width=spec.width,
                height=spec.height,
                label=spec.label,
                identifier=spec.identifier,
            )

        current_mode = MODE_DISPLAY_LABELS.get(self.mode, "NICHT GEWAHLT")
        info_lines = [
            (f"Modus: {current_mode}", 16, (200, 200, 200)),
            (f"Spieler 1: {self.fighter1.name}", 16, (200, 200, 200)),
            (f"Spieler 2: {self.fighter2.name}", 16, (200, 200, 200)),
        ]
        info_x = 30
        info_base_y = 40
        line_gap = 22
        for index, (text, size, color) in enumerate(info_lines):
            y = info_base_y + index * line_gap
            self._draw_text(
                f"menu_info_{index}",
                text,
                info_x,
                y,
                color,
                size,
                anchor_x="left",
            )

    def _draw_options(self) -> None:
        self._draw_menu_background((15, 15, 15))
        self._draw_title_banner("options_title", "Optionen", settings.HEIGHT - 120, 44)

        for spec, mode_value in self._mode_buttons():
            selected = self.mode is mode_value
            self._draw_menu_button(
                center_x=spec.center_x,
                center_y=spec.center_y,
                width=spec.width,
                height=spec.height,
                label=spec.label,
                identifier=spec.identifier,
                highlight=selected,
            )

    def on_close(self) -> None:
        self._stop_music()
        super().on_close()
