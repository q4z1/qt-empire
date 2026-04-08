# TODO

Ziel: vollständig spielbares Empire-Spiel (Einzelspieler + Hot-Seat).
Einträge sind grob nach Priorität innerhalb jeder Kategorie sortiert.

---

## Pflicht für Release (Blocker)

### KI
- einfacher KI-Spieler: Einheiten zu feindlichen Städten bewegen und angrenzende Gegner angreifen
- KI nutzt vorhandene `move_unit`/`end_turn`-API, keine Sonderrechte
- KI-Zug in der UI sichtbar machen: kurze Pause oder Zusammenfassung, bevor der Spieler wieder dran ist
- KI-Schwierigkeitsgrad: zumindest "einfach" und optional "mittel" (aggressivere Pfadwahl)

### Produktion
- Produktions-UI klar und direkt zugänglich: Klick auf eigene Stadt öffnet Bauauftrag-Auswahl
- aktueller Bauauftrag und Fortschritt sichtbar auf der Karte oder in der Sidebar
- Produktion ohne Stadtrolle (leere Stadt) sollte nutzbar sein oder klar erklären warum nicht

### Züge & Rundenfluss
- klare "Spieler X ist dran"-Anzeige beim Zugwechsel (Banner oder Modal)
- KI-Zug darf nicht interaktiv sein: Klicks während KI-Phase ignorieren oder blocken

### Spielende
- Game-Over-Anzeige ausbessern: klarer Winner-Screen mit Zusammenfassung statt nur Header-Text
- Neustart-Möglichkeit direkt aus dem Game-Over-Zustand heraus

### Karten & Szenarien
- mindestens 2-3 spielbare Szenarien unterschiedlicher Größe
- Szenario-Loader aus JSON-Datei statt nur hardcodierter Szenarien
- Startmenü zeigt Szenariobeschreibung und Kartengröße an

### Save/Load
- mehrere Speicherslots oder Dateiauswahl (nicht nur Quicksave)
- Laden aus dem Hauptmenü heraus

---

## Soll für Release (wichtig, kein harter Blocker)

### Einheiten & Kampf
- Lufteinheiten: `bomber` (Angriff auf Land/See) und `fighter` (Luftüberlegenheit/Abfang)
- Artillerie-Balancing finalisieren: Gegenfeuerwerte und Reichweite 3 prüfen
- Transportregeln verbessern: gezielte Cargo-Auswahl, Carrier vs. Transport unterscheiden
- Versorgung/Reparatur differenzieren: Hafenlogik für Seeeinheiten, Depots für Landeinheiten

### Stadtrollen & Produktion
- Harbor/Factory/Capital-Rollen weiter spezialisieren: welche Einheiten, welche Kosten
- Bauzeit sichtbar (Züge bis fertig) und in der Sidebar anzeigen
- leere Städte neutral/feindlich klar unterscheiden, Produktion erst nach Eroberung starten

### Fog of War
- Sichtradius abhängig von Einheitentyp klar sichtbar in der UI
- entdeckte aber aktuell unsichtbare Einheiten als "zuletzt gesehen"-Phantome anzeigen
- Fog-Grenze schärfer oder mit leichtem Verlauf darstellen

### Spielfluss
- Einheit kan abgewählt werden (Klick ins Leere oder Escape)
- "Alle Einheiten bewegt"-Hinweis am Rundenende: noch unbewegte Einheiten hervorheben
- Einheitenliste in der Sidebar anklickbar: Klick springt zur Einheit auf der Karte

---

## Nice-to-have (nach Release)

### KI
- stärkere KI: koordinierter Angriff, Verteidigung der Hauptstadt, Produktionspriorität
- verschiedene KI-Persönlichkeiten (aggressiv, defensiv, wirtschaftlich)

### Karten
- einfacher Karten-Editor oder Textformat für eigene Maps
- prozedurale Kartengenerierung als Alternative

### UI & Theme
- weitere Terrain-Varianten und feinere Küstenlinien
- zweites vollständiges Theme als Alternative zu Empire Deluxe
- Einheitendetail-Panel mit Stats beim selektieren

### Sonstiges
- Hot-Seat-Multiplayer: Bildschirm abdecken beim Spielerwechsel
- optionale Rundenzeit-Begrenzung
- Replay-Funktion auf Basis des Zuglogs
- CLI-Demo kompakter serialisieren

---

## Qualität (laufend)

- Tests für KI-Verhalten (deterministisch durch Seed)
- mehr Tests für Produktion, Sicht und Kampfketten
- Save/Load-Format versionieren
- API einfrieren und dokumentieren bevor C++-Port beginnt

---

## Langfristig / Post-Release

- C++-Port der Engine vorbereiten
- Python- und C++-API strukturell angleichen
- Performancekritische Pfade identifizieren (Pfadsuche, Sichtberechnung)
