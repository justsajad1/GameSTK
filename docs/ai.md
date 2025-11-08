# KI-Einsatz im Projekt The Battle of Empires

Dieses Dokument haelt fest, wie wir KI-gestuetzte Werkzeuge im Arcade-Fighting-Game "The Battle of Empires" eingesetzt haben. Wir beschreiben konkrete Einsatzgebiete, zeigen Prompts mit Rueckmeldungen und reflektieren Nutzen und Grenzen.

## Verwendete KI-Tools

- **ChatGPT 4o**: Unterstuetzung bei Architekturfragen rund um `arcade.Window` sowie bei der Formulierung von Zustandsablaeufen und Timings.
- **Claude 3.5 Sonnet**: Review von Kampfmechaniken, Balancing-Vorschlaegen und alternativen Datenstrukturen fuer Angriffsdefinitionen.
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

### Beispiel 2: Tastaturbelegungen konfliktfrei normalisieren

**Kontext:** Zwei Spieler teilen sich eine Tastatur. Wir wollten vermeiden, dass automatisch importierte Belegungen kollidieren, wenn ein Key doppelt vergeben ist.

**Prompt:**
```
Given a dict of desired key bindings for actions ["left","right","jump","punch","kick","special"], 
write a Python helper that walks through the desired keys and falls back to defaults if a key is already taken.
Return a normalized dict and keep the order of actions stable.
```

**Ergebnis (Auszug):**
```
def normalize_bindings(desired, defaults, actions):
    normalized = {}
    used = set()
    for action in actions:
        preferred = desired.get(action, defaults[action])
        for candidate in [preferred] + [defaults[a] for a in actions]:
            if candidate not in used:
                normalized[action] = candidate
                used.add(candidate)
                break
    return normalized
```

**Verwendung im Projekt:** Die Rueckmeldung wurde in `_normalize_player_controls` umgesetzt, das Konflikte behebt und Defaults bewahrt.

```python
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
```

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
