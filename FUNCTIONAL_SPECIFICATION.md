# Funktionale Spezifikation – Notar GNotKG Assistent

## 1. Zielgruppe & Use-Cases

**Primäre Nutzer**: Deutsche Notare (Einzelnotare oder kleine Kanzleien) auf macOS (Apple Silicon).

**Haupt-Use-Case**:
Ein Notar hat eine frisch beurkundete Urkunde (meist PDF) und möchte schnell eine korrekte, GNotKG-konforme Honorarrechnung erstellen, bei der alle verwendeten Werte transparent und nachvollziehbar sind.

**Weitere Use-Cases**:
- Erstellung von Rechnungen für verschiedene Tatbestände (Immobilienkauf, GmbH-Gründung, Testament, Vollmachten, Schenkung, Grundschuldbestellung etc.)
- Nachträgliche Korrektur / Ergänzung von Positionen
- Archivierung und Nachvollziehbarkeit für interne Zwecke oder bei Rückfragen von Mandanten / Gerichten
- Schnelle Prüfung, ob die aktuell verwendete GNotKG-Fassung noch gültig ist

## 2. Funktionale Anforderungen (MVP)

### FR-01: Dokumenten-Upload & Parsing
- Unterstützte Formate: `.pdf`, `.docx`, `.rtf`, `.txt`
- PDF: Text-Extraktion mit Layout-Erhaltung + automatischer OCR-Fallback bei rein gescannten Dokumenten
- Anzeige der Originaldatei (Öffnen im Standard-Programm oder eingebettete Vorschau)
- Metadaten-Erfassung (Dateiname, Upload-Zeitpunkt, Extraktionsqualität)

### FR-02: LLM-gestützte Extraktion
- Automatische Analyse des Dokumententextes durch lokales LLM
- Extraktion folgender Informationen (strukturiert):
  - Art des notariellen Geschäfts / Tatbestands
  - Relevante Geschäftswerte (mit genauer Bezeichnung und Quelle im Dokument)
  - Beteiligte Personen (Name, Rolle, ggf. Anschrift)
  - Vorgeschlagene Positionen aus dem Kostenverzeichnis (KV-Nummern)
  - Kurze Begründung / Herleitung der Vorschläge
- Rückgabe mit Confidence-Werten oder Unsicherheits-Flags
- Möglichkeit, mehrere alternative Interpretationen anzuzeigen (falls LLM unsicher)

### FR-03: Interaktive Bearbeitung & Human-in-the-Loop
- Darstellung aller vorgeschlagenen Positionen in einer editierbaren Tabelle
- Spalten (Beispiel):
  - KV-Nr.
  - Beschreibung / Tatbestand
  - Zugrunde liegender Geschäftswert (EUR)
  - Berechnete Gebühr (EUR) – **automatisch aktualisiert**
  - Quelle im Originaldokument (Seite / Absatz)
  - Bemerkung / Begründung
  - Override-Flag (wurde manuell geändert?)
- Sofortige Neuberechnung bei jeder Änderung durch den Notar
- Möglichkeit zum Hinzufügen / Löschen von Positionen
- Separate Eingabefelder für Auslagen, Pauschalen und sonstige Kosten
- Pflicht-Bestätigungsschritt: „Ich habe alle Positionen geprüft und bestätige die finale Rechnung“

### FR-04: Deterministische Gebührenberechnung (Fee Engine)
- Exakte Umsetzung der aktuellen GNotKG-Werttabellen (Anlage 2, Tabelle B für Notare)
- Unterstützung der wichtigsten Tatbestände aus dem Kostenverzeichnis (Anlage 1)
- Korrekte Anwendung von Wertvorschriften und Kombinationsregeln
- Automatische Berechnung von:
  - Einzelgebühren
  - Zwischensummen
  - Auslagen + Dokumentenpauschalen
  - Umsatzsteuer (derzeit 19 %)
  - Endbetrag brutto
- Versionierung der Fee-Engine mit klarem „Stand GNotKG“-Datum in jeder Rechnung

