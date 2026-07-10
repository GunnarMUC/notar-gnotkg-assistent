# Implementierungsanleitung für Coding-Agents – Notar GNotKG Assistent

**Ziel dieses Dokuments**: Ein Coding-Agent (Cursor, Claude Artifacts, Aider, Windsurf, OpenDevin etc.) soll mit diesem Briefing-Paket in der Lage sein, die komplette App eigenständig und korrekt zu implementieren.

**Wichtige Prinzipien für die Umsetzung**:
1. **Human-in-the-Loop ist nicht optional** – jede KI-Extraktion muss editierbar und bestätigungspflichtig sein.
2. **Gebührenbeträge dürfen niemals vom LLM berechnet werden** – nur die Fee Engine (deterministisch).
3. **Auditierbarkeit hat höchste Priorität**.
4. Lean halten – zuerst MVP, dann erweitern.
5. Alles auf Deutsch (UI-Texte, Fehlermeldungen, Rechnungen, Logs).

---

## Phase 0: Projekt-Setup (Grundgerüst)

### 0.1 Projekt initialisieren
```bash
mkdir notar-gnotkg-app
cd notar-gnotkg-app
uv init --python 3.12
uv add streamlit ollama pydantic pydantic-settings pymupdf pytesseract python-docx pandas openpyxl jinja2 httpx loguru sqlalchemy
# ggf. weitere
```

Erstelle folgende Ordnerstruktur:
```
notar-gnotkg-app/
├── app.py
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── document_parser.py
│   ├── llm_extractor.py
│   ├── fee_engine.py
│   ├── invoice_generator.py
│   ├── excel_logger.py
│   ├── gnotkg_checker.py
│   └── config.py
├── prompts/
│   └── extraction_v1.txt
├── templates/
│   └── invoice_template.md          # oder .html / .docx-Template
├── data/
│   ├── notary_profile.json
│   └── fee_tables/
│       └── v2026_01.json            # Beispiel für versionierte Tabellen
├── history/                         # wird zur Laufzeit angelegt
├── tests/
├── docker/
└── README.md (bereits vorhanden)
```

### 0.2 Pydantic-Modelle (`core/models.py`)
Definiere klare Modelle:
- `ExtractedPosition`
- `InvoicePosition` (final bestätigt)
- `NotaryProfile`
- `GeneratedInvoice`
- `AuditLogEntry`

Verwende `Field(..., description=...)` für gute LLM-Outputs.

---

## Phase 1: Dokumenten-Parsing

**Datei**: `core/document_parser.py`

**Anforderungen**:
- Funktion `parse_document(file_path: str) -> ParsedDocument`
- `ParsedDocument` enthält: `full_text`, `pages`, `metadata`, `extraction_quality` (enum: good / ocr_fallback / poor)
- Für PDF: `pymupdf` zuerst versuchen (Text + Layout). Bei sehr wenig Text → OCR mit `pytesseract`.
- OCR nur bei Bedarf (Konfigurations-Flag).
- Deutsche Sprache für Tesseract hart codieren (`lang='deu'`).
- Fehlerbehandlung: Bei totalem Fehlschlag → klare Fehlermeldung + Möglichkeit manueller Texteingabe.

**Tipp**: Gute Hilfsfunktion zum Konvertieren von PDF-Seiten in Bilder für OCR.

---

## Phase 2: LLM-Extraktion mit Structured Output

**Datei**: `core/llm_extractor.py`

**Kernfunktion**:
```python
def extract_from_text(
    text: str,
    model: str = "qwen2.5:14b-instruct-q5_K_M",
    temperature: float = 0.1
) -> ExtractionResult:
```

**Wichtige Techniken**:
- Verwende Ollama mit `format="json"` + Pydantic-Modell.
- Bei Fehlschlag: Retry mit angepasstem Prompt (max. 2–3 Versuche).
- System-Prompt + Few-Shot-Examples stark in `prompts/extraction_v1.txt` auslagern (siehe `LLM_PROMPTS.md`).
- Das LLM soll **nur vorschlagen** – keine finalen Beträge berechnen.

**Output-Modell** (Beispiel):
```python
class ExtractedPosition(BaseModel):
    kv_number: str | None = Field(..., description="z.B. '21200' oder 'KV 21200'")
    description: str
    business_value_eur: float | None
    source_reference: str          # "Seite 3, Absatz 2" oder "Ziffer 4.1"
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
```

`ExtractionResult` enthält Liste von Positionen + erkannte Mandanten + allgemeine Hinweise.

---

## Phase 3: Fee Engine (deterministisch)

**Datei**: `core/fee_engine.py` – **Höchste Priorität & Sorgfalt**

**Design**:
- Klasse `FeeEngine` mit Versions-String (z. B. `"GNotKG_Stand_2026-01-01_v1"`)
- Interne Datenstruktur: JSON oder Python-Dicts mit den aktuellen Tabellenwerten (Anlage 2).
- Methoden:
  - `calculate_fee(kv_number: str, business_value: float, **kwargs) -> FeeCalculation`
  - `get_available_kv_numbers() -> list[str]`
  - `validate_combination(positions: list[...]) -> list[str]` (Warnungen bei unüblichen Kombinationen)

**Für MVP**:
- Implementiere zuerst 5–8 häufige Tatbestände exakt (z. B. Beurkundung Immobilienkauf, GmbH-Gründung, Testament, Grundschuld, Vollzug, Betreuung).
- Verwende die offiziellen Tabellenwerte (gestaffelte Beträge).
- Für komplexere Fälle: Placeholder + klare Fehlermeldung „Diese Kombination bitte manuell prüfen“.

