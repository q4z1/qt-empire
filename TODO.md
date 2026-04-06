# TODO

## Kurzfristig

- GUI lokal interaktiv weiter prüfen und Layout iterativ verbessern
- Fernbewegung ueber mehrere Zuege mit gemerktem Ziel bauen
- Fernbewegung spaeter mit optionalem Klick-zu-Bestaetigen oder kleiner Schrittanimation pruefen
- rechte Seitenleiste weiter verfeinern: Gruppierung, kompaktere Cards, bessere Scroll-Indikatoren
- Menü und Statusbereich weiter atmosphärisch schärfen
- Tooltip-/Hover-System später noch gezielter für Einheiten, Städte und Produktion ausbauen
- CLI-Demo verkleinern, damit sie nicht den kompletten Kartenstate ausgibt
- sichtbaren State optional kompakter serialisieren
- Tooltips oder klarere Legende für Zielmarkierungen ergänzen
- optional Einheit abwählen und Hover-Infos für Aktionsfelder ergänzen
- Startmenü ausbauen: Dateiauswahl für Laden/Speichern, Einstellungen, Szenarioauswahl
- Szenarioauswahl weiter ausbauen: Vorschaubilder, Schwierigkeitsgrad, Fraktionen
- Terrain-Icons oder detailliertere Terrain-Darstellung später ergänzen
- Demo-Capture spaeter noch weiter ausbauen: weichere Kamera-/Ablaufwechsel und gezielte Kampf-/Transport-Szenen

## Regeln als Nächstes

- Bewegung zuerst fertigziehen, bevor neue groessere Regelsysteme dazukommen
- differenzierteres Produktionssystem mit mehr Bautypen und echten Werften
- Produktionsoberflaeche weiter ausbauen: Kosten, Bauzeit, Stadtrolle klarer darstellen
- Stadtrollen weiter ausbauen: Harbor/Factory weiter spezialisieren, dazu Hauptstadt
- Hauptstadt-Regeln spaeter weiter ausbauen: Sonderproduktion, Nachschub, klarere Eroberungs- und Niederlageeffekte
- weitere Einheitentypen
- klareres Kampfsystem in Richtung Empire Deluxe
- bessere Transportregeln: gezielte Cargo-Auswahl, mehrere Ladungstypen, Carrier/Transporter unterscheiden
- Versorgung/Reparatur weiter differenzieren: nur bestimmte Einheitentypen, Nachschub, Hafenlogik
- Siegbedingungen
- Siegbedingungen ueber reine Hauptstadt-Eroberung hinaus ausbauen

## Mittelfristig

- Fog of War weiter ausbauen
- AI-Grundgerüst
- Szenario-/Map-Loader statt fest kodierter Testkarte
- Trennung zwischen internem Vollstate und explizitem View-State noch klarer herausziehen
- Save/Load-Format versionieren und stabilisieren

## Qualität

- mehr Tests für Sicht, Produktion und Kampfketten
- Regressionstests für API-Verhalten
- optional Snapshot-Tests für sichtbaren UI-State

## Langfristig

- API stabilisieren und einfrieren
- C++-Port der Engine vorbereiten
- Python- und C++-API strukturell angleichen
- Performancekritische Teile identifizieren
