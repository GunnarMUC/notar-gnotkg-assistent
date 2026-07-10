# Deployment & Installation – Notar GNotKG Assistent

## Voraussetzungen

### Hardware (empfohlen)
- Apple Silicon Mac (M1/M2/M3/M4) mit **≥ 16 GB RAM**
- ≥ 24 GB RAM für 14B-Modelle in hoher Quantisierung (z. B. Qwen2.5-14B Q6)
- ≥ 15 GB freier Festplattenspeicher (Ollama + Modelle + App + Daten)

### macOS
- macOS 14 (Sonoma) oder neuer
- Optional: Xcode Command Line Tools (`xcode-select --install`) für `uv`/`pip`

### Alternative Plattformen
- **Linux** (Ubuntu 22.04+, Debian 12+): Voll unterstützt (AMD64 oder ARM64)
- **Windows**: Mit WSL2 (Ubuntu) – Ollama und App laufen im WSL2, Browser auf Windows

---

## 1. Ollama installieren

### macOS
```bash
# Nativer macOS-Installer (empfohlen)
# https://ollama.com → Download → Installieren
# ODER via Homebrew:
brew install ollama
```

Nach der Installation Ollama starten:
```bash
# Entweder die Ollama.app öffnen, oder:
ollama serve
# Läuft auf http://localhost:11434
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

---

## 2. LLM-Modell herunterladen

**Empfohlen**: Qwen2.5-14B (beste Qualität für deutsche Rechtstexte)

```bash
# Empfohlen: Qwen2.5-14B mit Q5_K_M Quantisierung (~10 GB)
ollama pull qwen2.5:14b-instruct-q5_K_M

# Alternative: Kleinere Modelle (weniger RAM, geringere Genauigkeit)
ollama pull qwen2.5:7b              # ~4.7 GB
ollama pull mistral-nemo:latest     # ~7.1 GB

# Für Embeddings / RAG-Erweiterungen
ollama pull nomic-embed-text:latest # ~274 MB
```

Verfügbare Modelle prüfen:
```bash
ollama list
```

> **Hinweis**: Der User kann später im UI frei zwischen installierten Modellen wechseln. Siehe auch `verfuegbare_LLMs.txt` für eine Liste getesteter Modelle.

---

## 3. System-Abhängigkeiten (macOS)

```bash
# Tesseract OCR + deutsches Sprachpaket
brew install tesseract tesseract-lang-deu

# Optional: Pandoc für RTF-Konvertierung
brew install pandoc
```

**Linux** (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu pandoc
```

---

## 4. Python-Umgebung einrichten

### Mit uv (empfohlen, schnell & reproduzierbar)
```bash
# Projektverzeichnis
cd notar-gnotkg-app

# uv installieren (falls nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Virtuelle Umgebung erstellen + Abhängigkeiten installieren
uv sync
```

### Mit venv + pip (klassisch)
```bash
cd notar-gnotkg-app
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows (WSL2)

pip install -r requirements.txt
```

---

## 5. Notar-Profil einrichten

Beim ersten Start der App wirst du durch ein Formular geführt:

- Name, Kanzlei, Adresse
- Telefon, E-Mail
- Bankverbindung (IBAN, BIC) für Rechnungen
- Steuernummer / USt-ID (optional)

Das Profil wird lokal in `data/notary_profile.json` gespeichert. Eine spätere Änderung ist jederzeit in der Sidebar möglich.

---

## 6. App starten

```bash
cd notar-gnotkg-app

# Mit uv:
uv run streamlit run app.py

# Mit venv:
source .venv/bin/activate
streamlit run app.py
```

Die App öffnet sich unter **http://localhost:8501** im Browser.

---

## 7. Docker (optional)

Die App kann auch im Docker-Container betrieben werden. **Wichtig**: Ollama bleibt auf dem Host-System (nativ, wegen Metal-Beschleunigung auf Apple Silicon).

