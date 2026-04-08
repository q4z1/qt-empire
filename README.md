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
- Einheiten koennen jetzt per Klick auf entfernte Ziele entlang eines Pfads bewegt werden
- Teilweise erreichte Fernziele koennen jetzt als Orders an einer Einheit haengen bleiben und in spaeteren eigenen Zuegen automatisch fortgesetzt werden
- Diese Orders koennen jetzt bewusst geloescht werden, und ein neues Fernziel ersetzt bestehende Orders
- Fernbewegung nutzt jetzt Klick-zur-Bestaetigung: erster Klick setzt das Ziel, zweiter Klick fuehrt aus
- bestaetigte Fernziele, Stopppunkt und laufende Orders werden jetzt auf der Karte klarer markiert
- Pending-Ziele koennen jetzt auch explizit wieder geloescht werden
- Hover ueber ein entferntes Ziel zeigt jetzt eine einfache Pfadvorschau fuer die aktuell selektierte Einheit
- Die Vorschau zeigt jetzt auch lange Ziele jenseits des aktuellen Bewegungslimits mit Stopppunkt und Endziel
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
- einfache Schrittanimation fuer Fernbewegungen in der UI
- queued Bewegungen und Auto-Fortsetzung werden jetzt ebenfalls animiert
- laufende Bewegungen werden jetzt auch in der rechten Seitenleiste zusammengefasst
- Artillerie als neue Fernkampfeinheit mit Reichweitenangriff
- Artillerie-Fernkampf beachtet jetzt eine einfache Sichtlinie über blockierendes Terrain
- Artillerie hat jetzt eigene Terrainmodifikatoren fuer Fernkampf
- Artillerie kann auf Reichweite 2 jetzt Gegenfeuer ausloesen
- Gegenfeuer greift jetzt auch auf Reichweite 3, aber mit abgeschwaechtem Schaden
- Gegenfeuer verbraucht die Bewegungs-/Reaktionsfaehigkeit der verteidigenden Artillerie
- Artillerie kann jetzt bis Reichweite 3 bombardieren, mit leichtem Schadensabfall auf Distanz 3
- die Seitenleiste zeigt jetzt die Reichweite der selektierten Einheit direkt an
- erstes Grafik-Theme mit Empire-Deluxe-anmutender Terrain-Darstellung auf Basis von SVG-Kacheln fuer Land und Wasser
- Stadt-Terrain hat jetzt eine eigene Empire-Deluxe-artige SVG-Kachel statt nur eines Plains-Fallbacks
- Wasser bekommt jetzt eine einfache Shoreline-Ueberlagerung an Landgrenzen, damit Kuesten weniger hart abbrechen
- das Grafik-Theme kann jetzt zwischen einem flachen Prototyp-Look und Empire Deluxe umgeschaltet werden
- die Theme-Auswahl bleibt jetzt getrennt von den Spielständen in einer kleinen UI-Settings-Datei erhalten
- Empire-Deluxe-Terrain hat jetzt auch einfache Strassen- und Fluss-Overlay-Varianten fuer mehr Abwechslung
- Plains und Wasser werden jetzt pro Kachel deterministisch aus mehreren SVG-Varianten gewählt
- Forest, Mountain und City nutzen jetzt ebenfalls mehrere Empire-Deluxe-SVG-Varianten pro Kachel
- das aktive Theme beeinflusst jetzt auch Menü, Board und Seitenleiste farblich
- minimale Qt/QML-Oberfläche
- headless Demo-Capture fuer Launcher- und Ingame-Sequenzen als MP4
- Bewegungs-Klänge fuer die vorhandenen Einheiten sind eingebunden und der Demo-Export erzeugt jetzt einen Audio-Track
- Gefechte haben jetzt ebenfalls Soundeffekte, getrennt nach Land-, Luft- und Seegefecht
- der Demo-Capture zeigt jetzt eine laengere, nachvollziehbare Sequenz mit Szenariowahl, Pfadvorschau, Bewegung, Save/Load und sichtbaren Gefechten
- visuelles Flackern der Map waehrend Bewegungsanimationen behoben: movementLayer war faelschlicherweise Kind des Grid-Items und hat das Layout verformt; Zustandsupdates werden jetzt atomar als einzelnes boardSnapshot-Objekt gesetzt
- einfacher KI-Gegner fuer Spieler 2 eingebaut: bewegt Einheiten auf naechste feindliche/neutrale Stadt zu, greift angrenzende Gegner an, setzt Produktion automatisch; KI-Zug laeuft nach End-Turn automatisch durch mit Overlay-Anzeige
- Tests für Kernregeln

- Verifiziert zuletzt:
- `.venv/bin/pytest -q` -> `49 passed`
- `.venv/bin/python -m compileall main.py game tests`
- Offscreen-QML-Load und `capture-demo` erfolgreich
- Bewegungsanimation ohne Map-Blanking verifiziert
- KI-Gegner spielt Spieler 2 automatisch nach End-Turn
- aktualisierte Demo unter `captures/demo-launcher-ingame.mp4`

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

## Naechster sinnvoller Schritt

- Game-Over-Screen verbessern: Winner-Banner mit Neustart-Option
- Produktion in der UI direkt per Stadtklick setzbar machen
- mindestens 2-3 Szenarien aus JSON laden statt hardcodiert

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
