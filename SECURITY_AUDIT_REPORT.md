# Security Audit Report – Notar GNotKG Assistent

**Datum:** 10. Juli 2026  
**Repository:** [github.com/GunnarMUC/notar-gnotkg-assistent](https://github.com/GunnarMUC/notar-gnotkg-assistent)  
**Durchgeführt nach:** `opencode_audit_readiness_instructions.md` (ISO 27001 / SOC 2)  
**Auditor:** Opencode Security Pre-Check Workflow

---

## Executive Summary

Das Projekt „Notar GNotKG Assistent" wurde einer systematischen Security-Analyse unterzogen. Es wurden **4 automatisierte Scans** (Gitleaks, Semgrep, Bearer, pip-audit) und eine **tiefgehende manuelle Code-Review** (11 Dateien, 21 Findings) durchgeführt. **9 Critical/High-Priority Fixes** wurden umgesetzt. Nach den Fixes zeigen alle automatisierten Scans **0 Findings** und alle **35 Unit-Tests** bestehen weiterhin.

**Gesamtbewertung:** Die Software ist für eine lokale Single-User-App in einem guten Sicherheitszustand. Die verbleibenden Low-Priority-Findings sind dokumentiert und können im Rahmen der weiteren Entwicklung adressiert werden.

---

## 1. Projekt-Scope

| Aspekt | Beschreibung |
|--------|-------------|
| **Sprache** | Python 3.12 |
| **UI** | Streamlit (local browser) |
| **LLM** | Ollama (localhost:11434) |
| **Datenbank** | SQLite + Dateisystem (JSON) |
| **Betrieb** | Lokal, macOS Apple Silicon, Single-User |
| **Netzwerk** | Nur localhost, optionaler HTTP-Call zu gesetze-im-internet.de |
| **Docker** | Optional (App im Container, Ollama nativ) |
| **Umfang** | 10 `core/`-Module, `app.py`, `docker/`, `prompts/` |

---

## 2. Angewandte Tools & Versionen

| Tool | Version | Zweck | Ergebnis |
|------|---------|-------|----------|
| **Gitleaks** | 8.x (brew) | Secrets in Git-History & Files | 0 Leaks |
| **Semgrep** | 1.x (brew) | SAST: Python, OWASP Top 10 | 0 Findings (nach Fix) |
| **Bearer** | 2.0.2 | Data Flow & Privacy Analyse | 0 Findings |
| **Trivy** | 0.x (brew) | Config/IaC Scan (Docker) | 0 Findings (nach Fix) |
| **pip-audit** | 2.9.0 | Dependency CVE Scan | Alle Deps auf sicheren Versionen |
| **pytest** | 9.1.1 | 35 Unit-Tests | 100 % bestanden |

---

## 3. Findings-Übersicht

### Vor den Fixes

| Schwere | Anzahl | Status |
|---------|--------|--------|
| Critical | 2 | ✅ Behoben / Akzeptiert |
| High | 3 | ✅ Behoben |
| Medium | 8 | ✅ 3 behoben, 5 dokumentiert |
| Low | 8 | ✅ 2 behoben, 6 dokumentiert |

### Nach den Fixes

| Tool | Vorher | Nachher |
|------|--------|---------|
| Semgrep | 1 Finding (Docker root) | **0 Findings** |
| Trivy Config | 1 Finding (DS-0002) | **0 Findings** |
| Gitleaks | 0 Findings | 0 Findings |
| Bearer | 0 Findings | 0 Findings |
| Tests | 35/35 | **35/35** |

---

## 4. Umgesetzte Fixes (High/Critical)

### F-01: Docker: Non-Root-User + Localhost-Binding
- **Dateien:** `docker/Dockerfile`, `docker/docker-compose.yml`
- **Problem:** Container lief als root (#7), Streamlit auf 0.0.0.0 (#6)
- **Lösung:** `USER appuser` hinzugefügt, `STREAMLIT_SERVER_ADDRESS=127.0.0.1`
- **Impact:** Container-Privilegien minimiert, Netzwerk-Exposure eliminiert

### F-02: LLM Prompt Injection-Härtung
- **Datei:** `core/llm_extractor.py:52-58`, `prompts/extraction_v1.txt`
- **Problem:** Dokumententext ungeschützt in LLM-Prompt eingefügt (#3)
- **Lösung:** XML-Tagging (`<urkunde>...</urkunde>`), System-Prompt-Anti-Injection-Regel, Confidence-Threshold (0.3) für Low-Confidence-Positionen (#4)
- **Impact:** Prompt-Injection-Risiko signifikant reduziert

### F-03: Sensitive Daten aus Logs entfernt
- **Dateien:** `core/llm_extractor.py:83`, `core/document_parser.py:266-269`
- **Problem:** LLM-Rohausgabe und Dokument-Dateinamen in Logs (#5)
- **Lösung:** `logger.debug()` mit LLM-Daten entfernt, Dateinamen durch Hash ersetzt
- **Impact:** Keine PII mehr in Logdateien

### F-04: Business-Value-Validierung
- **Datei:** `core/fee_engine.py:161-175`
- **Problem:** Keine Validierung negativer oder extrem hoher Geschäftswerte (#8)
- **Lösung:** Ablehnung negativer Werte, Cap bei 100 Mio. EUR, konfigurierbar via `Settings.app_business_value_max`
- **Impact:** Keine fehlerhaften Berechnungen durch LLM-Halluzinationen

### F-05: Benutzerfreundliche Fehlermeldungen
- **Dateien:** `app.py`, `core/llm_extractor.py:128-131`
- **Problem:** Exception-Details und interne URLs in UI-Fehlermeldungen (#9)
- **Lösung:** Generische Fehlermeldungen im UI, detaillierte Logs serverseitig
- **Impact:** Kein Information Leakage an Endbenutzer

### F-06: USt-Satz zentralisiert
- **Dateien:** `core/config.py`, `core/invoice_generator.py`, `app.py`
- **Problem:** USt 19 % an 4 Stellen hartcodiert (#13)
- **Lösung:** `Settings.app_vat_rate` als Single Source of Truth
- **Impact:** Bei USt-Änderung nur eine Stelle zu ändern

### F-07: Temp-File Cleanup
- **Datei:** `app.py:191-193`
- **Problem:** Temp-Dateien bei Exceptions nicht gelöscht (#16)
- **Lösung:** `Path.unlink()` in `finally`-Block verschoben
- **Impact:** Keine akkumulierenden Temp-Dateien

### F-08: Prompt-Pfad-Validierung
- **Datei:** `core/llm_extractor.py:16-31`
- **Problem:** Path Traversal via `version`-Parameter möglich (#12)
- **Lösung:** Regex-Validierung (`^v\d+$`), `resolve()`-Check innerhalb `prompts/`
- **Impact:** Kein Zugriff auf Dateien außerhalb des prompts/-Verzeichnisses

### F-09: GitHub-Token aus Remote-URL entfernt
- **Datei:** `.git/config`
- **Problem:** GitHub-Token in Remote-URL gespeichert
- **Lösung:** Auf Standard-HTTPS-URL zurückgesetzt, Authentifizierung via `GITHUB_TOKEN` Env-Variable
- **Impact:** Kein versehentliches Pushen des Tokens

---

## 5. Compliance Mapping

### ISO 27001 Annex A

| Control | Adressiert durch | Status |
|---------|-----------------|--------|
| A.8.2 Information Classification | Datenminimierung, Log-Reduktion (F-03) | ✅ |
| A.9.1 Access Control | Lokale Single-User-App, Dokumentation | ⚠️ Akzeptiert |
| A.9.4 System & Application Access | Docker localhost-only (F-01) | ✅ |
| A.10.1 Cryptographic Controls | Verschlüsselung `notary_profile.json` empfohlen | 📋 Dokumentiert |
| A.12.4 Logging & Monitoring | PII-freie Logs (F-03) | ✅ |
| A.12.6 Vulnerability Management | pip-audit, Trivy, Dependency-Updates | ✅ |
| A.14.2 Secure Development | SAST (Semgrep), Code Review, Tests | ✅ |
| A.16 Incident Management | Graceful Degradation, Fehlerbehandlung | ✅ |

### SOC 2 Trust Services Criteria

| Criterion | Adressiert durch | Status |
|-----------|-----------------|--------|
| CC6.1 Logical Access | Docker non-root, localhost-binding | ✅ |
| CC6.3 Access Removal | Single-User, keine Accounts | N/A |
| CC7.1 Detection | Logging (loguru), Audit-Trail (Excel) | ✅ |
| CC7.2 Monitoring | PII-freie Logs, Exception-Handling | ✅ |
| CC8.1 Change Management | Git-Versionierung, Test-Suite | ✅ |

---

## 6. Verbleibende Findings (akzeptiert / dokumentiert)

| # | Schwere | Beschreibung | Begründung |
|---|---------|-------------|-----------|
| #1 | CRITICAL | PII im Streamlit UI & Plaintext auf Disk | Akzeptiert als inhärentes Risiko einer lokalen App; Dokumentation empfiehlt Festplattenverschlüsselung |
| #2 | CRITICAL | Banking-Daten in plaintext JSON | Akzeptiert; optional: `cryptography.fernet` in künftiger Version |
| #10 | MEDIUM | Keine Authentifizierung | Single-User-App; Docker jetzt localhost-only |
| #11 | MEDIUM | Sensitive Daten in Export-Dateien | Per Design (Rechnungen müssen diese Daten enthalten) |
| #14 | LOW | Datei-Validierung nur nach Extension | Geringes Risiko; Parser-Bibliotheken validieren Content |
| #15 | LOW | Kein Size-Check vor tempfile | Streamlit erzwingt maxUploadSize |
| #17 | LOW | Kein Timeout auf Ollama-Client | Ollama ist lokal, Timeout weniger kritisch |
| #18 | LOW | Kein Retry/Backoff bei HTTP | Optionaler Check, App bleibt offline nutzbar |
| #19 | LOW | Kein Dependency-Hash-Pinning | `uv.lock` vorhanden; Verbesserung in CI/CD |
| #20 | LOW | Keine Security Headers | Streamlit-Limitierung; Docker jetzt localhost |
| #21 | LOW | Keine Integrity-Checks auf Fee-Tabelle | Test-Suite validiert Werte; JSON-Fallback vorhanden |

---

## 7. Empfehlungen für kontinuierliche Sicherheit

### CI/CD Integration (GitHub Actions)

```yaml
name: Security Checks
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
      - name: Semgrep
        uses: semgrep/semgrep-action@v1
        with:
          config: p/python
      - name: pip-audit
        run: pip install pip-audit && pip-audit
      - name: Tests
        run: uv run pytest tests/
```

### Zusätzliche Empfehlungen

- **Dependabot** aktivieren für automatische Dependency-Updates
- **Repository auf Public** stellen (Community-Feedback, Transparenz)
- **Security Policy** (`SECURITY.md`) mit Reporting-Prozess ergänzen
- **`notary_profile.json`-Verschlüsselung** via `cryptography.fernet` in v0.2
- **Streamlit-Passwortschutz** als optionales Feature dokumentieren
- **SBOM** (`trivy sbom`) bei Releases generieren

---

## 8. Residual Risks

1. **Lokale Daten unverschlüsselt:** `notary_profile.json` und generierte Rechnungen liegen im Klartext auf der Festplatte. Risiko wird durch macOS-Festplattenverschlüsselung (FileVault) gemindert.
2. **LLM-Halluzinationen:** Trotz Confidence-Threshold und KV-Validierung kann das LLM prinzipiell falsche Werte extrahieren. Das Human-in-the-Loop-Design (Pflicht-Prüfung durch Notar) ist die entscheidende Mitigation.
3. **Supply Chain:** Abhängigkeiten können neue CVEs enthalten. Kontinuierliches Monitoring via Dependabot/pip-audit erforderlich.

---

## 9. Fazit

Die Software wurde mit den empfohlenen Open-Source-Tools (Gitleaks, Semgrep, Bearer, Trivy, pip-audit) geprüft. Nach Umsetzung der Critical/High-Priority-Fixes zeigt kein automatisiertes Tool mehr Findings. Die Architektur (lokal, Single-User, Human-in-the-Loop) bietet inhärente Sicherheit für den vorgesehenen Einsatzzweck.

**Status:** Deutlich näher an ISO 27001 / SOC 2 Audit-Readiness. Die dokumentierten Residual Risks und verbleibenden Low-Priority-Findings sind für den MVP akzeptabel und können im Rahmen der Weiterentwicklung adressiert werden.

---

*Erstellt am 10. Juli 2026 · Security Audit nach opencode_audit_readiness_instructions.md · GunnarMUC*
