# Notar GNotKG Assistent – Lokale App für deutsche Notare

[![CI](https://github.com/GunnarMUC/notar-gnotkg-assistent/actions/workflows/ci.yml/badge.svg)](https://github.com/GunnarMUC/notar-gnotkg-assistent/actions)
[![Security Audit](https://img.shields.io/badge/security%20audit-passed-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Semgrep](https://img.shields.io/badge/semgrep-0%20findings-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Gitleaks](https://img.shields.io/badge/gitleaks-0%20leaks-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-lightgrey)](https://www.apple.com/mac/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Status](https://img.shields.io/badge/status-MVP%20ready-success)](UMSETZUNGSREPORT.md)

> **Lokale, DSGVO-konforme Desktop-App zur Erstellung GNotKG-konformer Honorarrechnungen aus Urkunden mit Hilfe eines lokalen LLMs (Ollama).**

**Ziel**: Schlanke, sichere, offline-fähige Assistenz-App für Notare. Die App extrahiert relevante Werte aus Urkunden (PDF, DOCX, RTF, TXT), schlägt passende Positionen aus dem Kostenverzeichnis vor, berechnet Gebühren **deterministisch exakt** nach aktueller GNotKG und erzeugt prüfbare Honorarrechnungen (RTF/DOCX/TXT) sowie ein vollständiges Excel-Traceability-Log.

**Wichtig**: Die App ist ein **Assistenz-Tool**. Die finale Prüfung, Verantwortung und Haftung liegen immer beim Notar (§ 17 BNotO, GNotKG).

---

## Kernfunktionen (MVP + erweitert)

- Upload von Urkunden (PDF mit/ohne OCR, DOCX, RTF, TXT)
- Intelligente Extraktion relevanter Geschäftswerte, Beteiligter und Tatbestände per lokalem LLM
- Vorschlag passender KV-Nummern aus dem Kostenverzeichnis (Anlage 1 GNotKG)
- **Deterministische, exakte Gebührenberechnung** nach Anlage 2 (Tabelle B) und Wertvorschriften
- Editierbare Zwischentabelle mit Human-in-the-Loop (Pflicht!)
- Generierung GNotKG-konformer Honorarrechnung (RTF / DOCX / TXT)
- Automatisches, revisionssicheres Excel-Log mit vollständiger Traceability (welcher Wert → welcher Paragraph → welche Gebühr)
- Automatischer GNotKG-Aktualitäts-Check beim Start (Abgleich mit gesetze-im-internet.de)
- Lokales Notar-Profil (einmalig einrichten)
- Vollständig lokal & offline-fähig (außer optionaler GNotKG-Check)
- Docker-Option für Reproduzierbarkeit + native Ollama-Empfehlung für Apple Silicon

---

## Tech-Highlights

- **LLM**: Ollama (nativer macOS-Betrieb auf M-Serie für beste Performance)
- **Modelle**: Frei wählbar, empfohlen ≥ 12B (z. B. Qwen2.5-14B-Instruct Q5/Q6 oder vergleichbar)
- **UI**: Streamlit (einfach, interaktiv, lokal im Browser)
- **Berechnung**: Reine Python-Logik (keine LLM-Halluzinationen bei Beträgen!)
- **Plattform**: Primär macOS (MacBook Pro M-Serie), lauffähig unter Linux/Windows mit Anpassungen
- **Datenschutz**: 100 % lokal, keine Cloud, keine Telemetrie, SQLite + Dateisystem

---

## Schnellstart (für Entwickler / Test)

```bash
# 1. Ollama installieren (nativer macOS Installer empfohlen)
# https://ollama.com

# 2. Modell pullen (Beispiel)
ollama pull qwen2.5:14b-instruct-q5_K_M

# 3. Projekt klonen / entpacken
cd notar-gnotkg-app

# 4. Python-Umgebung (uv empfohlen)
uv sync
# oder: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 5. App starten
streamlit run app.py
```

Danach im Browser unter `http://localhost:8501` öffnen.

**Vollständige Installations- und Nutzungsanleitung** siehe `DEPLOYMENT.md`.  
**Testdaten**: 15 fiktive Musterurkunden (Grundstückskauf + Testamente) in `Beispielurkunden/` (TXT, RTF, HTML).
**GNotKG-Volltext**: Parsbares XML (Stand: 10.12.2025) in `Gesetze/BJNR258610013 3.xml`.

---

## Ordnerstruktur (Ziel)

```
notar-gnotkg-app/
├── app.py                      # Haupt-Streamlit-App
├── core/
│   ├── __init__.py
│   ├── fee_engine.py           # Deterministische GNotKG-Berechnung
│   ├── document_parser.py      # PDF/DOCX/RTF → Text + OCR
│   ├── llm_extractor.py        # LLM-gestützte Extraktion (structured output)
│   ├── invoice_generator.py    # RTF/DOCX/TXT Erzeugung
│   ├── excel_logger.py         # Traceability-Excel
│   ├── gnotkg_checker.py       # Update-Check der GNotKG
│   └── models.py               # Pydantic-Modelle
├── prompts/
│   └── extraction_prompt.txt   # System-Prompt + Few-Shots
├── templates/
│   ├── invoice_template.html   # oder Jinja2 für DOCX
│   └── ...
├── data/
│   ├── notary_profile.json
│   ├── fee_tables/             # Versionierte Tabellen (JSON)
│   └── history/                # SQLite + generierte Dateien
├── tests/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── Beispielurkunden/
│   ├── txt/                       # 15 Muster-Urkunden (Plaintext)
│   ├── rtf/                       # 15 Muster-Urkunden (RTF)
│   └── html/                      # 15 Muster-Urkunden (HTML/Quelle)
├── Gesetze/
│   ├── GNotKG.pdf                 # GNotKG-Volltext (PDF)
│   └── BJNR258610013 3.xml        # GNotKG-Volltext (XML, parsbar)
├── README.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
├── NON_FUNCTIONAL_REQUIREMENTS.md
├── ... (weitere Briefing-Dateien)
└── requirements.txt / pyproject.toml
```

---

## Wichtige Hinweise für die Umsetzung

Dieses Briefing-Paket enthält alle notwendigen Spezifikationen, damit ein Coding-Agent (Cursor, Claude, Aider, OpenDevin etc.) die App vollständig implementieren kann.

**Reihenfolge der Umsetzung (empfohlen)**:
1. Projekt-Setup + Pydantic-Modelle
2. Dokumenten-Parsing + OCR
3. Streamlit-Grundgerüst mit Upload + Dummy-Daten
4. Fee-Engine (deterministisch, zuerst mit 5–8 häufigen Tatbeständen) + Invoice-Generator (DOCX)
5. LLM-Extraktion mit structured output + Prompts
6. Integration: Extraktion → editierbare Tabelle → Fee Engine → Rechnung
7. Excel-Logging + Traceability
8. GNotKG-Checker + Notar-Profil
9. Polish, Error-Handling, Disclaimer, Tests

**Kritische Prinzipien**:
- **Keine LLM-Berechnung von Gebührenbeträgen** – nur Extraktion + Vorschlag.
- Jede KI-Extraktion **muss** vom Notar editierbar und bestätigbar sein.
- Maximale Transparenz und Auditierbarkeit.
- Lean & wartbar halten (keine Over-Engineering).

---

## Status & Roadmap (Stand Briefing-Erstellung)

- [ ] MVP-Definition abgeschlossen
- [ ] Briefing-Paket für Coding-Agent erstellt
- [ ] Umsetzung durch Coding-Agent
- [ ] Test mit realen (anonymisierten) Urkunden
- [ ] Beta bei Notar(en)
- [ ] Release & Wartungskonzept (Fee-Engine-Updates bei Gesetzesänderungen)

---

## Lizenz & Haftung

Die App wird als Open-Source- oder interne Kanzlei-Lösung entwickelt.  
**Haftungsausschluss**: Die generierten Rechnungen und Berechnungen sind Vorschläge. Der Notar ist für die Richtigkeit und die Einhaltung des GNotKG verantwortlich.

---

**Erstellt**: Juli 2026  
**Für**: Lokalen Einsatz auf macOS (Apple Silicon)  
**Kontakt / Weiterentwicklung**: [Deine Angaben hier einfügen]

Viel Erfolg bei der Umsetzung! Die App hat echtes Potenzial, den Alltag von Notaren spürbar zu erleichtern, während sie die gesetzlichen Anforderungen erfüllt.