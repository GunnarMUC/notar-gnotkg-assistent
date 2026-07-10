# Nicht-funktionale Anforderungen – Notar GNotKG Assistent

## 1. Performance & Effizienz

### NFR-P01: App-Startzeit
- App-Start (Streamlit) inklusive GNotKG-Versions-Check: **< 5 Sekunden** bei normaler Internetverbindung
- Ohne Internetverbindung (Offline): **< 2 Sekunden** (Timeout des GNotKG-Checks wird abgefangen)

### NFR-P02: Dokument-Parsing
- PDF-Parsing (Text-Modus): **< 3 Sekunden** für Dokumente bis 50 Seiten
- OCR-Fallback (gescanntes PDF): **< 30 Sekunden** für 10 Seiten (auf Apple Silicon M-Serie)
- Fortschrittsanzeige bei OCR-Verarbeitung

### NFR-P03: LLM-Extraktion
- Extraktion einer Urkunde (bis 10.000 Tokens): **< 30 Sekunden** mit Qwen2.5-14B auf Apple Silicon M-Serie
- Bei > 30 Sekunden: Spinner mit Statusmeldung
- Abbruch-Möglichkeit für den Nutzer

### NFR-P04: Gebührenberechnung (Fee Engine)
- Berechnung einer Position: **< 50 ms** (sollte instantan wirken)
- Neuberechnung der gesamten Tabelle nach Edit: **< 200 ms**

### NFR-P05: Rechnungsgenerierung
- DOCX-Generierung (1–10 Positionen): **< 2 Sekunden**
- Excel-Traceability-Log: **< 3 Sekunden**

---

## 2. Zuverlässigkeit & Fehlertoleranz

### NFR-R01: Graceful Degradation
- Bei nicht erreichbarem Ollama: Klare Fehlermeldung mit Hinweis zur Fehlerbehebung (Ollama gestartet? Modell vorhanden?), manuelle Texteingabe als Fallback
- Bei fehlgeschlagenem GNotKG-Check: Warnung, aber App bleibt nutzbar (Offline-Modus)
- Bei PDF-Parsing-Fehler: Fallback auf manuelle Texteingabe

### NFR-R02: Datenintegrität
- SQLite mit WAL-Mode für Crash-Sicherheit
- Erstellte Rechnungen und Logs sofort auf Platte persistieren (nicht nur im Speicher)
- Keine Datenverluste bei App-Absturz (Streamlit-Session-States sind flüchtig – finalisierte Daten immer persistieren)

### NFR-R03: Eingabevalidierung
- Alle Benutzereingaben validieren vor Speicherung/Weitergabe
- Pflichtfelder im Notar-Profil hervorheben
- Geschäftswerte: Akzeptiere nur positive Zahlen, sinnvolle Ober- und Untergrenzen (1 € – 500.000.000 €)
- Datei-Upload: Größenbeschränkung auf 50 MB (typische Urkunden sind < 5 MB)

---

## 3. Sicherheit

### NFR-S01: Netzwerkisolation
- **Keine ausgehenden Verbindungen** außer:
  - `localhost:11434` (Ollama API)
  - `gesetze-im-internet.de` (optionaler GNotKG-Check, einmalig beim Start)
- Keine Telemetrie, kein Crash-Reporting, kein Tracking
- Docker-Container: `network_mode: host` oder explizites Port-Mapping nur für Ollama

### NFR-S02: Authentifizierung & Zugriff
- **Keine Benutzer-Authentifizierung** erforderlich (lokale Single-User-App)
- Streamlit-App läuft standardmäßig nur auf `localhost:8501`
- Optionaler Passwort-Schutz für Streamlit (empfehlen in DEPLOYMENT.md dokumentieren)

### NFR-S03: Datensicherheit
- Alle Daten (Urkunden, Profile, Rechnungen, Logs) ausschließlich im lokalen Dateisystem
- Keine Cloud-Speicherung, keine Uploads an Dritte
- SQLite-Datenbank im App-Datenverzeichnis (`data/`)
- Gitignore: `data/history/`, `data/notar_profile.json`, `data/notar_app.db`

### NFR-S04: Secrets Management
- Keine hartcodierten Secrets, API-Keys oder Tokens im Code
- Notar-Profil (IBAN, Steuernummer) in `data/notary_profile.json` – Zugriff nur lokal
- `.env`-Datei für optionale Konfiguration (Ollama-Host, Port etc.) – nicht ins Git-Repo

---

## 4. Datenschutz & DSGVO-Konformität

### NFR-D01: Datenminimierung
- App speichert nur das absolut Notwendige:
  - Notar-Profil (einmalig)
  - Generierte Rechnungen (Archiv)
  - Audit-Logs (Abrechnungszwecke)
- Keine Speicherung ganzer Urkundentexte über die aktuelle Session hinaus (konfigurierbar)

### NFR-D02: Datenhoheit
- Notar hat volle Kontrolle über alle gespeicherten Daten
- Export-Funktion für alle gespeicherten Rechnungen (Massendownload)
- Lösch-Funktion für Historie (einzelne Einträge oder alles)

### NFR-D03: Verarbeitungsverzeichnis
- Klarer Hinweis in Dokumentation, welche Daten wie verarbeitet werden
- Keine personenbezogenen Daten verlassen das lokale Gerät (außer sie sind in der generierten Rechnung selbst)

---

## 5. Usability & Benutzerfreundlichkeit

### NFR-U01: Zielgruppengerechte UI
- Alle UI-Texte auf Deutsch
- Klare, juristisch bekannte Begriffe (GNotKG, KV-Nr., Geschäftswert)
- Minimaler Trainingsaufwand: Notar soll ohne Handbuch arbeiten können

