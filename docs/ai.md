# KI-Einsatz im Projekt The Battle of Empires

Dieses Dokument haelt fest, wie wir KI-gestuetzte Werkzeuge im Arcade-Fighting-Game "The Battle of Empires" eingesetzt haben. Wir beschreiben konkrete Einsatzgebiete, zeigen Prompts mit Rueckmeldungen und reflektieren Nutzen und Grenzen.

## Verwendete KI-Tools

- **ChatGPT 5 (Codex)**: Unterstuetzung bei Architekturfragen rund um `arcade.Window` sowie bei der Formulierung von Zustandsablaeufen und Timings.
- **Claude Sonnet und Gemini**: Review von Kampfmechaniken, Balancing-Vorschlaegen und alternativen Datenstrukturen fuer Angriffsdefinitionen.
- **GitHub Copilot**: Inline-Hinweise beim Ausformulieren von Python-Methoden, z. B. fuer Sprite-Management und Eingabelogik.

## Beispiel-Prompts

Die folgenden Dialogauszuege zeigen typische Interaktionen mit generativen KI-Tools waehrend der Entwicklung.

### Beispiel 1: Spielstatus und Rundenlogik strukturieren

**Kontext:** Beim Umbau des Game-Loops wollten wir Menue, Charakterwahl und Matchflow klar trennen, ohne mehrere Fenster zu pflegen.

**Prompt:**
```
We are building a two-player local fighting game with the Python Arcade window class.
Help us design a simple state machine that covers menu -> options -> character_select -> playing -> round_over -> match_over.
We need timers for round restarts and a text overlay when a round winner is decided.
```

**Ergebnis (Auszug):**
```
- Track a string-based state variable on the window instance (e.g. self.state = "menu").
- Store timers as floats so they can count down in on_update.
- When a round ends set self.round_message and start a short cooldown before switching back to playing or match_over.
- Keep camera offset and UI text in dictionaries so you can reuse them in multiple states.
```

**Verwendung im Projekt:** Der Vorschlag floss in den Konstruktor von `StickmanFighterGame` ein und definiert heute die zentralen Timer.

```python
        self.state = "menu"
        self.mode: Optional[str] = None
        self.round_restart_timer = 0
        self.match_restart_timer = 0
        self.round_time_remaining = float(settings.ROUND_TIME_LIMIT)
        self.round_message = ""
```

### Beispiel 2: Spielerueberlappung mit Randbedingungen aufloesen

**Kontext:** Wenn beide Kaempfer gleichzeitig nach innen druecken, ueberlappen sich die Hitboxen und Figuren rutschen durch die Kamera. Wir brauchten eine robuste Aufteilung, die Restabstaende und Bildschirmraender respektiert.

**Prompt:**
```
In a 2P arcade fighter we track fighter.x, fighter.width, and a MIN_PLAYER_DISTANCE.
Design a helper _resolve_player_overlap() that:
- detects when fighters get closer than the min distance (consider collision widths),
- divides the overlap evenly, but clamps to the available space on each side,
- redistributes any remaining pixels so no one clips outside the screen.
Return early if fighters are vertically far apart or one is KO'ed.
```

**Ergebnis (Auszug):**
```
left, right = sort_by_x(f1, f2)
min_distance = max(MIN_PLAYER_DISTANCE, left.hw + right.hw)
overlap = min_distance - (right.x - left.x)
half = overlap / 2
left_shift = min(half, left.available_space_to_left_edge())
right_shift = min(half, right.available_space_to_right_edge())
shift_remaining_pixels_across_both_sides()
left.x -= left_shift
right.x += right_shift
```

**Verwendung im Projekt:** Das Muster wurde direkt in `_resolve_player_overlap` (`game/app.py:205`) uebernommen. Die Routine verteilt die Verschiebung, prueft zuerst vertikale Trennung sowie KO-Zustaende und sorgt anschliessend dafuer, dass beide Kaempfer trotz Restueberlappung innerhalb `settings.WIDTH` bleiben.

