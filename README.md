# Notar GNotKG Assistent

> **Der erste lokale KI-Assistent für deutsche Notare – gebührenrechtlich korrekt, datenschutzsicher und transparent.**

[![CI](https://github.com/GunnarMUC/notar-gnotkg-assistent/actions/workflows/ci.yml/badge.svg)](https://github.com/GunnarMUC/notar-gnotkg-assistent/actions)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)](tests/)
[![Security Audit](https://img.shields.io/badge/security%20audit-passed-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Semgrep](https://img.shields.io/badge/semgrep-0%20findings-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Gitleaks](https://img.shields.io/badge/gitleaks-0%20leaks-brightgreen)](SECURITY_AUDIT_REPORT.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-lightgrey)](https://www.apple.com/mac/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## Das Problem

Honorarrechnungen nach dem Gerichts- und Notarkostengesetz (GNotKG) sind komplex, fehleranfällig und zeitaufwändig. Gleichzeitig dürfen sensible Urkundeninhalte **nicht** in Cloud-KI-Dienste wandern, und Gebührenbeträge müssen juristisch exakt sein.

## Die Lösung

Ein **lokaler, DSGVO-konformer Desktop-Assistent**, der Urkunden mit einem lokalen LLM (Ollama) versteht, Geschäftswerte und KV-Nummern vorschlägt und Gebühren **deterministisch exakt** berechnet. Die KI entscheidet niemals über Beträge – das übernimmt eine auditierte Python-Engine.

---

## Innovation & Alleinstellungsmerkmale

| Innovation | Warum es zählt |
|------------|----------------|
| **🧠 Lokales LLM + deterministische Engine** | KI extrahiert Fakten, Python berechnet Gebühren. Keine Halluzinationen bei Beträgen. |
| **⚖️ Human-in-the-Loop als Pflicht** | Jede KI-Vorschlagsposition muss vom Notar geprüft und bestätigt werden. |
| **🔒 Privacy by Design** | 100 % lokal. Keine Cloud, keine Telemetrie, keine Dokumenten-Uploads. |
| **🛡️ Verschlüsseltes Notar-Profil** | IBAN, Steuernummer & Co. werden mit einem Master-Passwort (Fernet/PBKDF2) gesichert. |
| **📊 Revisionssicheres Excel-Log** | Jede Rechnung erhält ein Traceability-Log: Wert → Paragraph → Gebühr. |
| **🗂️ Versionierte Gebührentabellen** | GNotKG-Tabelle B und KV-Definitionen als strukturierte JSON-Dateien zukunftssicher hinterlegt. |
| **🍎 Native Apple-Silicon-Performance** | Empfohlen mit Ollama auf macOS M-Serie für maximale Geschwindigkeit. |

---

## Schnellstart

```bash
# 1. Ollama installieren
# https://ollama.com

# 2. Modell pullen
ollama pull qwen2.5:14b-instruct-q5_K_M

# 3. Projekt einrichten
git clone https://github.com/GunnarMUC/notar-gnotkg-assistent.git
cd notar-gnotkg-assistent
uv sync

# 4. App starten
streamlit run app.py
```

Danach unter `http://localhost:8501` öffnen.

---

## Kernfunktionen

- **Urkunden-Upload**: PDF (mit OCR), DOCX, RTF, TXT
- **KI-Extraktion**: Geschäftswerte, Beteiligte, KV-Nummern per lokalem LLM
- **Interaktive Prüfung**: Editierbare Positionstabelle mit Confidence-Score
- **Deterministische Berechnung**: GNotKG-Anlage 2 (Tabelle B) exakt nach dem Gesetz
- **Rechnungserstellung**: DOCX, RTF oder TXT
- **Audit-Trail**: Automatisches Excel-Traceability-Log pro Rechnung
- **GNotKG-Aktualitäts-Check**: Abgleich mit gesetze-im-internet.de beim Start
- **Notar-Profil**: Einmalig einrichten, optional verschlüsselt speichern

---

## Architektur

```text
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Urkunde    │────▶│  Lokales LLM      │────▶│  Vorschlag     │
│  (PDF/...)  │     │  (Ollama)         │     │  Positionen    │
└─────────────┘     └──────────────────┘     └────────────────┘
                                                       │
                                                       ▼
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Rechnung   │◀────│  Fee Engine       │◀────│  Notar prüft  │
│  + Excel-Log│     │  (deterministisch)│     │  & bestätigt   │
└─────────────┘     └──────────────────┘     └────────────────┘
```

Trennung von KI und Berechnung ist das zentrale Sicherheitsprinzip: das LLM liest und schlägt vor, die Engine rechnet.

---

## Sicherheit & Compliance

- **Keine Cloud**: Alle Verarbeitung findet auf dem lokalen Rechner statt.
- **Keine Hardcoded Secrets**: Verifiziert durch Gitleaks.
- **SAST & Dependency Audit**: Semgrep und pip-audit in der CI.
- **Verschlüsselung**: Optionale AES-verschlüsselte Speicherung des Notar-Profils.
- **DSGVO-konform**: Datenminimierung, lokale Speicherung, kein Datenverarbeitungsvertrag mit Dritt-Anbietern nötig.

Details im [Security Audit Report](SECURITY_AUDIT_REPORT.md) und [SECURITY.md](SECURITY.md).

---

## Projektstruktur

```text
notar-gnotkg-assistent/
├── app.py                  # Dünner Streamlit-Einstieg
├── core/                   # Geschäftslogik
│   ├── fee_engine.py       # Deterministische GNotKG-Berechnung
│   ├── document_parser.py  # PDF/DOCX/RTF/TXT + OCR
│   ├── llm_extractor.py    # Ollama-Extraktion
│   ├── invoice_generator.py
│   ├── excel_logger.py
│   ├── gnotkg_checker.py
│   └── profile_crypto.py   # Profilverschlüsselung
├── ui/                     # Streamlit-UI-Komponenten
├── data/fee_tables/        # Versionierte JSON-Gebührentabellen
├── prompts/                # System-Prompts + Few-Shots
├── tests/                  # 63 Tests, 91 % Coverage
└── SECURITY_AUDIT_REPORT.md
```

---

## Roadmap

- [x] MVP mit lokalem LLM + deterministischer Fee Engine
- [x] Profilverschlüsselung + Sicherheitsaudit
- [x] CI/CD mit Qualitätssicherung, SAST & Dependency-Audit
- [ ] Weitere KV-Nummern aus dem Kostenverzeichnis
- [ ] Rechnungs-Templates (HTML/Jinja2)
- [ ] SQLite-basierte Historie + Volltextsuche
- [ ] Beta-Test bei Notarkanzleien

---

## Lizenz & Haftung

MIT License. Die Software ist ein Assistenztool. Die alleinige Verantwortung für die Richtigkeit und die Einhaltung des GNotKG liegt stets beim Notar (§ 17 BNotO).

---

**Erstellt für**: Deutsche Notare, lokaler Einsatz auf macOS (Apple Silicon), lauffähig unter Linux/Windows.
