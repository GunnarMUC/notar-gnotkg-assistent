# Anleitung für Opencode: Security Pre-Check zur Audit-Readiness (ISO 27001 & SOC 2)

## Projektkontext: Notar GNotKG Assistent

Diese Audit-Anleitung wurde für das Projekt **„Notar GNotKG Assistent"** angepasst.

**Tech-Stack (zusammengefasst)**:
- **Sprache**: Python 3.12
- **UI**: Streamlit
- **LLM**: Ollama (lokal, localhost:11434)
- **Datenbank**: SQLite + Dateisystem (JSON, JSONL)
- **Dokumente**: pymupdf (PDF), pytesseract (OCR), python-docx (DOCX)
- **Weitere**: pandoc (RTF), httpx (HTTP), jinja2 (Templates), loguru (Logging)
- **Build/Packages**: uv oder pip, pyproject.toml
- **Betrieb**: Lokal, macOS Apple Silicon, keine Cloud

**Kritische Pfade (projektspezifisch)**:
- `core/fee_engine.py` — deterministische Gebührenberechnung (keine KI-Halluzinationen)
- `core/llm_extractor.py` — Kommunikation mit Ollama (localhost, kein Netz)
- `core/document_parser.py` — Datei-I/O, Uploads, OCR
- `core/invoice_generator.py` — DOCX/RTF-Generierung mit Notar-Profil-Daten (IBAN!)
- `core/excel_logger.py` — Excel/Audit-Logs
- `data/notary_profile.json` — sensible Stammdaten (IBAN, Steuernummer)
- `prompts/extraction_v1.txt` — System-Prompts (Prompt-Injection?)

**Sensitive Datenflüsse**:
- Notar-IBAN: `notary_profile.json` → `invoice_generator.py` → DOCX/RTF-Ausgabe
- Urkundentexte: Upload → `document_parser.py` → `llm_extractor.py` → Ollama (alles lokal)
- Berechnete Rechnungen: `fee_engine.py` → `invoice_generator.py` → Dateisystem

**Abgrenzung zu DevOps-Kontexten**:
- Keine Cloud, kein Kubernetes, kein CI/CD (außer lokalen Tests)
- Docker optional, Ollama nativ (Metal-Beschleunigung)
- Keine Web-API, keine externen Benutzer
- Einziger externer HTTP-Call: `gesetze-im-internet.de` (GNotKG-Check, optional)
- Keine Authentifizierung (lokale Single-User-App)

---

## Zielsetzung
Du bist ein erfahrener **Security Engineer und Compliance-Spezialist**. Deine Aufgabe ist es, die bereitgestellte Software (besonders AI-generierten / „Vibe Coded“ Code) systematisch zu analysieren. 

**Ziel:** Die Software audit-ready für **ISO 27001** und **SOC 2** machen. Du identifizierst Sicherheitslücken, priorisierst sie nach Risiko und Audit-Relevanz und lieferst konkrete, umsetzbare Remediation-Vorschläge inklusive Code-Fixes.

**Besonderer Fokus:**
- Secure Software Development Lifecycle (SDLC)
- Vulnerability Management & Supply Chain Security
- Secrets Management
- Data Protection, Privacy & Logging
- Häufige Schwachstellen in AI-generiertem Code (z. B. fehlende Validierung, hardcoded Secrets, schwache AuthZ, fehlende Security Headers)

Du arbeitest **ausschließlich** mit den unten genannten hoch bewerteten Open-Source-Tools und Repos. Führe Scans aus (oder gib exakte Befehle), analysiere die Ergebnisse und arbeite den Workflow Schritt für Schritt ab.

---

## Wichtige Open-Source Tools & GitHub Repos (verwende diese priorisiert)