### Beispiel 3: Spritesheets robuster importieren

**Kontext:** Mehrere Kaempfer teilen sich Spritesheets, deren sichtbare Bereiche stark variieren. Wir brauchten eine Automatisierung, die Bounding-Boxen analysiert und Dummy-Frames erzeugt, falls Assets fehlen.

**Prompt:**
```
In a Python Arcade project we load fighter sprite sheets with Pillow. 
How can we compute the visible area (alpha bbox), track the tallest and widest frame, 
and cache processed textures so we only do the heavy work once?
Suggest a function signature that returns both textures per facing and some metrics.
```

**Ergebnis (Auszug):**
```
Use a module-level dict keyed by (sheet_path, frame_size).
When loading, compute alpha.getbbox() to derive visible width/height and bottom margin.
Return ( {"right": frames, "left": flipped_frames}, metrics_dict ).
If the file is missing produce a magenta placeholder so the game fails gracefully.
```

**Verwendung im Projekt:** Das Pattern findet sich in `load_sprite_sheet` wieder und steuert das Texture-Caching.

```python
    cache_key = (texture_path.resolve(), frame_size)
    cached = _SPRITE_CACHE.get(cache_key)
    if cached:
        textures_cached, metrics_cached = cached
        textures_copy = {side: frames[:] for side, frames in textures_cached.items()}
        return textures_copy, dict(metrics_cached)

    if not texture_path.is_file():
        print(f"Missing sprite replaced: {texture_path.name}")
        textures = {"right": [DUMMY_FRAME], "left": [DUMMY_FRAME]}
```

## Kritische Bewertung des KI-Einsatzes

| Vorteile | Nachteile/Einschraenkungen |
| --- | --- |
| Schnelles Validieren von Arcade-spezifischen Patterns und State-Flow-Ideen | Antworten sind gelegentlich generisch und muessen auf das konkrete Projekt zugeschnitten werden |
| Inspiration fuer Datenstrukturen (z. B. AttackSpec, Texture-Caching) | Teilweise fehlerhafte Beispiele, insbesondere bei Bibliotheksfunktionen |
| Beschleunigte Dokumentation und Commit-Beschreibungen | Benoetigt sorgfaeltige Quellcode-Reviews, um unbeabsichtigte Seiteneffekte zu vermeiden |

## Abschliessende Einschaetzung

### Was haben wir ueber den Einsatz von KI-Tools gelernt?
- Praezise Prompts mit Projektkontext fuehren zu brauchbaren Ergebnissen.
- Iteratives Nachfragen ist wichtig, um Vorschlaege auf Arcade und unsere Assets zuzuschneiden.
- KI ersetzt kein Fachwissen, hilft aber beim Strukturieren von Ideen und Code.
- Wir dokumentieren relevante Prompts und Entscheidungen im Repo, damit Teammitglieder Spaeter getroffene Annahmen nachvollziehen koennen.

### Fuer welche Anwendungsfaelle sind KI-Tools besonders geeignet?
- Architektur- und Refactoring-Diskussionen rund um Fensterzustand, Timer und Eingaben.
- Brainstorming von Visual- und Audioideen, bevor final gerendert wird.
- Dokumentation und QA-Checklisten, etwa fuer manuelle Tests der Kampfmechaniken.

### Fuer welche Anwendungsfaelle sind sie nur eingeschraenkt geeignet?
- Endgueltige Balancing-Entscheidungen der Kaempfer (muss im Spiel getestet werden).
- Vollautomatische Sprite-Generierung ohne Nachbearbeitung.
- Performance-Kritische Optimierungen, die fundiertes Profiling erfordern.

### Fazit
KI-Werkzeuge helfen uns vor allem beim Strukturieren von Spielsystemen und beim schnellen Bewerten alternativer Loesungen. Die finale Umsetzung bleibt dennoch Handarbeit, weil Arcade-spezifische Details und Balancing in Tests erarbeitet werden muessen.