```bash
# Image bauen
docker build -t notar-gnotkg-app -f docker/Dockerfile .

# Container starten (mit Zugriff auf Host-Ollama)
docker run -d \
  --name notar-app \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/history:/app/history \
  --add-host host.docker.internal:host-gateway \
  notar-gnotkg-app

# Oder via docker-compose:
docker compose -f docker/docker-compose.yml up -d
```

**Apple Silicon**: Docker Desktop hat keine vollständige GPU-Unterstützung für Ollama im Container. Deshalb die klare Trennung: App im Container, Ollama nativ auf dem Mac. Verbinde den Container via `host.docker.internal:11434` zum Host-Ollama.

---

## 8. Verzeichnisstruktur nach Installation

```
notar-gnotkg-app/
├── data/
│   ├── notary_profile.json          # Notar-Stammdaten
│   ├── notar_app.db                 # SQLite (History, Audit)
│   ├── fee_tables/
│   │   └── v2026_01.json            # Aktuelle Gebührentabelle
│   └── generated_invoices/          # Erstellte Rechnungen (nach Erstellung)
├── history/
│   └── audit_full.jsonl             # Append-Only Audit-Log
└── prompts/
    └── extraction_v1.txt            # Aktueller Extraktions-Prompt
```

---

## 9. Erster Durchlauf – Kurzanleitung

1. **App starten** (siehe Schritt 6)
2. **Notar-Profil ausfüllen** (automatisch beim ersten Start)
3. **LLM-Modell auswählen** (Sidebar, Dropdown aus `ollama list`)
4. **Beispielurkunde hochladen** (aus `Beispielurkunden/txt/` oder eigene Urkunde)
5. **„Dokument analysieren“** klicken
6. **Extraktion prüfen** – Positionen bearbeiten/korrigieren
7. **„Finale Positionen bestätigen“** → Rechnung generieren
8. **Rechnung + Excel-Log herunterladen**

---

## 10. Updates

### App-Update
```bash
git pull
uv sync                        # Neue Abhängigkeiten installieren
```

### Fee-Engine-Update
Neue JSON-Tabelle in `data/fee_tables/` ablegen. Die App erkennt neue Versionen und warnt bei veralteten Tabellen. Details siehe `FEE_CALCULATION_LOGIC.md`.

### GNotKG-Aktualitätsprüfung
Die App prüft beim Start automatisch auf `gesetze-im-internet.de`, ob die lokale GNotKG-Version noch aktuell ist. Bei Abweichung erscheint eine Warnung im UI.

---

## 11. Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| **Ollama nicht erreichbar** | `ollama serve` ausführen oder Ollama.app öffnen |
| **Modell nicht gefunden** | `ollama pull qwen2.5:14b-instruct-q5_K_M` |
| **OCR funktioniert nicht** | `tesseract --list-langs` – muss `deu` enthalten; `brew install tesseract-lang-deu` |
| **Nicht genug RAM** | Kleineres Modell verwenden (z. B. `qwen2.5:7b`) |
| **Streamlit-Port belegt** | `streamlit run app.py --server.port 8502` |
| **GNotKG-Check schlägt fehl** | Kein Internet oder Firewall; App bleibt offline nutzbar |

---

## 12. Sicherheitshinweise

- Die App ist für den **lokalen Einzelplatz-Betrieb** ausgelegt
- Streamlit läuft standardmäßig nur auf `localhost` (nicht aus dem Netzwerk erreichbar)
- Keine Daten verlassen das Gerät (außer optionaler GNotKG-Check)
- Notar-Profil und IBAN liegen unverschlüsselt im lokalen Dateisystem → Zugriff nur durch macOS-Benutzerkonten geschützt
- Optionaler Passwort-Schutz kann via Streamlit Secrets oder `.streamlit/secrets.toml` eingerichtet werden

---

**Bei Problemen oder Fragen**: Siehe `README.md`, `ARCHITECTURE.md` oder die weiteren Briefing-Dateien.