### FR-05: Erzeugung der Honorarrechnung
- Ausgabeformate wählbar: **DOCX** (primär), **RTF**, **TXT**
- Inhalt muss mindestens enthalten (gem. GNotKG-Anforderungen):
  - Bezeichnung des Verfahrens / Geschäfts
  - Angewandte Nummern des Kostenverzeichnisses
  - Geschäftswert(e) bei wertabhängigen Gebühren
  - Beträge der einzelnen Gebühren und Auslagen
  - Notar-Stammdaten (Name, Kanzlei, Adresse, Kontaktdaten)
  - Datum der Rechnung
  - Zahlungshinweis + Bankverbindung
  - Deutlicher Disclaimer zur Verantwortung des Notars
- Professionelles, sauberes Layout (Logo-Platzhalter, Tabellen, Summen hervorgehoben)
- Dateiname-Vorschlag: `Rechnung_[Mandant]_[Datum]_[Geschäft].docx`

### FR-06: Excel-Traceability-Log
- Automatische Erzeugung eines strukturierten Excel-Files bei jeder Rechnungserstellung
- Mindestinhalt:
  - Rechnungs-ID (UUID oder fortlaufend)
  - Erstellungszeitpunkt
  - Original-Urkunde (Dateiname + Hash)
  - LLM-Modell + Version + Parameter
  - Für jede Position: KV-Nr, Beschreibung, Wert, Quelle, berechnete Gebühr, Override-Status
  - Finale bestätigte Gesamtsumme
  - Notar, der bestätigt hat
- Ziel: Jeder Cent in der Rechnung ist lückenlos auf einen extrahierten Wert aus der Urkunde zurückverfolgbar

### FR-07: GNotKG-Aktualitäts-Check
- Beim Start der App (oder manuell triggerbar):
  - Abruf der Seite `https://www.gesetze-im-internet.de/gnotkg/`
  - Extraktion des aktuellen Stand-Datums der GNotKG
  - Vergleich mit der in der App hinterlegten Fee-Engine-Version
  - Bei Abweichung: Deutliche Warnung im UI + Hinweis, die Fee-Engine zu aktualisieren
- Die eigentliche Aktualisierung der Tabellen erfolgt manuell durch den Entwickler/Notar (Fee-Engine ist versioniert)

### FR-08: Notar-Profil & Einstellungen
- Einmalige Einrichtung eines lokalen Profils:
  - Name des Notars / der Notarin
  - Kanzleibezeichnung & Adresse
  - Telefon, E-Mail, Website
  - Bankverbindung (für Rechnung)
  - Steuernummer / USt-ID (falls relevant)
  - Optionales Logo (Base64 oder Dateipfad)
- Einstellungen:
  - Standard-LLM-Modell
  - Standard-Ausgabeformat
  - OCR standardmäßig aktiv?
  - Pfad für Archiv-Ordner
  - Aktuelle Fee-Engine-Version (readonly + Update-Hinweis)

### FR-09: Historie & Wiederverwendung
- Liste aller bisher erstellten Rechnungen (lokal)
- Suche / Filter nach Datum, Mandant, Tatbestand
- Möglichkeit, eine alte Rechnung zu laden, zu duplizieren oder neu zu generieren
- Zugriff auf die zugehörigen Excel-Logs und Original-Urkunden

## 3. Nicht-funktionale Anforderungen (kurz)

Siehe separate Datei `NON_FUNCTIONAL_REQUIREMENTS.md`.

## 4. Out-of-Scope für MVP (spätere Versionen)

- Vollautomatische Rechnungserstellung ohne Bestätigung
- Multi-User / Netzwerkbetrieb
- Direkte Integration in bestehende Notar-Software (z. B. via API)
- Automatische Aktualisierung der Fee-Tabellen bei Gesetzesänderungen (nur manuell)
- Mobile App / Web-Version
- Erweiterte Buchhaltungsexporte (DATEV etc.) – nur Excel-Log

---

**Diese Spezifikation ist die Grundlage für die Umsetzung.**  
Alle weiteren Briefing-Dateien bauen darauf auf.