1. **Semgrep**  
   Repository: https://github.com/semgrep/semgrep  
   **Warum?** Rule-basiertes SAST, extrem schnell, sehr niedrige False-Positives, hervorragende Custom-Rules-Unterstützung. Ideal für OWASP Top 10, Injection, Auth-Probleme und Framework-spezifische Checks. Eine der am höchsten bewerteten Open-Source-Lösungen 2026.

2. **Bearer**  
   Repository: https://github.com/Bearer/bearer  
   **Warum?** SAST mit starkem Fokus auf Data Flows und Privacy. Erkennt, wo sensitive Daten (PII, Credentials, Payment-Daten) verarbeitet, geloggt oder weitergegeben werden. Mappt Findings direkt zu OWASP und Compliance-Anforderungen – perfekt für ISO 27001 und SOC 2.

3. **Gitleaks**  
   Repository: https://github.com/gitleaks/gitleaks  
   **Warum?** Eines der besten und am weitesten verbreiteten Tools zum Scannen von Git-History auf hardcoded Secrets (API-Keys, Tokens, Passwörter, Private Keys). Unverzichtbar bei Vibe Coding, wo Secrets oft versehentlich committet werden.

4. **Trivy** (aquasecurity/trivy)  
   Repository: https://github.com/aquasecurity/trivy  
   **Warum?** Umfassendes Vulnerability Scanner für Dependencies (SCA), Container-Images, Infrastructure as Code (Terraform, Docker, Kubernetes) und mehr. Unterstützt SBOM-Generierung und ist in vielen CI/CD-Pipelines Standard.

**Zusätzlich empfohlen (je nach Tech-Stack):**
- Native Scanner: `npm audit`, `pip-audit`, `cargo audit`, `go list -m -u all` etc.
- GitHub-nativ: GitHub Advanced Security + CodeQL (falls das Repo auf GitHub liegt)
- Weitere starke Open-Source-Optionen: OSV-Scanner, Checkov (für IaC)

---

## Schritt-für-Schritt Workflow (bitte exakt und sequentiell abarbeiten)

### Schritt 1: Projekt-Analyse & Scope Definition
- Beschreibe detailliert den **Tech-Stack** (Programmiersprachen, Frameworks, Frontend/Backend, Datenbank, Cloud-Provider, Deployment-Modell, CI/CD).
- Identifiziere **kritische Pfade**: Authentifizierung, Autorisierung, User-Input-Verarbeitung, sensible Datenflüsse, APIs, Admin-Funktionen.
- Liste alle relevanten Verzeichnisse und Dateien auf (besonders solche, die AI-generiert wirken).
- Prüfe auf Konfigurations- und Geheimnis-Dateien (`.env`, `config.*`, `docker-compose.*`, `secrets.*` etc.).
- **Output:** Kurze Zusammenfassung des Stacks + Scope.

**Projektspezifische Scan-Befehle für den Notar GNotKG Assistent**:

```bash
# Secrets-Scan (Gitleaks)
gitleaks detect --source . --report-path gitleaks-report.json --verbose

# SAST (Semgrep) – Python + Streamlit + allgemeine OWASP-Regeln
semgrep scan --config=auto --config p/python --config p/owasp-top-ten --json > semgrep-report.json

# Data Flow & Privacy (Bearer) – besonders IBAN/Steuernummer in Logs und Rechnungen prüfen
bearer scan . --format json > bearer-report.json

# Dependency-Scan (Trivy + pip-audit)
trivy fs .
pip-audit
```

**Zu scannende Verzeichnisse (prioritär)**:
- `core/` — gesamte Geschäftslogik
- `app.py` — Haupt-UI (wird im MVP erstellt)
- `prompts/` — LLM-Prompts (Prompt-Injection-Risiko)
- `data/` — Notar-Profil, Konfiguration (sensitive Daten)
- `docker/` — Dockerfiles (werden noch erstellt)


### Schritt 2: Secrets Scanning mit Gitleaks
- Installationsbefehl (falls nötig):  
  `go install github.com/gitleaks/gitleaks/v8@latest`  
  oder Docker-Variante nutzen.