**Wichtig**:
- Die Fee Engine **darf nie** vom LLM aufgerufen werden.
- Alle Beträge müssen exakt mit der offiziellen Tabelle übereinstimmen (Nachrechnen mit Beispielen aus notar.de oder gnotkg.de).

---

## Phase 4: Invoice Generator

**Datei**: `core/invoice_generator.py`

- Funktion `generate_invoice(final_positions: list[InvoicePosition], notary: NotaryProfile, ...) -> GeneratedInvoice`
- Verwende `python-docx` für DOCX (empfohlen).
- Für RTF: Entweder Pandoc aufrufen oder einfachen Text + später Konvertierung.
- Template-Ansatz: Basis-Layout in Jinja2 oder direkt im Code aufbauen (Header, Tabelle, Summen, Footer mit Disclaimer).
- Integriere immer:
  - Aktuelle Fee-Engine-Version
  - Erstellungsdatum
  - Deutlichen Haftungshinweis

---

## Phase 5: Excel Logger & Audit

**Datei**: `core/excel_logger.py`

- Bei jeder erfolgreichen Rechnungserstellung einen neuen Eintrag erzeugen.
- Struktur:
  - Ein Haupt-Sheet „Übersicht“
  - Ein Detail-Sheet pro Rechnung (benannt nach Rechnungs-ID)
- Verwende `openpyxl` für Formatierung (Farben für Overrides, fette Summen, etc.).
- Speichere zusätzlich eine JSON-Version des vollständigen Audit-Logs (einfacher zu parsen).

---

## Phase 6: GNotKG Checker

**Datei**: `core/gnotkg_checker.py`

Einfache, robuste Implementierung:
```python
def check_gnotkg_version() -> GnotkgStatus:
    # httpx.get("https://www.gesetze-im-internet.de/gnotkg/")
    # BeautifulSoup oder regex für "Stand: DD.MM.YYYY"
    # Vergleich mit local_version
```

Bei Abweichung: `status = "OUTDATED"` + Warnmeldung für die UI.

---

## Phase 7: Streamlit UI (`app.py`)

**Empfohlener Aufbau** (Single-File zuerst, später aufteilen):

```python
import streamlit as st
from core import ...

st.set_page_config(page_title="Notar GNotKG Assistent", layout="wide")

# Sidebar: Notar-Profil + LLM-Auswahl + GNotKG-Status
# Hauptbereich:
# 1. Upload-Bereich
# 2. Nach erfolgreichem Parse: "Extraktion starten" Button
# 3. st.data_editor() für die extrahierten / finalen Positionen (live update)
# 4. Separate Section für Auslagen + Gesamtsumme-Vorschau
# 5. Button "Rechnung generieren" (nach Bestätigung)
# 6. Download-Buttons für alle Formate + Excel-Log
```

**Wichtige Streamlit-Patterns**:
- `st.session_state` für den aktuellen Workflow-Zustand
- `st.data_editor` mit `on_change` Callback → sofortige Neuberechnung
- `st.columns` für gutes Layout (Original-Vorschau | Editier-Tabelle)
- Gute Error- und Success-Messages
- Deutliche visuelle Unterscheidung: „KI-Vorschlag“ vs. „Final bestätigt“

---

## Phase 8: Datenpersistenz & Config

- `data/notary_profile.json` (einfach lesbar/schreibbar)
- SQLite in `data/notar_app.db` für History + Audit
- Tabellen: `invoices`, `audit_logs`, `positions`
- Config via `pydantic-settings` + `.env` oder JSON

---

## Phase 9: Error Handling, Logging & Disclaimer

- Überall klare, deutsche Fehlermeldungen.
- `loguru` für strukturierte Logs (auch in Datei).
- In jeder generierten Rechnung und im UI ein klarer Disclaimer:
  > „Diese Rechnung wurde mit Unterstützung eines KI-Tools erstellt. Die alleinige Verantwortung für die Richtigkeit und die Einhaltung des Gerichts- und Notarkostengesetzes (GNotKG) liegt beim Notar.“

---

## Phase 10: Testing & Qualitätssicherung

- Mindestens:
  - Unit-Tests für die Fee Engine (mit bekannten Beispielen aus der Praxis)
  - Integrationstests für Extraction → Fee Engine → Invoice
  - Manuelle Tests mit 5–10 anonymisierten realen Urkunden verschiedener Typen
- Edge-Cases dokumentieren: Sehr hohe/niedrige Werte, ungewöhnliche Tatbestände, schlechte OCR-Qualität.

---

## Empfohlene Reihenfolge der Implementierung (praktisch)

1. Projekt-Setup + Modelle
2. Document Parser (ohne OCR zuerst)
3. Streamlit-Grundgerüst mit Upload + Dummy-Daten
4. Fee Engine (mit 4–5 Tatbeständen) + Invoice Generator (DOCX)
5. LLM Extractor + Prompts
6. Integration Extraction → editierbare Tabelle → Fee Engine
7. Excel Logger + Audit
8. GNotKG Checker + Notar-Profil
9. Polish, Error-Handling, Disclaimer, Tests

---

**Nach Fertigstellung des MVP**:
- Ausführliche Tests mit echten Urkunden
- Feedback-Schleife mit Notar
- Erweiterung der Fee Engine auf weitere häufige Tatbestände
- Verbesserung der Prompts anhand realer Fehler

---

Du (der Coding-Agent) hast jetzt alle notwendigen Informationen.  
Beginne mit Phase 0 und arbeite dich systematisch durch. Bei Unklarheiten zu GNotKG-Details oder Beispielen: Die Briefing-Dateien `FEE_CALCULATION_LOGIC.md` und `LLM_PROMPTS.md` enthalten weitere Hinweise.

Viel Erfolg – die App wird Notaren helfen und gleichzeitig höchste rechtliche Standards einhalten.