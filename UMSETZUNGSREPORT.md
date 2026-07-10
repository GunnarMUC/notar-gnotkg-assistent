# Umsetzungsreport – Notar GNotKG Assistent

**Stand:** 10. Juli 2026  
**Repository:** [github.com/GunnarMUC/notar-gnotkg-assistent](https://github.com/GunnarMUC/notar-gnotkg-assistent)  
**Status:** MVP vollständig implementiert, 35 Tests grün, lauffähig

---

## 1. Ziel

Lokale, DSGVO-konforme Desktop-App für deutsche Notare zur Erstellung GNotKG-konformer Honorarrechnungen aus Urkunden (PDF, DOCX, RTF, TXT) mit Hilfe eines lokalen LLMs (Ollama). Die App ist vollständig offline-fähig (außer optionalem GNotKG-Aktualitäts-Check).

---

## 2. Umgesetzte Module

### 2.1 Architektur-Übersicht

```
app.py                          Streamlit-Hauptapp (4-Tab Workflow)
core/
├── __init__.py                 Package-Exports
├── config.py                   pydantic-settings (Ollama, App, Pfade)
├── models.py                   8 Pydantic-Modelle
├── document_parser.py          PDF/DOCX/RTF/TXT → ParsedDocument
├── llm_extractor.py            Ollama structured JSON → ExtractionResult
├── fee_engine.py               Deterministische GNotKG-Berechnung
├── invoice_generator.py        DOCX/RTF/TXT Erzeugung
├── excel_logger.py             Revisionssicheres Traceability-Excel
└── gnotkg_checker.py           Aktualitätsprüfung (gesetze-im-internet.de)
prompts/
└── extraction_v1.txt           LLM System-Prompt + Few-Shot Examples
tests/
├── test_fee_engine.py          17 Tests
├── test_document_parser.py      8 Tests
├── test_generator.py            4 Tests
└── test_models.py               6 Tests
```

### 2.2 Document Parser (`core/document_parser.py`)

| Format | Methode | Fallback |
|--------|---------|----------|
| PDF    | pymupdf (fitz) Text-Extraktion | OCR via pytesseract bei < 200 Zeichen Text |
| DOCX   | python-docx Paragraph-Extraktion | — |
| RTF    | Eigene RTF-Stripping-Engine (CP1252/UTF-8) | — |
| TXT    | UTF-8 Plaintext | — |

**Features:** Encoding-Detection (UTF-8 → CP1252 Fallback), Qualitäts-Metadaten (`good`/`ocr_fallback`/`poor`), Seitenzählung.

### 2.3 LLM Extractor (`core/llm_extractor.py`)

- **Ollama Integration** via `ollama` Python-Client
- **Structured Output:** `format="json"` + Pydantic-Validierung
- **Retry-Logik:** Bis zu 3 Versuche bei JSON-Fehlern
- **Markdown-Codeblock-Handling:** Extrahiert JSON aus ```json … ``` Blöcken
- **Temperatur:** Niedrig (default 0.1) für konsistente Extraktion
- **Fehlerbehandlung:** Ollama-Verbindungsfehler, JSON-Parse-Fehler

### 2.4 Fee Engine (`core/fee_engine.py`) — Kritischstes Modul

**Deterministische Berechnung** — keinerlei LLM-Aufrufe.

| Feature | Details |
|---------|---------|
| **Tabelle B** | 56 Staffeln (1.500 € – 60.000.000 €), lineare Extrapolation darüber |
| **KV-Nummern (MVP)** | 10 Tatbestände: 21200, 21201, 22110, 22114, 22125, 22200, 23300, 24102, 25100, 25200 |
| **Gebührentypen** | `value_based` (wertabhängig mit Rate × Tabelle), `flat` (Pauschalgebühr) |
| **Min/Max-Fees** | Konfigurierbare Unter- und Obergrenzen pro KV-Nr. |
| **Validierung** | Warnt bei fehlender Kombination (z.B. Beurkundung ohne Vollzug) |
| **Versionierung** | `GNotKG_Stand_2026-01-01_v1` |

**Beispiele:**
- KV 21200 (Beurkundung), 385.000 € → 1.060,00 € (1,0-fach Tabelle B)
- KV 22125 (Betreuung), 385.000 € → 2.120,00 € (2,0-fach)
- KV 23300 (Grundschuld), 300.000 € → 420,00 € (0,5-fach)
- KV 22114 (Elektr. Vollzug) → 15,00 € (Pauschal)

### 2.5 Invoice Generator (`core/invoice_generator.py`)

| Format | Bibliothek | Inhalt |
|--------|-----------|--------|
| **DOCX** | python-docx | Kopf (Notar), Tabelle (Positionen), Summen, Zahlungsinfo, Disclaimer |
| **RTF** | Eigenbau (RTF-Syntax) | Gleicher Inhalt, einfache Formatierung |
| **TXT** | Plaintext | Tabellarische Darstellung mit ASCII-Rahmen |

**Enthaltene Pflichtangaben (§ 19 GNotKG):** KV-Nr., Beschreibung, Geschäftswert, Gebührenbeträge, Summen, USt 19%, Zahlungsinfo, Rechtsbehelfsbelehrung, Disclaimer.

### 2.6 Excel Logger (`core/excel_logger.py`)

3-Sheet Traceability-Log pro Rechnung:
- **Sheet „Übersicht“:** Rechnungs-ID, Notar, Urkunde, Summen, Fee-Engine-Version
- **Sheet „Positionen“:** Alle Positionen mit Fundstelle, gelb markiert bei manuellen Änderungen
- **Sheet „Audit-Log“:** Timestamp, Aktion, Details (append-only)

### 2.7 GNotKG Checker (`core/gnotkg_checker.py`)

- HTTP-Request auf `gesetze-im-internet.de/gnotkg/`
- Extrahiert „Stand:“-Datum per Regex
- Vergleich mit lokaler Fee-Engine-Version
- Ausgabe: `is_current` (bool) + Warnungen bei Abweichung
- Graceful Degradation bei fehlender Internetverbindung

### 2.8 Streamlit-App (`app.py`)

**4-Tab Workflow:**

1. **📤 Upload** — Datei-Upload, Parse-Button, Text-Vorschau mit Qualitätsanzeige
2. **🔍 Extraktion** — LLM-Aufruf, Fortschrittsanzeige, Ergebnis-Anzeige (Positionen + Beteiligte)
3. **✏️ Prüfung** — `st.data_editor` für interaktive Bearbeitung, Live-Summe, Auslagen, Bestätigung
4. **📄 Rechnung** — Format-Auswahl, Generierung, Download-Buttons (Rechnung + Excel-Log)

**Sidebar:** Notar-Profil (speicherbar), LLM-Modell-Auswahl, GNotKG-Status.

---

## 3. Tests

**35 Tests, alle grün** (pytest):

| Test-Klasse | Anzahl | Fokus |
|-------------|--------|-------|
| `TestFeeEngineLookup` | 5 | Tabellen-Lookup (Staffeln, Grenzwerte) |
| `TestFeeEngineCalculate` | 8 | KV-Berechnung (wertabhängig, flat, min/max, unbekannt) |
| `TestFeeEngineTotals` | 1 | Gesamtsummen mit Auslagen + USt |
| `TestFeeEngineValidation` | 2 | Kombinationswarnungen |
| `TestFeeEngineKvList` | 1 | Verfügbare KV-Nummern |
| `TestParseTxt` | 2 | TXT-Parsing (Kaufvertrag, Testament) |
| `TestParseRtf` | 2 | RTF-Parsing, Trailing-Backslash-Test |
| `TestUnsupportedFormat` | 2 | Fehlerbehandlung (ungültiges Format, nicht existent) |
| `TestRtfStripping` | 2 | RTF-Command-Stripping, Hex-Escapes |
| `TestInvoiceGenerator` | 3 | TXT, DOCX, RTF Generierung |
| `TestExcelLogger` | 1 | Excel-Erstellung |
| `TestSettings` | 2 | Config-Defaults |
| `TestModels` | 4 | Pydantic-Modelle, Validierung |

---

## 4. Daten & Ressourcen

| Ressource | Umfang |
|-----------|--------|
| **Beispielurkunden** | 15 fiktive Urkunden in 3 Formaten (TXT/RTF/HTML): 8× Grundstückskauf, 7× Testament |
| **GNotKG-Text** | Vollständiger Gesetzestext als XML (`Gesetze/BJNR258610013 3.xml`) und PDF |
| **Prompt** | System-Prompt mit Rollendefinition, KV-Referenz, 2 Few-Shot-Beispielen (Kaufvertrag, Testament) |
| **Fee-Tabellen** | Tabelle B (Anlage 2) mit 56 Staffeln, 10 KV-Definitionen |

---

## 5. Projekt-Infrastruktur

| Datei | Zweck |
|-------|-------|
| `pyproject.toml` | Projekt-Metadaten, Dependencies, Build-System (hatchling) |
| `requirements.txt` | Pip-kompatible Dependency-Liste |
| `.env.example` | Beispiel-Konfiguration (Ollama, Streamlit, OCR) |
| `.gitignore` | Python, IDE, macOS, sensible Daten |
| `LICENSE` | MIT-Lizenz |
| `Dockerfile` + `docker-compose.yml` | Container-Betrieb (App im Container, Ollama nativ) |
| `uv.lock` | Gepinnte Abhängigkeiten (uv) |

---

## 6. Bekannte Einschränkungen (MVP)

- **Fee Engine:** 10 KV-Nummern implementiert (häufigste Fälle). Weitere KV-Nr. nach Bedarf ergänzbar.
- **RTF-Parsing:** Eigene Engine deckt die meisten Fälle ab; sehr komplexe RTF-Dokumente können Artefakte enthalten.
- **OCR:** Nur bei PDF mit wenig Text aktiviert; benötigt `tesseract` + deutsches Sprachpaket.
- **LLM:** Erfordert Ollama mit einem leistungsfähigen Modell (empfohlen ≥ 12B Parameter).
- **PDF mit Formularen/Signaturen:** Keine spezielle Behandlung von digitalen Signaturen oder Formularfeldern.
- **Multi-User:** Nicht unterstützt (lokale Single-User-App).

---

## 7. Offene Punkte / Nächste Schritte

### Kurzfristig (vor erstem Praxiseinsatz)

- [ ] Test mit 3–5 realen (anonymisierten) Urkunden eines Notars
- [ ] Fee-Engine-Werte gegen offizielle Tabelle und Referenzrechner (notar.de) validieren
- [ ] Prompt-Tuning anhand realer Extraktionsergebnisse
- [ ] `data/notary_profile.json` Gitignore prüfen (sensibel!)

### Mittelfristig (Beta-Phase)

- [ ] Erweiterung der Fee-Engine auf 20–30 KV-Nummern
- [ ] RAG-Erweiterung: Lokale Embeddings der KV-Nummern ins LLM injizieren
- [ ] Undo/Redo in der editierbaren Tabelle
- [ ] Batch-Verarbeitung mehrerer Urkunden
- [ ] Optionaler Passwort-Schutz für die Streamlit-App

### Langfristig (Release)

- [ ] Integration externer GNotKG-Kommentare als Referenz
- [ ] Automatische Tests mit GitHub Actions (CI)
- [ ] Signierte und gestempelte PDF-Rechnungen (falls rechtlich relevant)
- [ ] DATEV-Export (optional)
- [ ] Beitrag zur Notar-Community (Open Source?)

---

## 8. DevOps & Deployment

### Lokale Installation

```bash
uv sync
uv run streamlit run app.py
# → http://localhost:8501
```

Voraussetzungen: Python 3.12+, Ollama, Tesseract OCR (optional), Pandoc (optional).

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

App im Container, Ollama nativ auf dem Host (Metal-Beschleunigung auf Apple Silicon).

### CI/CD

Aktuell kein CI/CD eingerichtet. Empfohlen: GitHub Actions mit `pytest`, `ruff`, und optional `semgrep` + `gitleaks` (siehe `opencode_audit_readiness_instructions.md`).

---

## 9. Zusammenfassung

Der **Notar GNotKG Assistent** ist als MVP vollständig implementiert und lauffähig:

- **7 Core-Module** mit klarer Trennung der Verantwortlichkeiten
- **35 Tests** mit 100 % Erfolgsquote
- **15 Beispielurkunden** für Tests und Prompt-Tuning
- **Vollständig lokale Architektur** — keine Cloud, keine Telemetrie
- **DSGVO-konform** durch Design (Datenminimierung, lokale Verarbeitung)
- **Human-in-the-Loop** als zentrales Designprinzip (nicht optional)
- **Deterministische Fee-Engine** — keine LLM-Halluzinationen bei Beträgen

**Nächster Meilenstein:** Test mit realen Urkunden und Feedback-Schleife mit einem Notar.

---

*Erstellt am 10. Juli 2026 · GunnarMUC · [github.com/GunnarMUC/notar-gnotkg-assistent](https://github.com/GunnarMUC/notar-gnotkg-assistent)*
