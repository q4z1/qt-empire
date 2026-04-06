# Architecture

## Kernprinzip

Das Projekt ist strikt in zwei Schichten getrennt:

1. `game/logic`
   Enthält alle Spielregeln und den vollständigen Game-State.
   Diese Schicht ist headless, testbar und darf nichts über Qt, QML oder UI-Objekte wissen.

2. `game/ui`
   Enthält Darstellung, Interaktion und Qt/QML-Integration.
   Diese Schicht darf nur Daten aus der Engine lesen und Befehle über die API zurückgeben.

## Zielarchitektur

Die Python-Engine ist ein Vorläufer für einen späteren C++-Port.
Deshalb gelten diese Regeln:

- keine Qt-Abhängigkeiten in der Logik
- keine Python-Magie oder dynamischen Laufzeittricks
- portierbare Datenstrukturen
- möglichst explizite, deterministische Algorithmen

## Datenfluss

Die UI spricht nicht direkt mit internen State-Objekten, sondern mit einer schmalen API.

Aktuelle Engine-API:
- `create_game()`
- `load_game(path)`
- `get_visible_state()`
- `select_unit(unit_id)`
- `move_unit(unit_id, target_position)`
- `end_turn()`

Diese API liefert nur einfache Daten zurück, aktuell in Dict-/List-Form.
Der sichtbare State enthält inzwischen auch UI-taugliche Aktionsdaten wie `legal_targets`, die aber weiterhin vollständig in der Engine berechnet werden.

## Aktuelle Logikmodule

[`game/logic/models.py`](/home/min/Development/empire/game/logic/models.py)
- einfache Datamodelle wie `Position`, `Unit`, `Tile`, `MapSize`
- `Tile` traegt jetzt auch persistierte Stadtrollen wie `city`, `factory` oder `harbor`

[`game/logic/state.py`](/home/min/Development/empire/game/logic/state.py)
- zentraler `GameState`
- Tile- und Unit-Verwaltung
- Sichtberechnung und Exploration
- Persistenzformat für Vollstate
- Rueckfall-Ableitung von Stadtrollen wie `city` und `harbor` fuer Legacy-State ohne explizites Rollenfeld
- traegt jetzt auch `game_over` und `winner_id` fuer einfache Siegbedingungen

[`game/logic/rules.py`](/home/min/Development/empire/game/logic/rules.py)
- Einheitenwerte
- Terrainbewegung
- Kampfauflösung
- Transportkapazität und Domain-Regeln
- Produktionskonstanten und erlaubte Stadt-Bauoptionen je Stadtrolle
- Reparatur-/Versorgungswerte fuer Staedte
- Sonderwerte fuer `capital` wie groessere Sicht und staerkere Reparatur

[`game/logic/scenarios.py`](/home/min/Development/empire/game/logic/scenarios.py)
- Aufbau mehrerer vordefinierter Szenarien und Szenariometadaten

[`game/logic/api.py`](/home/min/Development/empire/game/logic/api.py)
- stabile Kommandoschicht zwischen Engine und UI
- JSON Save/Load für headless Nutzung und GUI
- Produktionslogik und Capture erhalten Stadtrollen explizit mit
- prueft jetzt auch eine erste Siegbedingung ueber verbliebene `capital`-Staedte
- enthaelt jetzt auch einfache Pfadsuche fuer entfernte Bewegungsziele
- liefert ausserdem eine Engine-berechnete Pfadvorschau fuer das aktuell gehoverte Ziel
- die Vorschau unterscheidet zwischen vollem geplanten Pfad und dem in dieser Runde erreichbaren Teil

## Aktuelle UI-Module

[`game/ui/controller.py`](/home/min/Development/empire/game/ui/controller.py)
- Qt-Bridge zwischen QML und Engine
- keine Regeln, nur Weiterleitung und State-Update
- erzeugt auch einen frischen Spielzustand für "Neues Spiel"
- bindet Quick Save / Quick Load an einen festen Projektpfad