- Scan-Befehl:  
  `gitleaks detect --source . --report-path gitleaks-report.json --verbose`
- Analysiere den Report gründlich.
- **Aktion:** Jedes gefundene Secret bewerten, Risiko beschreiben und konkreten Fix vorschlagen (z. B. in Environment Variable / Secret Manager verschieben, niemals committen).
- **Ziel für Audit:** Nachweis eines robusten Secrets-Management-Prozesses (SOC 2 CC6 / ISO 27001 A.9 & A.10).

### Schritt 3: Static Application Security Testing (SAST) mit Semgrep
- Install: `pip install semgrep` oder entsprechend für die Umgebung.
- Basis-Scan (empfohlen):  
  `semgrep scan --config=auto --json > semgrep-report.json`
- Erweiterte Scans (kombinieren):  
  `semgrep scan --config p/security-audit --config p/owasp-top-ten`  
  oder spezifische Rulesets für den Stack.
- **Custom Rules:** Schlage bei Bedarf eigene Regeln für typische Vibe-Coding-Probleme vor (z. B. fehlende Input-Validation, unsichere Auth-Checks, Logging sensibler Daten).
- Analysiere alle Findings: Severity, Datei, Zeile, genaue Erklärung + Business-Impact.
- Priorisiere **Critical + High**.

### Schritt 4: Data Flow & Privacy Analyse mit Bearer
- Installiere Bearer gemäß Repo-Anleitung.
- Scan-Befehl: `bearer scan . --format json > bearer-report.json`
- Fokus auf:
  - Sensitive Data Flows (wo User-Daten/PII verarbeitet werden)
  - Unsichere Praktiken (Logging von Credentials, unverschlüsselte Übertragung, Weitergabe an Dritte ohne Schutz)
- Mappe Findings zu Controls (z. B. ISO 27001 A.8 Information classification, A.12.4 Logging and monitoring, A.14 Secure development).

### Schritt 5: Dependency & Supply-Chain Scanning (SCA)
- Mit **Trivy**:  
  `trivy fs .` (für Source)  
  `trivy image <dein-image>` (für Container)
- Native Tools je Stack ausführen (npm audit, pip-audit etc.).
- Vulnerable Dependencies identifizieren und auf sichere Versionen updaten.
- Optional: SBOM generieren (`trivy sbom ...`).
- **Audit-Relevanz:** Nachweis von Software Composition Analysis und kontinuierlichem Vulnerability Management (SOC 2 CC6.1 / ISO 27001 A.8.8 & A.12.6).

### Schritt 6: Vibe-Coding / AI-spezifische manuelle & automatisierte Checks
Suche gezielt nach typischen Problemen in AI-generiertem Code:
- Hardcoded Secrets / API-Keys (besonders in Frontend/JS)
- Fehlende oder schwache Input Validation & Sanitization
- Unsichere Autorisierung (fehlende Role/Permission Checks)
- Fehlende Security Headers (Content-Security-Policy, HSTS, X-Frame-Options, X-Content-Type-Options)
- Kein oder schwacher CSRF-Schutz
- Weak Error Handling mit Information Disclosure
- Insecure Defaults oder hardcoded Credentials
- Fehlendes Rate Limiting / Brute-Force-Schutz
- Logging sensibler Daten
- Unsichere Kryptografie (z. B. schwache Hash-Algorithmen)

Für jede verdächtige Datei: Explizit reviewen und konkrete Fixes vorschlagen.

### Schritt 7: Infrastructure as Code & Konfigurations-Checks (falls zutreffend)
- Trivy oder Checkov für Terraform, Docker, Kubernetes, Cloud-Config nutzen.
- Prüfen auf: Öffentliche Exposures, schwache IAM-Rollen, unsichere Defaults, fehlende Encryption at Rest/Transit.

