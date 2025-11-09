# Implementierung des Spiels "The Battle of Empires"

Hier berichte ich (Sajad) Lead-Developer (unterstützt von Eddy und Vinh) über Architektur, Technik und Zusammenarbeit rund um den Arcade-Port.

## Codestruktur

* **Wurde der Prototyp weiterentwickelt oder "from Scratch" begonnen?**  
  Ausgangspunkt war ein funktionsfähiger Pygame-Prototyp. Mithilfe von KI wurde daraus ein Arcade-3.3.2-Gerüst generiert, das wir anschließend manuell verfeinert haben: Event-Loop, Rendering, Asset-Ladepfade sowie neue Features (Charakterauswahl, Tag/Nacht-Modus, Pausenlogik) entstanden Schritt für Schritt direkt in Arcade.

* **Wie ist der Code organisiert?**  
  - `game/main.py`: setzt das Arbeitsverzeichnis auf die Projektwurzel und startet das Fenster, egal ob das Paket oder das Skript ausgeführt wird.  
  - `game/app.py`: enthält `StickmanFighterGame`, das Menü, Flow-States, Eingaben, HUD und Sound/Lade-Logik steuert.  
  - `game/core.py`: kapselt Gameplay-Primitiven wie `Fighter`, `AttackSpec`, Sprite-Sheet-Handling, Angriffseffekte und Trefferlogik.  
  - `game/settings.py`: zentrale Konfigurationsquelle (Auflösung, Physik, Steuerung, Soundpfade, Kämpferkatalog, Standardauswahl).  
  - `assets/`: Sprites, Sounds und Hintergründe; dank `ensure_path()` funktionieren sie unabhängig vom aktuellen Arbeitsverzeichnis.  
  - `docs/`: Projektdokumentation (Storyboard, Projektmanagement, diese Implementierungsbeschreibung).

* **Welche wichtigen Klassen und Funktionen gibt es?**  
  - **`StickmanFighterGame` (`game/app.py`)** – leitet vom Arcade-Window ab, verwaltet alle Spielzustände (Menü, Charakterwahl, Optionen, Playing, Round-/Match-Over, Pause), lädt Assets und orchestriert die Kämpfer.  
    ```python
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
    
            self.state = "menu"
            self.mode: Optional[str] = None
            self.round_restart_timer = 0
            self.match_restart_timer = 0
            self.camera_offset = 0.0
            self.round_time_remaining = float(settings.ROUND_TIME_LIMIT)
            self.round_message = ""
    
            self.background: Optional[arcade.Texture] = None
            self.sounds = _load_sounds()
            self.music_player: Optional[object] = None
            self._start_music_loop()
    
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
    ```
  - **`Fighter` (`game/core.py`)** – repräsentiert animierte Kämpfer inklusive Eingabe, Gravitation, Doppelsprung, Attacken mit Cooldowns, Trefferfeedback, Effekten und Todes-/Respawnlogik. `try_hit()` prüft Reichweiten anhand der dynamisch berechneten Kollisionsbreite und löst Treffer samt Invincibility-Frames aus.
  - **`AttackSpec` und `ActiveEffect` (`game/core.py`)** – Dataclasses, die Schaden, Cooldown, Hit-Frame-Ratio sowie visuelle Effekte beschreiben. Dadurch lassen sich Attacken für jeden Charakter feinjustieren.
  - **`load_sprite_sheet()` (`game/core.py`)** – lädt, cached und spiegelt Sprite-Sheets, berechnet sichtbare Bounds, erzwingt skalierte Texturen (Nearest-Neighbor) und liefert Kennzahlen, die später für Kollisionsbreiten und Bodenabstände genutzt werden.
  - **Hilfsfunktionen (`game/settings.py`)** – `base_path`, `asset_path`, `ensure_path` kapseln alle Dateipfade und vermeiden harte Pfadangaben in Spielcode.

## Implementierte Features

* **Welche technischen Features wurden umgesetzt?**  
  - Lokales 2-Spieler-Fighting mit frei belegbaren Tasten je Spieler; `_normalize_player_controls()` verhindert doppelte Belegungen.  
  - Drei Attacken pro Kämpfer inklusive Cooldown, Hit-Frame-Ratio, optionalem VFX (z. B. Projektile beim Samurai) und individuellen Schadenswerten.  
  - Vollständiger Match-Flow: Timer (`ROUND_TIME_LIMIT`), Sudden-Death-Regeln, automatischer Runden-/Match-Reset, HUD mit Lebensbalken, Score-Pips und Modusanzeige.  
  - Tag-/Nacht-Option mit eigenen Hintergrund-Texturen, Kamerawobble für Parallax-Effekt und gestreamter Musik, die im Loop läuft.  
  - Datengetriebener Kämpferkatalog (`settings.FIGHTERS`) mit Sprite-Verzeichnissen, Frame-Größen, Actionsheets und Effekten; neue Charaktere benötigen lediglich Asset-Einträge.  
  - Charakterauswahl- und Optionsmenü für Maus/Keyboard, inklusive visueller Hervorhebung, sowie Pausenmenü mit Hotkeys für Fortsetzen, Neustart und Menü.
  ```python
  DEFAULT_FIGHTER_SELECTION = {
      "player1": "samurai_commander",
      "player2": "samurai_archer",
  }
  ```

