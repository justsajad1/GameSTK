# Test Dokumentation

## Teststrategie
- Jede Aenderung an `game/app.py`, `game/core.py` oder `game/settings.py` wurde sofort lokal per `python3 game/main.py` geprobt. Wir spielen Menue -> Charakterwahl -> Tag/Nacht-Modus -> drei Runden durch, damit Animationen, Kamera, HUD und Audio bei jedem Commit ueberprueft werden.
- Nach der Eigenkontrolle teilte ich (Sajad) oder jeder andere, der etwas Neues gemacht hat, kurze Capture-Videos mit den anderen Projektmitgliedern in der WhatsApp-Gruppe. Anschließend wiederholen beide die Szenarien (Player 1 vs. Player 2) auf ihren Rechnern und melden Abweichungen oder Timing-Probleme zurück.
- Reproduzierbare Fehler und kleinere Auffaelligkeiten werden direkt im WhatsApp-Thread gesammelt und beim naechsten Commit behoben.

## Balancing
- Der Schwierigkeitsgrad basiert auf festen Parametern wie `PLAYER_SPEED = 6`, `JUMP_SPEED = 15`, `ATTACK_RANGE = 120`, `ROUND_TIME_LIMIT = 60.0` und `WINS_TO_MATCH = 3` (`game/settings.py:49-66`). Diese Werte halten Matches auf drei bis vier Runden und geben beiden Seiten genug Reaktionszeit.
- Testmethodik: Best-of-five-Sparrings mit wechselnden Charakteren. Eddy konzentriert sich auf Schaden/Cooldowns, Vinh beobachtet Luftduelle und Wandnaehe, Sajad protokolliert KO-Zeiten und berichtet sie in die WhatsApp-Gruppe.
- Aus den Sessions resultierten die heutigen `ATTACK_PROFILES` mit 20/30/45 Schaden und Cooldowns von 0,33/0,5/1,0 s (`game/settings.py:71-94`). Dadurch bleiben Kombos gefaehrlich, ohne Dauer-Stun auszuloesen; gleichzeitig wurde `ATTACK_RANGE` auf 120 Pixel erhoeht, damit Sprungangriffe nicht ins Leere laufen.

## Debugging
- **Ueberlappende Kaempfer**: Gleichzeitige Vorwaertsbewegungen liessen Sprites ineinander rutschen. `_resolve_player_overlap()` verteilt nun die Mindestdistanz anhand der Kollisionsbreiten und Bildschirmgrenzen (`game/app.py:205-245`). Der Fix wurde lokal reproduziert und anschliessend von Eddy/Vinh gegengeprueft.
- **HUD-Name Spieler 2**: Der zweite Name lag auf dem Lebensbalken, weil er linksbuendig gezeichnet wurde. Wir rendern den Text jetzt mit `anchor_x="right"` am rechten Balkenrand (`game/app.py:527-548`). Der Bug wurde ohne KI behoben und auf beiden Hintergruenden getestet.
- **Fehlende Sprites**: Nicht vorhandene PNGs liessen `load_sprite_sheet()` abstuerzen. Die Funktion erzeugt inzwischen Dummy-Texturen und loggt den Dateinamen (`game/core.py:55-88`), sodass Tests weiterlaufen koennen. Verifiziert mit absichtlich entfernten Dateien.

## Bekannte Fehler
- **Kein Einzelspieler**: Es gibt weiterhin keinen KI-Gegner; ein Mensch muss Spieler 2 uebernehmen (`README.md`). Workaround: Trainingslaeufe mit einem passiven zweiten Spieler.
- **Kein Controller-Support**: Arcade verarbeitet nur Tastatureingaben. Wer ein Gamepad nutzen will, muss externe Mapping-Tools wie JoyToKey einsetzen.
- **Restueberlappung an Screen-Raendern**: Stossen beide Kaempfer direkt an dieselbe Kante, bleiben <= 4 Pixel Ueberdeckung stehen, weil `_resolve_player_overlap()` den `TOUCH_TOLERANCE` respektiert (`game/app.py:205-245`). Kurz zurueckweichen oder springen loest das Problem.

## KI-Einsatz beim Debugging
- Eingesetzte Tools: ChatGPT 5 (Codex), Claude Sonnet, Gemini und GitHub Copilot (`docs/ai.md`). Sie unterstuetzen uns bei Architektur-, Balancing- und QA-Fragen.
- Prompt "Spielstatus und Rundenlogik strukturieren" (`docs/ai.md`, Beispiel 1) fuehrte zu der heutigen State-Machine mit `self.state`, Timern und Overlay-Texten (`game/app.py:100-160`).
- Prompt "Spielerueberlappung aufloesen" (`docs/ai.md`, Beispiel 2) resultierte direkt im aktuellen `_resolve_player_overlap()` und behebt das oben beschriebene Clipping.
- Prompt "Spritesheets robuster importieren" (`docs/ai.md`, Beispiel 3) inspirierte das Caching samt Dummy-Frames in `load_sprite_sheet()` (`game/core.py:116-188`), womit Asset-Luecken sichtbar, aber nicht blockierend werden.
- Nicht jeder Fix brauchte KI: Die rechtsbuendige Darstellung des Spielernamens von Slot 2 in `game/app.py:527-548` entstand bewusst manuell, um Arcade-Textplatzierung besser zu verstehen.

Finden Sie einen Fehler, dann [schreiben Sie uns eine E-Mail](mailto:najafizadasajad@gmail.com)
