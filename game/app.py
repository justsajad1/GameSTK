"""Game window and UI flows."""

from __future__ import annotations

from typing import Dict, Optional

import arcade
from arcade.types.rect import XYWH
import math

try:  # Support both package and script-style imports.
    from . import core, settings  # type: ignore
except ImportError:  # pragma: no cover - script execution path
    import core  # type: ignore
    import settings  # type: ignore

SoundMap = Dict[str, Optional[arcade.Sound]]


def _load_sounds() -> SoundMap:
    """Load all configured sounds and return them keyed by identifier."""

    sounds: SoundMap = {}
    for key, configured_path in settings.SOUND_FILES.items():
        file_path = settings.ensure_path(configured_path)
        if file_path.is_file():
            print(f"{file_path.name} found")
            sounds[key] = arcade.load_sound(str(file_path))
        else:
            print(f"{file_path.name} missing")
            sounds[key] = None

    return sounds


class StickmanFighterGame(arcade.Window):
    """Main game window managing menu, match flow, and rendering."""

    def __init__(self) -> None:
        super().__init__(
            settings.WIDTH,
            settings.HEIGHT,
            settings.WINDOW_TITLE,
            resizable=False,
            update_rate=1 / settings.FPS,
        )

        self.state = "menu"  # "menu" | "options" | "playing" | "round_over" | "match_over"
        self.mode: Optional[str] = None  # "day" | "night"
        self.round_restart_timer = 0
        self.match_restart_timer = 0
        self.camera_offset = 0.0

        self.background: Optional[arcade.Texture] = None
        self.sounds = _load_sounds()
        self.music_player: Optional[object] = None
        self._start_music_loop()

        self.controls1 = {
            "left": settings.key_code("A"),
            "right": settings.key_code("D"),
            "jump": settings.key_code("W"),
            "punch": settings.key_code("F"),
            "kick": settings.key_code("G"),
        }
        self.controls2 = {
            "left": settings.key_code("LEFT"),
            "right": settings.key_code("RIGHT"),
            "jump": settings.key_code("UP"),
            "punch": settings.key_code("NUM_0", "NUMPAD_0", "KP_0", default=ord("0")),
            "kick": settings.key_code("NUM_1", "NUMPAD_1", "KP_1", default=ord("1")),
        }

        fighter1_cfg = settings.FIGHTER_OVERRIDES["fighter1"]
        fighter2_cfg = settings.FIGHTER_OVERRIDES["fighter2"]

        fighter1_path = settings.ensure_path(settings.FIGHTER_SPRITE_DIRS["fighter1"])
        fighter2_path = settings.ensure_path(settings.FIGHTER_SPRITE_DIRS["fighter2"])

        self.fighter1 = core.Fighter(
            400,
            150,
            self.controls1,
            "Tutankhamun",
            fighter1_path,
            self.sounds,
            action_files=fighter1_cfg["action_files"],
            frame_size=fighter1_cfg["frame_size"],
        )
        self.fighter2 = core.Fighter(
            900,
            150,
            self.controls2,
            "Charlemagne",
            fighter2_path,
            self.sounds,
            action_files=fighter2_cfg["action_files"],
            frame_size=fighter2_cfg["frame_size"],
        )

        self.keys: Dict[int, bool] = {}
        self.winner: Optional[str] = None
        self.score1 = 0
        self.score2 = 0

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

    def load_background(self, mode: str) -> None:
        bg_filename = "arena_day.jpg" if mode == "day" else "arena_night.jpg"
        background_path = settings.asset_path("image_files", bg_filename)
        if background_path.is_file():
            self.background = arcade.load_texture(str(background_path))
            print(f"Loaded {mode} background: {bg_filename}")
        else:
            self.background = None
            print("Background image not found:", background_path)

    def start_match(self) -> None:
        """Called after the player chooses mode on the menu."""

        self.score1 = 0
        self.score2 = 0
        self.winner = None
        if self.mode is None:
            self.mode = "night"
        self.load_background(self.mode)
        self.start_round()

    def start_round(self) -> None:
        self.fighter1.reset()
        self.fighter2.reset()
        self.state = "playing"
        self.winner = None
        self.round_restart_timer = 0

    def finish_round(self, round_winner: core.Fighter) -> None:
        """Update scores, move to next round or mark the match finished."""
        if round_winner is self.fighter1:
            self.score1 += 1
        else:
            self.score2 += 1

        if self.score1 >= settings.WINS_TO_MATCH or self.score2 >= settings.WINS_TO_MATCH:
            self.state = "match_over"
            self.winner = self.fighter1.name if self.score1 > self.score2 else self.fighter2.name
            self.match_restart_timer = int(4 * settings.FPS)
        else:
            self.state = "round_over"
            self.winner = round_winner.name
            self.round_restart_timer = int(3 * settings.FPS)

    def restart_round(self) -> None:
        self.start_round()

    def back_to_menu(self) -> None:
        self.state = "menu"
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
        arcade.draw_text(f"{self.fighter1.name}", x1_left, top_y + 16, settings.WHITE, 14)

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
        arcade.draw_text(f"{self.fighter2.name}", x2_right - 120, top_y + 16, settings.WHITE, 14)

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

        if self.mode:
            mode_text = {"day": "TAG", "night": "NACHT"}.get(self.mode, "")
            if mode_text:
                arcade.draw_text(
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

        if self.state == "menu":
            self._draw_menu()
            return

        if self.state == "options":
            self._draw_options()
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

        if self.state == "round_over":
            arcade.draw_text(
                f"{self.winner} hat die Runde gewonnen!",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 40,
                settings.WHITE,
                36,
                anchor_x="center",
                bold=True,
            )
            arcade.draw_text(
                "Naechste Runde...",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 5,
                settings.WHITE,
                18,
                anchor_x="center",
            )
        elif self.state == "match_over":
            arcade.draw_text(
                f"{self.winner} GEWINNT DAS DUELL!",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 + 40,
                settings.WHITE,
                40,
                anchor_x="center",
                bold=True,
            )
            arcade.draw_text(
                "Zurueck zum Menue...  (R = Wiederspielen, M = Menue)",
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - 5,
                settings.WHITE,
                18,
                anchor_x="center",
            )

    def on_update(self, delta_time: float) -> None:  # noqa: D401 - Arcade signature
        if self.state == "playing":
            self.fighter1.update(self.keys, self.fighter2)
            self.fighter2.update(self.keys, self.fighter1)

            if self.fighter1.is_dead or self.fighter2.is_dead:
                round_winner = self.fighter2 if self.fighter1.is_dead else self.fighter1
                self.finish_round(round_winner)
            return

        if self.state == "round_over" and self.round_restart_timer > 0:
            self.round_restart_timer -= 1
            if self.round_restart_timer <= 0:
                self.restart_round()
        elif self.state == "match_over" and self.match_restart_timer > 0:
            self.match_restart_timer -= 1
            if self.match_restart_timer <= 0:
                self.back_to_menu()

    def on_key_press(self, symbol: int, modifiers: int) -> None:  # noqa: D401 - Arcade signature
        if symbol == settings.KEY.ESCAPE:
            self._stop_music()
            arcade.close_window()
            return

        if self.state == "menu":
            if symbol in (settings.KEY.ENTER, getattr(settings.KEY, "RETURN", settings.KEY.ENTER)):
                if self.mode is None:
                    self.mode = "night"
                self.start_match()
            elif symbol == settings.KEY.O:
                self.state = "options"
            elif symbol == settings.KEY.X:
                self._stop_music()
                arcade.close_window()
            return

        if self.state == "options":
            if symbol == settings.KEY.M:
                self.state = "menu"
            elif symbol == settings.KEY.D:
                self.mode = "day"
                self.state = "menu"
            elif symbol == settings.KEY.N:
                self.mode = "night"
                self.state = "menu"
            return

        if self.state == "round_over":
            if symbol == settings.KEY.R:
                self.restart_round()
            return

        if self.state == "match_over":
            if symbol == settings.KEY.R:
                self.start_match()
            elif symbol == settings.KEY.M:
                self.back_to_menu()
            return

        self.keys[symbol] = True

    def on_key_release(self, symbol: int, modifiers: int) -> None:  # noqa: D401 - Arcade signature
        if symbol in self.keys:
            self.keys[symbol] = False

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:  # noqa: D401
        if self.state == "menu":
            btn_w = 360
            btn_h = 80
            gap = 30
            start_y = settings.HEIGHT / 2 + btn_h + gap

            buttons = [
                ("start", settings.WIDTH / 2 - btn_w / 2, start_y - btn_h / 2, btn_w, btn_h),
                ("options", settings.WIDTH / 2 - btn_w / 2, start_y - (btn_h + gap) - btn_h / 2, btn_w, btn_h),
                ("exit", settings.WIDTH / 2 - btn_w / 2, start_y - 2 * (btn_h + gap) - btn_h / 2, btn_w, btn_h),
            ]
            for name, bx, by, bw, bh in buttons:
                if bx <= x <= bx + bw and by <= y <= y + bh:
                    if name == "start":
                        if self.mode is None:
                            self.mode = "night"
                        self.start_match()
                    elif name == "options":
                        self.state = "options"
                    elif name == "exit":
                        self._stop_music()
                        arcade.close_window()
                    return

        if self.state == "options":
            btn_w = 300
            btn_h = 100
            gap = 80
            y0 = settings.HEIGHT / 2 - btn_h / 2
            day_x = settings.WIDTH / 2 - gap / 2 - btn_w
            night_x = settings.WIDTH / 2 + gap / 2

            if day_x <= x <= day_x + btn_w and y0 <= y <= y0 + btn_h:
                self.mode = "day"
                self.state = "menu"
                return
            if night_x <= x <= night_x + btn_w and y0 <= y <= y0 + btn_h:
                self.mode = "night"
                self.state = "menu"
                return

    def _draw_menu(self) -> None:
        arcade.draw_lrbt_rectangle_filled(0, settings.WIDTH, 0, settings.HEIGHT, (20, 20, 20))
        arcade.draw_text(
            settings.WINDOW_TITLE,
            settings.WIDTH / 2,
            settings.HEIGHT - 140,
            settings.WHITE,
            48,
            anchor_x="center",
            bold=True,
        )

        btn_w = 360
        btn_h = 80
        gap = 30
        start_y = settings.HEIGHT / 2 + btn_h + gap

        button_labels = ["STARTEN", "OPTIONEN", "VERLASSEN"]
        for index, label in enumerate(button_labels):
            y = start_y - index * (btn_h + gap) - btn_h / 2
            x = settings.WIDTH / 2 - btn_w / 2
            arcade.draw_lrbt_rectangle_filled(x, x + btn_w, y, y + btn_h, (50, 50, 50))
            arcade.draw_lrbt_rectangle_outline(x, x + btn_w, y, y + btn_h, (200, 200, 200), 3)
            arcade.draw_text(
                label,
                x + btn_w / 2,
                y + btn_h / 2,
                settings.WHITE,
                24,
                anchor_x="center",
                anchor_y="center",
            )

        current_mode = {"day": "TAG", "night": "NACHT"}.get(self.mode or "", "NICHT GEWAHLT")
        mode_label = f"Modus: {current_mode}"
        arcade.draw_text(
            mode_label,
            settings.WIDTH / 2,
            settings.HEIGHT / 2 - 180,
            (200, 200, 200),
            16,
            anchor_x="center",
        )
        arcade.draw_text(
            "Klicke auf einen Block zum Auswaehlen",
            settings.WIDTH / 2,
            settings.HEIGHT / 2 - 210,
            (180, 180, 180),
            12,
            anchor_x="center",
        )

    def _draw_options(self) -> None:
        arcade.draw_lrbt_rectangle_filled(0, settings.WIDTH, 0, settings.HEIGHT, (15, 15, 15))
        arcade.draw_text(
            "Optionen",
            settings.WIDTH / 2,
            settings.HEIGHT - 120,
            settings.WHITE,
            40,
            anchor_x="center",
            bold=True,
        )

        btn_w = 300
        btn_h = 100
        gap = 80
        y = settings.HEIGHT / 2 - btn_h / 2

        day_x = settings.WIDTH / 2 - gap / 2 - btn_w
        night_x = settings.WIDTH / 2 + gap / 2

        for label, x in [("TAG", day_x), ("NACHT", night_x)]:
            arcade.draw_lrbt_rectangle_filled(x, x + btn_w, y, y + btn_h, (60, 60, 60))
            arcade.draw_lrbt_rectangle_outline(x, x + btn_w, y, y + btn_h, (220, 220, 220), 3)
            arcade.draw_text(
                label,
                x + btn_w / 2,
                y + btn_h / 2,
                settings.WHITE,
                26,
                anchor_x="center",
                anchor_y="center",
            )

        arcade.draw_text(
            "Waehle die Arena-Beleuchtung. Nach der Auswahl kehrst du zum Menue zurueck.",
            settings.WIDTH / 2,
            settings.HEIGHT / 2 - 120,
            (200, 200, 200),
            14,
            anchor_x="center",
        )
        arcade.draw_text(
            "ESC zum Beenden, M fuer Menue",
            settings.WIDTH / 2,
            settings.HEIGHT / 2 - 150,
            (180, 180, 180),
            12,
            anchor_x="center",
        )

    def on_close(self) -> None:
        self._stop_music()
        super().on_close()