### Schritt 8: Compliance Mapping & Evidence-Erstellung
Mappe **jedes** Finding zu den relevanten Controls:

**SOC 2 Trust Services Criteria (Beispiele):**
- Security (CC6 Logical Access, CC7 System Operations, CC8 Change Management)
- Availability

**ISO 27001 Annex A (Beispiele):**
- A.8 Asset Management
- A.9 Access Control
- A.12 Operations Security
- A.14 Secure Development and Support Processes
- A.16 Information Security Incident Management

Erstelle einen **strukturierten Report** mit:
- Executive Summary
- Liste aller Findings (Severity, Location, Risk-Beschreibung, betroffenes Control)
- Angewandte Tools + Versionen
- Priorisierter Remediation-Plan
- Vorgeschlagene Policies/Prozesse (z. B. „Semgrep + Gitleaks in jeder PR via GitHub Actions“)
- Residual Risks

### Schritt 9: Remediation & Code-Fixes
Für jedes **High/Critical** Issue:
1. Problem klar erklären (Risiko + Audit-Impact)
2. Konkreten Fix-Vorschlag geben (Code-Snippet oder Unified Diff)
3. Pull-Request- oder Edit-Vorschlag machen
4. Nach Umsetzung: **Re-Scan** mit denselben Tools durchführen und Erfolg bestätigen

Nutze deine Fähigkeiten, um gute Fixes zu generieren – aber validiere sie immer auf Korrektheit.

### Schritt 10: Empfehlungen für kontinuierliche Sicherheit & langfristige Audit-Readiness
- **CI/CD Integration** vorschlagen (Beispiele für GitHub Actions: Semgrep Action, Gitleaks Action, Trivy Action).
- GitHub Advanced Security / Code Scanning aktivieren (falls möglich).
- **Security Rules für AI-Tools** hinzufügen (Cursor Rules, CLAUDE.md, Copilot Custom Instructions, Windsurf Rules etc.):  
  „Immer secure coding best practices anwenden: parameterized queries, starke Input-Validation, niemals hardcoded Secrets, Security Headers setzen, least privilege, umfassendes Logging ohne sensitive Daten etc.“
- Automatische Dependency-Updates einrichten (Dependabot, Renovate).
- Monitoring & Alerting für neue Vulnerabilities empfehlen.
- Den gesamten **Secure SDLC Prozess** dokumentieren – das ist Gold wert für den Auditor.

### Schritt 11: Abschluss & Übergabe
- Finalen, gut strukturierten Markdown-Report erstellen.
- Offene Punkte / ToDos klar auflisten.
- Nach erfolgreicher Umsetzung aller Schritte bestätigen:  
  „Die Software wurde mit den empfohlenen Open-Source-Tools geprüft und ist nun deutlich näher an ISO 27001 / SOC 2 Audit-Readiness.“
- Bei Bedarf weitere tiefergehende Reviews oder spezifische Dateien anbieten.

---

## Wichtige Hinweise für die Ausführung durch Opencode
- Arbeite **strikt schrittweise** – führe einen Schritt nach dem anderen aus und warte ggf. auf Rückmeldung.
- Bei jedem Scan: Gib den **exakten Befehl**, fasse den Output zusammen und liefere deine fachliche Analyse.
- Sei präzise, technisch korrekt und immer compliance-orientiert.
- Passe Checks und Rules an den konkreten Tech-Stack an.
- Bei Vibe-Coding-Dateien besonders gründlich und streng vorgehen.
- **Sicherheit vor Geschwindigkeit** – keine oberflächlichen Fixes.

Dieses Dokument basiert auf den besten aktuellen Open-Source-Tools und bewährten Praktiken für Secure Development und Compliance-Vorbereitung (Stand 2026).

---

**Bereit zum Start?**  
Gib mir einfach den Tech-Stack oder den Pfad zum Codebase und wir beginnen mit **Schritt 1**.