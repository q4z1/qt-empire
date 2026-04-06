# Empire Prototype

Modernes, Empire-inspiriertes rundenbasiertes Strategiespiel mit klar getrennter Engine- und UI-Architektur.

## Ziel

Das Projekt orientiert sich an klassischen Empire-Varianten, mit Tendenz zu `Empire Deluxe`, bleibt aber in der ersten Phase bewusst klein und portierbar.

Kurzfristige Ziele:
- spielbare Python-Prototyp-Engine
- Qt6/QML-Desktop-UI mit PySide6
- deterministische, headless testbare Logik

Langfristige Ziele:
- Cross-platform Desktop-App
- Port der Game Logic von Python nach C++
- UI möglichst unverändert auf derselben API weiterbetreiben

## Aktueller Stand

Bereits vorhanden:
- rechteckige Grid-Karte
- Terrain: `plains`, `forest`, `mountain`, `water`, `city`
- Einheiten: `infantry`, `tank`, `transport`, `destroyer`
- Bewegung mit Terrain-/Domain-Regeln
- deterministischer Nahkampf mit Gegenschlag
- Stadteroberung
- einfache Stadtproduktion
- Fog of War mit `visible` und `explored`
- erstes Transportmodell mit Embark/Disembark
- legale Zielmarkierungen für Auswahl und Aktionen
- Kartenklicks priorisieren markierte Aktionen vor bloßer Re-Selektion
- Startmenü mit Einstieg in die Spielansicht
- JSON-basiertes Quick Save / Quick Load
- einfache SVG-Icons für Einheiten und Städte
- Szenarioauswahl im Startmenü
- einfache Bauaufträge pro Stadt (`infantry` oder `tank`)
- Küstenstädte können zusätzlich See-Einheiten bauen
- Städte tragen nun persistierte Rollen wie `City`, `Factory` oder `Harbor`
- Produktion hängt an expliziten Stadtrollen:
  `City` fuer Infanterie, `Factory` fuer Landruestung, `Harbor` fuer See-Einheiten
- `Capital` ist als erste Sonderstadt eingefuehrt:
  mehr Sicht, staerkere Reparatur und Grundlage fuer Siegbedingungen
- Städte reparieren und versorgen eigene Einheiten zu Zugbeginn
- Eroberung der letzten gegnerischen Hauptstadt beendet das Spiel
- rechte Seitenleiste mit scrollbareren Status-/Einheitslisten
- laufender GUI-Feinschliff für besser lesbare Karten- und Sidebar-Hierarchie
- Hover-Hinweise und Legende fuer Kartenaktionen
- kompaktere Pfadangaben und breitere rechte Sidebar
- minimale Qt/QML-Oberfläche
- headless Demo-Capture fuer Launcher- und Ingame-Sequenzen als MP4
- Tests für Kernregeln

## Projekt starten

Virtuelle Umgebung und Dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

CLI-Demo:

```bash
.venv/bin/python main.py cli
```

GUI:

```bash
.venv/bin/python main.py ui
```

Kurzes Headless-Demo-Video:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python main.py capture-demo
```

Ausgabe:
- `captures/demo-launcher-ingame.mp4`

Quick Save:
- GUI speichert und lädt aktuell über `saves/quicksave.json`

Tests:

```bash
.venv/bin/pytest -q
```

## Struktur

```text
game/
  logic/   # headless Regeln und Game-State
  ui/      # Qt/QML-Präsentationsschicht
main.py    # Einstiegspunkt für cli/ui
tests/     # Regeltests
```

## Leitlinien

- Keine Qt-Imports in `game/logic`
- UI enthält keine Spielregeln
- API zwischen Engine und UI bleibt einfach und portierbar
- Datenmodell bevorzugt Primitive, Listen, Dicts und einfache Klassen
- Verhalten muss deterministisch und testbar bleiben

Siehe auch [`ARCHITECTURE.md`](/home/min/Development/empire/ARCHITECTURE.md) und [`TODO.md`](/home/min/Development/empire/TODO.md).