[`game/ui/demo_capture.py`](/home/min/Development/empire/game/ui/demo_capture.py)
- headless Capture-Helfer fuer kurze UI-Demos
- rendert Frames direkt aus dem QML-Fenster und kodiert sie mit `ffmpeg` zu MP4
- bildet inzwischen einen laengeren, skriptbaren Showcase-Ablauf fuer Launcher und Gameplay ab

[`game/ui/qml/Main.qml`](/home/min/Development/empire/game/ui/qml/Main.qml)
- Startmenü und Spielansicht in einer einfachen Screen-Struktur
- Karten- und Statusdarstellung
- Eingabe per Klick
- Darstellung von Fog of War
- Transport- und Cargo-Informationen
- Einheiten- und Stadt-Icons aus lokalen SVG-Assets
- Stadtliste mit einfacher Produktionsauswahl

## Architekturregeln für kommende Änderungen

- Neue Regeln immer zuerst in `game/logic` implementieren
- UI nur erweitern, um neue Zustandsdaten anzuzeigen
- Tests für Regelverhalten ergänzen, bevor UI-spezifische Details bewertet werden
- API möglichst stabil halten
- Jede neue Mechanik so formulieren, dass sie später in C++ ohne konzeptionellen Umbau portiert werden kann

## Aktuelle Interaktionsregel Auswahl

Die GUI berechnet keine legalen Züge selbst.
Stattdessen liefert die Engine für die selektierte Einheit eine Liste `legal_targets` mit:

- Zielposition
- Aktionstyp wie `move`, `attack`, `embark`, `disembark`
- kurzer Label-Text für UI/Debug

Damit bleibt die Regeldefinition zentral in `game/logic/api.py`.

## Aktueller UI-Flow

Die UI besitzt jetzt einen einfachen Startzustand:

- Startmenü als initialer Screen
- `Spiel starten` erzeugt einen frischen Engine-State
- `Spiel starten` nutzt das aktuell gewählte Szenario aus dem Startmenü
- `Spiel laden` lädt aktuell einen Quick-Save aus dem Projektordner
- `Einstellungen` ist weiter Platzhalter
- Spielansicht kann über einen `Menu`-Button wieder verlassen werden

Dieser Flow liegt vollständig in QML/Controller und verändert keine Regeln in der Engine.

## Aktuelle Interaktionsregel Transport

Das erste Transportmodell bleibt absichtlich klein:

- Land-Einheit bewegt sich auf benachbartes eigenes `transport`-Feld: Einheit steigt ein
- transportierte Einheit bleibt im State erhalten, ist aber nicht als Karten-Occupant sichtbar
- transportierte Einheit kann über `move_unit` wieder auf ein benachbartes gültiges Landfeld aussteigen
- ein `transport` kann alternativ beim Klick auf ein benachbartes Landfeld seine erste geladene Einheit entladen

Das Modell ist bewusst pragmatisch und noch nicht final Empire-Deluxe-genau.

## Nächste Architekturfragen

- Sichtsystem nur radiusbasiert oder später mit Linien-/Terrainblockern?
- Produktionssystem pro Stadt fix oder konfigurierbare Bauaufträge?
- Kampfmodell als einfacher deterministischer Wertvergleich oder näher an Empire Deluxe?
- Transport-/Carrier-System als frühe Basiskomponente oder später?

## Aktueller Wiedereinstieg

Der zuletzt bearbeitete Schwerpunkt war Bewegung und Bewegungs-UX:

- entfernte Ziele koennen bereits per Pfadsuche angeklickt werden
- die Engine liefert eine Pfadvorschau mit vollem Pfad, erreichbarem Teil und Stopppunkt
- QML rendert diese Vorschau nur noch, berechnet aber keine Route selbst

Der naechste logische Architektur-Schritt waere:

- gemerktes Bewegungsziel pro Einheit oder pro Auswahl
- automatisches Weiterlaufen ueber mehrere Zuege
- weiterhin strikt in `game/logic`, ohne Routenlogik in QML zu duplizieren
