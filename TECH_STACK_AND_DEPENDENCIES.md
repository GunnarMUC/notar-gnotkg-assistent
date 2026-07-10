# Tech-Stack & Abhängigkeiten – Notar GNotKG Assistent

## Primärer Tech-Stack (empfohlen für MVP)

| Bereich              | Technologie                          | Begründung / Alternativen                          | Version / Hinweis                  |
|----------------------|--------------------------------------|----------------------------------------------------|------------------------------------|
| **UI / Frontend**    | Streamlit                            | Einfach, interaktiv, Python-only, gute Komponenten für Tabellen & Downloads | Aktuellste stabile Version      |
| **LLM Runtime**      | Ollama (nativer macOS Installer)     | Beste Performance auf Apple Silicon (Metal), einfache Modellverwaltung | Neueste Version                    |
| **LLM Modelle**      | Qwen2.5-14B-Instruct (Q5/Q6) oder vergleichbar (Mistral-Nemo 12B etc.) | Gute Reasoning-Qualität bei 12–14B auf 24 GB RAM   | Quantisiert, context ≥ 16k–32k    |
| **Backend Language** | Python 3.11+                         | Ökosystem, LLM-Integration, Dokumenten-Libs        | 3.11 oder 3.12 empfohlen           |
| **Package Manager**  | `uv` (empfohlen) oder `pip`          | Sehr schnell, moderne Lockfiles                    | -                                  |
| **Dokumenten-Parsing** | `pymupdf` (fitz) + `pytesseract`   | Gute PDF-Qualität + OCR-Fallback                   | + `tesseract-ocr-deu` via Homebrew |
| **Strukturierte Ausgabe** | Pydantic v2 + Ollama structured output | Typsicher, Validierung, Retry-Logik             | -                                  |
| **Office-Generierung** | `python-docx`                       | Professionelle DOCX-Erstellung                     | Primär für Rechnungen              |
| **RTF**              | Pandoc (System) oder Fallback        | Gute Konvertierung von Markdown/HTML → RTF         | Optional, als System-Dependency    |
| **Excel**            | `pandas` + `openpyxl`                | Schöne formatierte, farbkodierte Traceability-Logs | -                                  |
| **Templates**        | Jinja2                               | Flexible Rechnungs-Templates                       | -                                  |
| **Datenbank**        | SQLite (via `sqlalchemy` oder direkt) | Einfach, lokal, ausreichend für History + Config   | Datei-basiert                      |
| **Web-Requests**     | `httpx`                              | Moderner Async-Client für GNotKG-Check             | -                                  |
| **Logging / Audit**  | `loguru`                             | Schönes, strukturiertes Logging                    | -                                  |
| **Konfiguration**    | `pydantic-settings` oder JSON/YAML   | Typsichere Config                                  | -                                  |
| **Testing**          | `pytest` + `pytest-mock`             | Standard für Python                                | -                                  |

## Docker (optional, für Dev & Reproduzierbarkeit)

- **Base Image**: `python:3.12-slim` oder `python:3.12-bookworm`
- **Ziel**: App im Container, **Ollama bleibt nativ** auf dem Mac (wegen Metal-Beschleunigung)
- `docker-compose.yml` mit Volume-Mounts für `data/`, `history/` und ggf. `ollama` Socket (falls gewünscht)
- **Hinweis**: Auf Apple Silicon Docker Desktop hat Ollama im Container derzeit keine gute GPU-Unterstützung → klare Trennung empfohlen.

## System-Abhängigkeiten (macOS)

```bash
# OCR
brew install tesseract tesseract-lang-deu

# Optional für RTF
brew install pandoc

# Python (via uv oder pyenv)
```

## Python Dependencies (pyproject.toml / requirements.txt Auszug)

```toml
[project]
dependencies = [
    "streamlit>=1.38",
    "ollama>=0.3",
    "pydantic>=2.8",
    "pydantic-settings>=2.4",
    "pymupdf>=1.24",
    "pytesseract>=0.3.10",
    "python-docx>=1.1",
    "pandas>=2.2",
    "openpyxl>=3.1",
    "jinja2>=3.1",
    "httpx>=0.27",
    "loguru>=0.7",
    "sqlalchemy>=2.0",
    # Optional
    # "docling>=2.0",      # Moderner PDF-Parser
    # "unstructured[pdf]>=0.15",
]
```

## Empfohlene Modelle (Stand 2026)

| Modell                        | Quantisierung     | RAM-Verbrauch (ca.) | Qualität für Extraktion | Bemerkung                     |
|-------------------------------|-------------------|---------------------|--------------------------|-------------------------------|
| Qwen2.5-14B-Instruct          | Q5_K_M / Q6_K     | ~10–12 GB           | Sehr gut                 | Aktuell stark empfohlen       |
| Mistral-Nemo 12B              | Q5/Q6             | ~8–10 GB            | Gut                      | Schnell                       |
| Llama-3.1-8B / 70B (falls verfügbar) | entsprechend | variabel            | Gut                      | Je nach Kontext               |

Der User kann im UI frei zwischen installierten Ollama-Modellen wechseln.

## Warum dieser Stack?

- **Maximale Lokalität & Performance** auf Apple Silicon
- **Minimale Komplexität** → schnelle Umsetzung eines MVP
- **Gute Developer Experience** (Streamlit, uv, Pydantic)
- **Rechtliche Sicherheit** durch deterministische Berechnung
- **Wartbarkeit** bei zukünftigen GNotKG-Änderungen

---

**Nächster Schritt**: Lies `FUNCTIONAL_SPECIFICATION.md` für die detaillierten Anforderungen.