* **Welche besonderen Herausforderungen gab es dabei?**  
  - Die automatische Umwandlung von Pygame nach Arcade deckte nur Grundstrukturen ab; komplexe States, Audio-Streaming sowie die Sprite-Verwaltung mussten komplett neu gedacht werden.  
  - Unterschiedlich große Sprite-Sheets (162px Ägypter vs. 128px Samurai) verlangten nach dynamischer Skalierung, damit Hitboxen und optische Größen zueinander passen.  
  - Geteilte Tastatursteuerung führte erst zu überlappenden Keycodes, weshalb ein Normalisierer für verfügbare Tasten nötig wurde.  
  - Arcade lädt standardmäßig linear gefilterte Texturen, wodurch Pixel-Art verwaschen wirkte und ein eigener Workaround erforderlich war.  
  - Durch das Streaming der Musik im Loop mussten wir Audio-Player-Instanzen sauber starten/stoppen, um Memory-Leaks beim Szenenwechsel zu vermeiden.

* **Lösungen, auf die Sie besonders stolz sind:**  
  - **Stabile Spielertrennung trotz gleichzeitiger Eingaben** – `_resolve_player_overlap()` verteilt Überlappung gleichmäßig und berücksichtigt den verfügbaren Platz an den Bildschirmrändern.
    ```python
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
    ```
  - **Pixel-Look erhalten** – Arcade filtert Texturen standardmäßig bilinear; durch das globale Setzen des SpriteList-Filters bleiben Pixel scharf, egal wie stark sie skaliert werden.
    ```python
    from arcade import gl
    arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST
    ```
  - **Datengetriebene Attack-Balancing-Struktur** – `AttackSpec` hält Schaden, Cooldowns und Effekte zentral, wodurch sich Kämpfer in `settings.FIGHTERS` leicht tunen lassen.
    ```python
    @dataclass
    class AttackSpec:
        name: str
        damage: int
        cooldown_frames: int
        hit_frame_ratio: float = 0.5
        effect: Optional[str] = None
    ```
  - **Sprite-Sheet-Caching & Auto-Skalierung** – `load_sprite_sheet()` skaliert Frames hoch, erzwingt Maximalgrößen und misst sichtbare Bounds, damit Kollisionsbreiten korrekt sind.
    ```python
    def load_sprite_sheet(
        sheet_path: Path | str,
        frame_size: int = settings.FRAME_SIZE,
    ) -> tuple[TextureBundle, dict[str, float]]:
        texture_path = settings.ensure_path(sheet_path)
        cache_key = (texture_path.resolve(), frame_size)
        cached = _SPRITE_CACHE.get(cache_key)
        if cached:
            textures_cached, metrics_cached = cached
            textures_copy = {side: frames[:] for side, frames in textures_cached.items()}
            return textures_copy, dict(metrics_cached)
    
        frames_right: list[arcade.Texture] = []
        frames_left: list[arcade.Texture] = []
        upscale_factor = float(getattr(settings, "FIGHTER_TEXTURE_UPSCALE", 1.0))
        max_dimension = float(getattr(settings, "FIGHTER_TEXTURE_MAX_DIMENSION", 0.0))
    
        with Image.open(texture_path) as sheet_image:
            sheet_img = sheet_image.convert("RGBA")
            sheet_width, sheet_height = sheet_img.size
            num_frames = max(1, sheet_width // frame_size)
    
            for frame_index in range(num_frames):
                left = frame_index * frame_size
                box = (left, 0, left + frame_size, sheet_height)
                frame_img = sheet_img.crop(box).copy()
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
                frame_img = processed_frame
                # ... (Bounding-Box-Messung, Spiegelung, Metrics)
    ```

## Zusammenarbeit im Entwickler:innenteam, Tools

* **Wie wurde die Arbeit unter den Entwickler:innen aufgeteilt?**  
  - Sajad verantwortete Architektur, Portierung, Match-Flow, Sprite-Pipeline, Sound-Handling und finale Integration.  
  - Eddy lieferte Asset-Feedback (Sprites/Sounds), prüfte Balancing (Schaden, Cooldowns) und testete Menü- sowie Pausen-Flows.  
  - Vinh konzentrierte sich auf QA (Eingaben, Kollisionsfälle, Tag-/Nacht-Hintergründe) und half beim Einpflegen neuer Charaktervarianten.  
  - Gemeinsame Tests liefen in kurzen Sessions: Einer steuerte Spieler 1, der andere Spieler 2, um Edge-Cases (Doppelsprünge, gleichzeitige KOs) live zu beobachten.  
  - Bugtracking erfolgte in GitHub-Issues; Fixes wurden jeweils von einer zweiten Person gegengeprüft.

