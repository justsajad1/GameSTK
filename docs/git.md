# Git Dokumentation
Git-Verantwortlicher: Sajad

## Repository-Struktur
- `game/` enthält den Python-Code des Spiels (`app.py`, `core.py`, `settings.py`, `main.py`) sowie Laufzeitdateien.
- `assets/` bündelt alle Medien (Sprites, Sounds, Bilddateien) inkl. Lizenzhinweisen.
- `docs/` dokumentiert das Projekt (Git, KI, Implementierung, Projektmanagement etc.).
- `requirements.txt` fixiert die Python-Abhängigkeiten für Arcade 3.3.2 und Konsorten.
- Es wurde fast nur auf `main` gearbeitet. Wenn es nötig war, wurden kurze lokale Zweige benutzt und dann direkt wieder in `main` eingefügt. So wurde das Setup einfach gehalten.


## Workflow
- Typischer Ablauf: `git pull` → Entwicklung/Tests in VS Code (Cursor) → `git status`/`git diff` prüfen → zielgerichtetes Staging → Commit → `git push`.
- Verwendete Tools: Git im Terminal (Win + Uni-Pool) und das eingebaute Source-Control von VS Code/Cursor.
- Merge-Konflikte traten selten auf, da Features nacheinander in `main` landeten. Falls doch, wurden sie direkt im Editor gelöst (manuelle Auswahl der gültigen Blöcke, anschließendes Testen).

## Commit-Praxis
- Commits erfolgten nach jedem abgeschlossenen Arbeitspaket (neue Charaktere, Dokumentupdates, Bugfixes). Damit blieb die Historie lesbar und rücksetzbar.
- Beispiel-Messages: `cf18bae code entsprechend den neuen charachter angepasst...`, `c4b4145 wiederhochladen des repos, da die .git-datei verloren gegangen ist`.
- Alle Teammitglieder (Ich (Sajad), Eddy, Vinh) haben mindestens einen Commit selbstständig bzw. angeleitet durchgeführt; bei Bedarf stand ich neben ihnen und habe den Ablauf (Stage → Commit → Push) erklärt.

## Account-Zuordnung
- `sajad01 <najafizadasajad@gmail.com>` = Sajad (eigener Laptop).
- `Sayed Sajad Najafizada <najafizada@campus.tu-berlin.de>` = Sajad am Uni-PC-Pool.
- Eddy und Vinh haben ihre eigenen Rechner und die Gitlab-Website der TU Berlin benutzt, um Commit auszuführen.

## Herausforderungen
Das größte Problem war, dass der Ordner `.git` versehentlich gelöscht wurde. Dadurch war das Repository nicht mehr mit dem Remote verbunden.
Die Lösung ist, das Projekt zu klonen und die Änderungen manuell zu übertragen. Weil einige neue Dateien nicht im alten Verzeichnis waren, wurde das komplette Verzeichnis erneut hochgeladen. Hätte man die Änderungen damals in ein frisches Clone importiert, wäre das sauberer gewesen. Aber jetzt ist es dokumentiert und nachvollziehbar.
