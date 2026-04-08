# TODO

## Kurzfristig

- GUI lokal interaktiv weiter prüfen und Layout iterativ verbessern
- rechte Seitenleiste weiter verfeinern: Gruppierung, kompaktere Cards, bessere Scroll-Indikatoren
- Theme-System weiter ausbauen: weitere Empire-Deluxe-Details, eventuell weitere Skins und bessere Karten-Texturen
- Theme-System weiter ausbauen: Stadt- und Küstendetails, vielleicht stärkere Tile-Kontraste und weitere Terrain-Varianten
- Theme-System weiter ausbauen: Uferverlaeufe, Kuestenlinien und ggf. distincte Meer- vs. Flussoptik
- Theme-System weiter ausbauen: weitere Skins als echte Alternativen ergänzen
- Theme-System weiter ausbauen: weitere Varianten fuer Strassen, Flusslaeufe und Uferkanten
- Theme-System weiter ausbauen: weitere Varianten fuer forest, mountain und city
- Theme-System weiter ausbauen: feinere Unterschiede zwischen den Varianten, etwa Stadtgrenzen, Wegkreuzungen oder Uferwechsel
- Theme-System weiter ausbauen: UI-Palette noch genauer auf Empire-Deluxe-Atmosphaere trimmen
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
- Artillerie-Regeln weiter ausbauen: Gegenfeuer-Feintuning und Reichweitenbalance
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