* **Welche Werkzeuge (Editoren, IDEs) wurden genutzt?**  
  - Sajad nutzte Cursor (VSCode + Codex) für KI-unterstützte Iterationen.  
  - Eddy und Vinh arbeiteten primär in PyCharm mit Arcade-Debugger und Live-Reload.  
  - Versionskontrolle via Gitlab; Tests liefen lokal unter Python 3.13.  
  - Für Assets kamen Aseprite/GIMP (Sprites) sowie Audacity (Soundanpassungen) zum Einsatz.  

## KI-Einsatz für Entwicklung

* **Welche KI-Tools wurden verwendet?**  
  - Codex (über Cursor) für schnelle Pygame→Arcade-Portierung und Boilerplate.  
  - Claude für Fehleranalysen (z. B. unscharfe Sprites) und alternative Lösungswege.  
  - Gemini für konzeptionelle Datenstrukturen (Attack-Specs, Effektverwaltung) und Prompt-Ideen.

* **Beispiele für Prompts und deren Ergebnisse**

  **Prompt für den Arcade-Port (Codex in Cursor):**
  
  _"Port the following pygame main loop and event handling to arcade 3.3.2 with an `arcade.Window` subclass. Preserve the state machine and add hooks for menus and gameplay."_
  
  **Ergebnis:**
  ```python
  class StickmanFighterGame(arcade.Window):
      def on_draw(self) -> None:
          self.clear()
          if self.state == "menu":
              self._draw_menu()
              return
          if self.background:
              arcade.draw_texture_rect(self.background, XYWH(...))
          self.fighter1.draw()
          self.fighter2.draw()
          self.draw_hud()
  
      def on_update(self, delta_time: float) -> None:
          if self.state == "playing":
              self.fighter1.update(self.keys, self.fighter2)
              self.fighter2.update(self.keys, self.fighter1)
              self._resolve_player_overlap()
  ```

  **Prompt für Kollisionsauflösung (Claude):**
  
  _"Bei gleichzeitigen Vorwärtseingaben laufen meine Kämpfer ineinander. Wie kann ich in Arcade den Mindestabstand erzwingen?"_
  
  **Ergebnis:**
  ```python
  def _resolve_player_overlap(self) -> None:
      left, right = (fighter1, fighter2) if fighter1.x <= fighter2.x else (fighter2, fighter1)
      collision_span = left.collision_half_width + right.collision_half_width
      min_distance = max(settings.MIN_PLAYER_DISTANCE, collision_span)
      current_distance = right.x - left.x
      if current_distance >= min_distance - settings.TOUCH_TOLERANCE:
          return
      overlap = min_distance - current_distance
      left_available = max(0.0, left.x - left.w / 2)
      right_available = max(0.0, settings.WIDTH - right.x - right.w / 2)
      left_shift = min(overlap / 2, left_available)
      right_shift = min(overlap / 2, right_available)
      left.x -= left_shift
      right.x += right_shift
  ```

  **Prompt für Datenstrukturen (Gemini):**
  
  _"Design a readable data structure for fighter attack specs (damage, cooldown, hit frame, optional VFX) so that each character can override just parts of it."_
  
  **Ergebnis:**
  ```python
  ATTACK_PROFILES = {
      "attack1": {"damage": 20, "cooldown": 1.0 / 3.0, "hit_frame_ratio": 0.4},
      "attack2": {"damage": 30, "cooldown": 0.5, "hit_frame_ratio": 0.5},
      "attack3": {"damage": 45, "cooldown": 1.0, "hit_frame_ratio": 0.6},
  }
  ```

**Integration der KI‑Vorschläge**

Vorschläge dienten als Ausgangspunkt; Struktur wurde übernommen, Variablennamen, States und Asset‑Handling an die Codebasis angepasst.

- Nach jeder KI‑Änderung testeten wir kurz (Spielstart, Moduswechsel, komplette Matches), um Regressionen früh zu erkennen.

- Vorschläge mit falschen Arcade‑Konstanten oder veraltetem API‑Wissen wurden verworfen; bei Bedarf fragten wir gezielt nach neueren Versionen oder ergänzten Kontextcode im Prompt.

- Die Kombination mehrerer KI‑Ideen (z. B. Texture‑Filter‑Hinweis von Claude + Loop‑Gerüst von Codex) beschleunigte Experimente; der finale Merge erfolgte stets nach manuellem Code‑Review.

- Änderungen wurden in Commit‑Nachrichten dokumentiert.