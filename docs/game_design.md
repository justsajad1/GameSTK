# Game Design Dokument

## Spielkonzept
**Grundlegendes Konzept:**
Dieses Spiel ist ein 2D-Stickman-Kampfspiel, das in einer mittelalterlichen Welt spielt. Sieben verschiedene Herrscher kämpfen in Duellen gegeneinander, um die Reiche ihrer Gegner zu erobern. Jede Partie besteht aus drei Runden; derjenige, der die Mehrheit der Runden gewinnt, geht als neuer Herrscher hervor.

**Spielmechaniken:**
- 2D-Duellkampf zwischen zwei Spielern
- Grundbewegungen: Laufen, Springen, Doppelsprung, Angriff
- Jeder Charakter besitzt einzigartige Bewegungen, Spezialangriffe und Kombos
- Eine Runde ist beendet, wenn die Lebenspunkte eines Charakters vollständig aufgebraucht sind

**Unterschiede zum ursprünglichen Prototypen:**
- Fünf neue spielbare Charaktere mit individuellen Bewegungen und Kombos
- Hinzugefügter Doppelsprung
- Überarbeitete Lebensbalken
- Attraktiveres, modernes Hauptmenü
- Flüssigeres und reaktionsschnelleres Gameplay

**Storyboard und Game-Canvas:**
![Hauptmenü](sandbox:/mnt/data/Screenshot_20251114_170229_com_whatsapp_MediaViewActivity.jpg)

---

## Story und Charaktere
**Hintergrundgeschichte:**
In einer mittelalterlichen Epoche, in der die Erweiterung des eigenen Reiches von größter Bedeutung ist, treffen sieben Herrscher aus verschiedenen Regionen aufeinander. Sie organisieren ein königliches Turnier, in dem jeder Kampf über drei Runden ausgetragen wird. Der Sieger erhält einen Teil des gegnerischen Reiches und kommt dem Ziel näher, die gesamte Welt zu beherrschen.

**Protagonist:**
- Name: Wird im Projekt definiert
- Eigenschaften: Variieren je nach ausgewähltem Charakter
- Steuerung: Tastatur (Pfeiltasten/WASD), Leertaste zum Springen
- Animationen: Idle, Laufen, Springen, Doppelsprung, Angriff, Kombo

**Spielbare Charaktere:**
Hier sind die sieben auswählbaren Kämpfer, jeder mit einem eigenen Kampfstil und vollständigen Animationssätzen:

- **Tutankhamun** – Schnelle, präzise Angriffe im altägyptischen Stil
- **Charlemagne** – Europäischer Herrscher mit kraftvollen Schlägen
- **Knight II** – Schwerer Ritter mit robuster Ausrüstung
- **Knight III** – Beweglicherer Ritter mit höherer Geschwindigkeit
- **Samurai** – Nahkampfspezialist mit Katana
- **Samurai Archer** – Fernkämpfer mit schnellen Pfeilangriffen
- **Samurai Commander** – Taktischer Kämpfer mit ausgewogenen Fähigkeiten

**Charakterauswahl:**
![Charakterauswahl](sandbox:/mnt/data/Screenshot_20251114_170213_com_whatsapp_MediaViewActivity.jpg)

---

## Spielziel und Progression
**Ziel des Spiels:**
Das Hauptziel besteht darin, drei Runden in einem Duell zu gewinnen. Der Spieler, der zwei von drei Runden für sich entscheidet, gewinnt das Match.

**Fortschrittsmetriken:**
- Anzahl gewonnener Runden
- Besiegte Herrscher im Verlauf des Turniers

**Schwierigkeitsentwicklung:**
Der Schwierigkeitsgrad hängt direkt vom Können des Gegners ab – sei es ein menschlicher Zweitspieler oder eine KI. Je stärker der Gegner agiert, desto anspruchsvoller wird der Kampf.

---

## Level Design
**Verfügbare Arenen:**
1. **Tagesarena** – Helle Atmosphäre, klare Sicht
2. **Nachtarena** – Dunklere Stimmung, kontrastreiche Umgebung

**Levelaufbau:**
Beide Arenen sind symmetrisch gestaltet und bieten ausreichend Raum für Kampfbewegungen, Kombos und taktische Positionierung.

**Herausforderungen:**
- Unterschiedliche visuelle Stimmung (Tag/Nacht)
- Kein Gelände, das den Kampf beeinflusst – Fokus auf Skill und Reaktion

---

## Assets und Ressourcen
**Grafiken:**
Die Charaktere basieren auf Stickman-Assets, die über *itch.io* heruntergeladen wurden. Sie verfügen über vollständige Animationssätze für alle Kampfbewegungen. Die Arenen bestehen aus PNG-Hintergrundbildern für Tag- und Nachtvarianten.

**Animationen:**
Jeder Charakter besitzt Animationen für Idle, Laufen, Springen, Angriff und Kombo.

**Sounds:**
Es werden lizenzfreie Sounds aus dem Internet verwendet, darunter:
- KO-Soundeffekte
- Angriffstreffer-Sounds
- Intro-Sound des Spiels

**Ressourcenherkunft:**
- Charakter-Assets: itch.io
- Arenen: freie Online-Quellen
- Sounds: lizenzfreie Soundbibliotheken

---

## Technische Realisierung
**Engine:**
Das Spiel wurde mit der *Arcade*-Engine entwickelt, die ideal für 2D-Actionspiele geeignet ist.

**Dateiformate:**
- Charaktere: PNG-Spritesheets mit Frames von 162 px Höhe
- Arenen: PNG-Bilder

**Ladeprozess:**
- Spritesheets werden beim Spielstart geladen und in Animationssequenzen zerlegt
- Die ausgewählte Arena wird als Hintergrund geladen
- Arcade verwaltet Animationen, Bewegung, Treffererkennung und Kollisionslogik in Echtzeit

*(Weitere technische Diagramme oder Beispielcode können später ergänzt werden.)*

