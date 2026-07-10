# Architektur – Notar GNotKG Assistent

## Überblick (High-Level)

Die App folgt einer **klaren, modularen, lokalen Architektur** mit starker Trennung von Verantwortlichkeiten:

- **LLM-Schicht** nur für semantische Extraktion und Vorschläge (nicht für Berechnungen)
- **Deterministische Core-Engine** für alle rechtlich relevanten Berechnungen
- **Thin UI** (Streamlit) als interaktive Schicht mit starker Human-in-the-Loop-Kontrolle
- **Lokale Persistenz** ohne jegliche Cloud-Abhängigkeit (außer optionalem GNotKG-Check)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app.py)                     │
│  Upload → Vorschau → Editierbare Tabelle → Vorschau Rechnung    │
│  + Notar-Profil + Historie + Einstellungen                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Document      │     │ LLM Extractor   │     │ Fee Engine       │
│ Parser        │────▶│ (structured)    │────▶│ (deterministisch)│
│ (PDF/OCR/...) │     │                 │     │                  │
└───────────────┘     └─────────────────┘     └────────┬─────────┘
                                                       │
        ┌──────────────────────────────────────────────┼──────────┐
        ▼                                              ▼          ▼
┌──────────────────┐                          ┌────────────────┐  │
│ Invoice          │                          │ Excel Logger   │  │
│ Generator        │                          │ (Traceability) │  │
│ (DOCX/RTF/TXT)   │                          └────────────────┘  │
└──────────────────┘                                              │
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    ▼
            ┌───────────────┐
            │ Local Storage │
            │ (SQLite + FS) │
            └───────────────┘
```

## Komponenten im Detail

### 1. Document Parser (`core/document_parser.py`)
- Unterstützt: PDF (Text + Layout), DOCX, RTF, TXT
- Fallback-OCR mit `pytesseract` + deutschem Sprachpaket für gescannte Dokumente
- Ausgabe: Strukturierter Text + Metadaten (Seitenanzahl, Extraktionsqualität)
- Optional: Erweiterte Parser wie `docling` für bessere Struktur

### 2. LLM Extractor (`core/llm_extractor.py`)
- Verwendet Ollama Python-Client
- Structured Output via Pydantic-Modelle (JSON Mode + Validation + Retry)
- Liefert:
  - Erkannte Tatbestände / KV-Nummern-Vorschläge
  - Extrahierte Geschäftswerte mit Quellenangabe (Seite/Absatz)
  - Beteiligte Personen
  - Confidence / Unsicherheits-Flags
- **Kein direkter Aufruf der Fee-Engine** – nur Vorschläge

### 3. Fee Engine (`core/fee_engine.py`) – **Kritischste Komponente**
- **Rein deterministisch** (kein LLM)
- Implementiert:
  - Werttabellen aus Anlage 2 GNotKG (Tabelle B)
  - Ausgewählte Tatbestände aus Kostenverzeichnis (Anlage 1)
  - Wertvorschriften (§§ 95 ff. GNotKG)
  - Kombinationsregeln (z. B. Beurkundung + Vollzug + Betreuung)
- Versioniert (z. B. `FeeEngineV2026_01`)
- Einfache Update-Möglichkeit bei Gesetzesänderungen (JSON + Python-Funktionen)
- Gibt für jede Position exakten Betrag + Begründung zurück

### 4. Invoice Generator (`core/invoice_generator.py`)
- Erzeugt professionelle Honorarrechnung
- Pflichtinhalte nach GNotKG § 19 / allgemeine Anforderungen:
  - Bezeichnung des Geschäfts
  - Angewandte KV-Nummern
  - Geschäftswert(e)
  - Einzelbeträge + Summe
  - Auslagen + Pauschalen
  - USt (derzeit 19 %)
  - Notar-Stammdaten
- Formate: DOCX (primär, editierbar), RTF, TXT
- Verwendet Jinja2-Templates + `python-docx`

### 5. Excel Logger (`core/excel_logger.py`)
- Erstellt pro Rechnung ein strukturiertes Excel (oder zentrales Log)
- Vollständige Traceability:
  - Welcher extrahierte Wert aus welcher Stelle der Urkunde
  - Welche KV-Nr / Paragraph
  - LLM-Modell + Version + Timestamp
  - User-Overrides
  - Finale bestätigte Werte
- Ermöglicht lückenlose Nachvollziehbarkeit für interne Revision oder bei Nachfragen

### 6. GNotKG Checker (`core/gnotkg_checker.py`)
- Beim App-Start: HTTP-Request an `https://www.gesetze-im-internet.de/gnotkg/`
- Extrahiert aktuelles „Stand:“-Datum
- Vergleich mit lokal gespeicherter Version
- Bei Abweichung: Deutliche Warnung + Hinweis auf manuelles Update der Fee-Engine

### 7. UI Layer (Streamlit)
- Single-File- oder modularer Aufbau (`app.py` + `pages/`)
- Interaktive Elemente:
  - Datei-Upload
  - Editierbare `st.data_editor` für extrahierte Positionen
  - Echtzeit-Neuberechnung bei Änderungen
  - Vorschau der Rechnung
  - Download-Buttons
- Starke visuelle Trennung: KI-Vorschlag vs. finale bestätigte Werte

## Datenfluss (typischer Use-Case)

1. Notar lädt Urkunde hoch
2. Parser → strukturierter Text
3. LLM Extractor → strukturierte Vorschläge (Pydantic)
4. UI zeigt Vorschläge in editierbarer Tabelle
5. Notar prüft, korrigiert, ergänzt Auslagen
6. Bei jeder Änderung → Fee Engine recalculates
7. Notar bestätigt finale Positionen
8. Invoice Generator erzeugt Dokument(e)
9. Excel Logger schreibt vollständigen Audit-Eintrag
10. Dateien stehen zum Download bereit + werden archiviert

## Design-Prinzipien

- **Human-in-the-Loop by Design**: Keine vollautomatische Rechnungserstellung
- **Deterministisch wo rechtlich relevant**: Gebührenbeträge niemals vom LLM
- **Auditierbarkeit first**: Jeder Schritt nachvollziehbar
- **Lean & Maintainable**: Wenige Abhängigkeiten, klare Module
- **Privacy by Design**: Alles lokal, minimale Daten, keine unnötigen Logs
- **Erweiterbar**: Fee-Engine und Prompts leicht aktualisierbar

## Technische Schnittstellen

- Ollama API (localhost:11434)
- Lokales Dateisystem + SQLite
- Optional: Pandoc für RTF-Konvertierung (System-Tool)

## Skalierbarkeit & Zukunft

Die Architektur ist bewusst für **Einzelnotar / kleine Kanzlei** ausgelegt.  
Spätere Erweiterungen (Batch, Mandanten-DB, Multi-User via lokales Netzwerk) sind modular möglich, ohne die Kernprinzipien zu verletzen.

---

**Nächste Schritte für die Umsetzung**: Siehe `IMPLEMENTATION_INSTRUCTIONS.md`