### NFR-U02: Fehlervermeidung & Assistenz
- Undo-Funktion in editierbarer Tabelle (oder Warnung vor unbeabsichtigten Änderungen)
- Plausibilitäts-Checks mit Warnhinweisen (z. B. „Geschäftswert 45.000.000 € – entspricht das tatsächlich Ihrer Urkunde?“)
- Tooltipps zu KV-Nummern und Berechnungsgrundlagen

### NFR-U03: Barrierefreiheit (Grundlegend)
- Ausreichende Schriftgrößen (≥ 14px)
- Kontrastreiche Farbgestaltung (KI-Vorschlag vs. bestätigt)
- Tastatur-Navigation in editierbarer Tabelle (via Streamlit/HTML)

### NFR-U04: Feedback & Status
- Eindeutige Status-Indikatoren:
  - Grün: Berechnung erfolgreich, bestätigt
  - Gelb: KI-Vorschlag, ungeprüft, Warnung
  - Rot: Fehler, kritische Warnung
- Fortschrittsbalken bei längeren Operationen (OCR, LLM-Extraktion)

---

## 6. Kompatibilität & Plattformen

### NFR-C01: Primärplattform macOS
- Entwickelt und getestet auf macOS 14+ (Sonoma) und 15+ (Sequoia) auf Apple Silicon (M1–M4)
- Ollama nativ auf macOS (Metal-Beschleunigung)
- Streamlit-Betrieb im Standard-Browser (Safari, Chrome, Firefox)

### NFR-C02: Sekundärplattformen
- Linux (Ubuntu 22.04+, Debian 12+): Grundsätzlich lauffähig mit Anpassungen (Ollama läuft nativ)
- Windows: Lauffähig mit WSL2 (Ollama im WSL2, Streamlit ebenfalls)
- Docker: Primär für Linux/macOS; auf Apple Silicon ohne Ollama im Container (Trennung empfohlen)

### NFR-C03: Browser
- Safari 17+, Chrome 120+, Firefox 120+ (aktuelle Versionen)
- Streamlit unterstützt alle gängigen Browser nativ

---

## 7. Wartbarkeit & Erweiterbarkeit

### NFR-M01: Modularer Code
- Klare Trennung in `core/`-Module mit definierten Schnittstellen
- Fee-Engine und Prompts unabhängig aktualisierbar
- Jede Komponente einzeln testbar (Unit-Tests)

### NFR-M02: Versionierung
- Fee-Engine: Versioniert mit GNotKG-Stand-Datum (z. B. `v2026_01`)
- Prompts: Versioniert in `prompts/extraction_vX.txt`
- App-Version in `pyproject.toml` oder `__init__.py`
- Jede generierte Rechnung enthält die verwendeten Versionen (Fee-Engine + LLM + Prompt)

### NFR-M03: Konfigurierbarkeit
- Alle Pfade und Parameter über `pydantic-settings` + `.env` oder JSON konfigurierbar
- Keine hartcodierten Pfade (außer Defaults)

### NFR-M04: Abhängigkeiten
- Minimale Anzahl an externen Abhängigkeiten
- Alle Abhängigkeiten mit konkreten Versionen in `pyproject.toml` oder `requirements.txt` gepinnt
- Regelmäßiger Dependency-Update-Check (Dependabot/Renovate empfohlen)

---

## 8. Testbarkeit & Qualitätssicherung

### NFR-T01: Unit-Tests
- Fee-Engine: 100 % Testabdeckung der Berechnungslogik (kritischstes Modul)
- Ausreichende Tests mit echten Praxis-Beispielen (aus Beispielurkunden und notar.de)

### NFR-T02: Integrationstests
- End-to-End-Test: Urkunde (TXT) → Extraktion → Fee-Engine → Rechnung
- Mit verschiedenen Urkundentypen aus `Beispielurkunden/`

### NFR-T03: Testdaten
- 15 Beispielurkunden in `Beispielurkunden/txt/` als Test-Fixtures nutzbar
- Anonymisierte, realistische Daten aus Grundstückskauf und Testament

---

## 9. Dokumentation

### NFR-DOC01: Code-Dokumentation
- Alle öffentlichen Funktionen mit Docstrings (auf Python-Ebene)
- Deutsche Kommentare für business-relevante Logik

### NFR-DOC02: Nutzerdokumentation
- Vollständige Installations- und Nutzungsanleitung (`DEPLOYMENT.md`)
- Erklärungen zu GNotKG-Grundlagen in der App (Tooltipps, Hilfe-Button)
- Disclaimer rechtssicher und prominent

---

## 10. Auditierbarkeit & Compliance

### NFR-A01: Traceability
- Jeder Berechnungsschritt muss nachvollziehbar sein (siehe `FR-06` in `FUNCTIONAL_SPECIFICATION.md`)
- Excel-Log enthält: Quelle → KV-Nr → Geschäftswert → Berechnungsformel → Endergebnis
- Bei manuellen Overrides: Vorher/Nachher dokumentiert

### NFR-A02: Revisionssicherheit
- Append-Only-Log (`audit_full.jsonl`) im Dateisystem
- Jeder Audit-Eintrag mit Timestamp, Version und Nutzer-Aktion
- Löschungen nur durch explizite Nutzeraktion, nicht automatisch

### NFR-A03: GNotKG-Konformität
- Umsetzung der gesetzlichen Anforderungen an die Kostenberechnung (§ 19 GNotKG)
- Rechtsbehelfsbelehrung in jeder Rechnung (§ 7a GNotKG)
- Disclaimer zur Verantwortung des Notars (§ 17 BNotO)
