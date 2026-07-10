# Fee Calculation Logic – Deterministische GNotKG-Berechnung

## Grundprinzipien

Die Fee Engine ist das **rechtlich kritischste Modul**. Sie darf **unter keinen Umständen** von einem LLM beeinflusst oder aufgerufen werden. Alle Beträge müssen exakt der aktuellen Fassung des Gerichts- und Notarkostengesetzes (GNotKG) entsprechen.

**Zentrale Regel**:
> Der Notar darf nur die gesetzlich vorgeschriebenen Gebühren erheben – nicht mehr und nicht weniger (§ 17 BNotO i. V. m. GNotKG).

## Wichtige Bestandteile der GNotKG (Stand 2026)

- **Anlage 1** (zu § 3 Abs. 2): Kostenverzeichnis – enthält alle Gebührentatbestände mit KV-Nummern (z. B. 21200 Beurkundungsverfahren, 24102 etc.)
- **Anlage 2** (zu § 34 Abs. 3): Gebührentabellen
  - Tabelle A (Gerichte)
  - **Tabelle B (Notare)** – relevant für diese App
- Wertvorschriften §§ 95–113 GNotKG (wie wird der Geschäftswert ermittelt?)
- Weitere Vorschriften zu Auslagen, Pauschalen, USt etc.

## Empfohlene Implementierungsstrategie für die Fee Engine

### 1. Versionierte Tabellen (empfohlen)

Lege die aktuellen Tabellenwerte in einer JSON-Datei ab:

`data/fee_tables/v2026_01.json`

Beispiel-Struktur (stark vereinfacht):

```json
{
  "version": "GNotKG_Stand_2026-01-01_v1",
  "table_b": {
    "description": "Gebührentabelle B für Notare",
    "brackets": [
      {"up_to": 1500, "fee": 23},
      {"up_to": 13000, "fee": 83},
      {"up_to": 125000, "fee": 300},
      {"up_to": 550000, "fee": 1015},
      // ... weitere Staffeln exakt aus Anlage 2
    ]
  },
  "kv_definitions": {
    "21200": {
      "description": "Beurkundungsverfahren",
      "fee_type": "value_based",
      "rate": 1.0,
      "table": "B"
    },
    "22114": {
      "description": "Elektronischer Vollzug und XML-Strukturdaten",
      "fee_type": "flat_or_value",
      "flat_fee": 15
    }
    // weitere häufige KV-Nummern
  }
}
```

### 2. Python-Implementierung (`core/fee_engine.py`)

```python
from pydantic import BaseModel
from typing import Literal
import json

class FeeCalculation(BaseModel):
    kv_number: str
    description: str
    business_value: float | None
    fee_amount: float
    calculation_basis: str          # z.B. "Tabelle B, 1,0-fach, Wert 385000 €"
    notes: str | None = None

class FeeEngine:
    def __init__(self, table_version: str = "v2026_01"):
        self.version = f"GNotKG_Stand_2026-01-01_{table_version}"
        self.tables = self._load_tables(table_version)

    def calculate_position(
        self,
        kv_number: str,
        business_value: float | None = None,
        multiplier: float = 1.0
    ) -> FeeCalculation:
        # Hier die exakte Logik implementieren:
        # - Werttabellen-Lookup
        # - Multiplikatoren (z. B. 2,0 für Beurkundung + Vollzug)
        # - Flat Fees
        # - Kombinationsregeln
        pass

    def calculate_invoice_total(self, positions: list[FeeCalculation]) -> dict:
        # Summenbildung + USt 19%
        pass
```

### 3. Für den MVP: Fokus auf häufige Tatbestände

Implementiere zuerst exakt:

1. Beurkundung Immobilienkaufvertrag (KV 21200 + ggf. weitere)
2. Vollzug (elektronisch)
3. Betreuung
4. Grundschuldbestellung
5. GmbH-Gründung (Musterprotokoll / individuell)
6. Testament / Erbvertrag
7. Vorsorgevollmacht / Patientenverfügung

Für jeden dieser Fälle die korrekten KV-Nummern, Wertregeln und Tabellenwerte hinterlegen.

### 4. Umgang mit Gesetzesänderungen

- Jede neue GNotKG-Fassung → neue Version der `fee_tables/` + neue Klasse oder Parameter in `FeeEngine`.
- Die App zeigt in jeder Rechnung die verwendete Version an.
- Bei Start wird nur geprüft, ob die lokale Version noch aktuell ist (Warnung bei Abweichung). Die eigentliche Aktualisierung erfolgt manuell durch den Entwickler.

### 5. Plausibilitäts-Checks & Warnungen

Die Fee Engine sollte bei ungewöhnlichen Kombinationen oder extremen Werten Warnungen ausgeben (z. B. „Sehr hoher Wert – bitte manuell prüfen“), aber niemals die Berechnung verweigern.

---

## Quellen für korrekte Tabellenwerte

### GNotKG XML-Datei (im Projekt enthalten)

Die Datei `Gesetze/BJNR258610013 3.xml` enthält den vollständigen GNotKG-Text im XML-Format von `gesetze-im-internet.de` (Stand: zuletzt geändert durch Art. 6 G v. 10.12.2025).

**Vorteile für die Implementierung**:
- **Anlage 1 (Kostenverzeichnis)**: Enthält alle KV-Nummern mit Beschreibung und Gebührensatz — kann automatisch geparst und als Nachschlagewerk in der App verwendet werden
- **Anlage 2 (Gebührentabelle B)**: Staffelwerte für Notargebühren — Grundlage für die Fee-Engine
- **Wertvorschriften (§§ 95–113)**: Regeln zur Geschäftswertermittlung — für Plausibilitäts-Checks und RAG

**Empfohlene Strategie**:

1. **Einmaliges Parsen** (Build-Schritt, nicht zur Laufzeit): Schreibe ein Skript `scripts/parse_gnotkg_xml.py`, das das XML parst und folgende strukturierte JSON/CSV-Dateien generiert:
   - `data/fee_tables/kv_definitions.json` — alle KV-Nummern aus Anlage 1
   - `data/fee_tables/table_b.json` — die vollständige Staffeltabelle aus Anlage 2
   - `data/fee_tables/value_rules.json` — Extrakt der Wertvorschriften

2. **Zur Laufzeit**: Die Fee-Engine nutzt die generierten JSON-Dateien (schneller, kein XML-Parsing pro Start).

3. **RAG-Erweiterung** (optional): Embeddings der einzelnen KV-Nummern und Wertvorschriften für das LLM (bessere KV-Vorschläge).

**XML-Struktur-Hinweise**:
- Jeder Paragraph ist ein `<norm>`-Element mit `<enbez>` (z. B. `§ 34`) und `<text>` (Inhalt)
- Anlage 1 enthält eine Tabelle mit `<row>`-Elementen (KV-Nr, Gebührentatbestand, Gebühr)
- Anlage 2 enthält die Staffelwerte in `<row>`-Elementen (bis-Wert, Gebühr)
- Das `<fussnoten>`-Element enthält wichtige Hinweise (Gesetzesänderungen, Übergangsregeln)

```python
# Minimalbeispiel: Paragraphen aus dem XML parsen
import xml.etree.ElementTree as ET

tree = ET.parse("Gesetze/BJNR258610013 3.xml")
root = tree.getroot()
ns = {"ns": "http://www.gesetze-im-internet.de/dtd/1.01/gii-norm.dtd"}

for norm in root.findall(".//ns:norm", ns):
    enbez = norm.find(".//ns:enbez", ns)
    text = norm.find(".//ns:text", ns)
    if enbez is not None and text is not None:
        print(f"{enbez.text}: {text.text[:100]}...")
```

### Online-Quellen

- Offizielle Seite: https://www.gesetze-im-internet.de/gnotkg/anlage_2.html
- Praktische Beispiele und Rechner: notar.de, gnotkg.de, diverse Notar-Kanzleien
- Aktuelle Kommentare zum GNotKG (z. B. von Diehn oder anderen Fachautoren)

**Empfehlung**: Für die ersten Versionen 3–5 reale Beispiele aus der Praxis nachrechnen und als Unit-Tests abspeichern. Nutze die XML-Datei in `Gesetze/` als primäre Datenquelle für die Fee-Tabellen und das Kostenverzeichnis (siehe Abschnitt „Quellen für korrekte Tabellenwerte“).

---

**Für den Coding-Agent**:  
Die Qualität der Fee Engine entscheidet über die rechtliche Zulässigkeit der App. Nimm dir hier besonders viel Zeit für Korrektheit und Tests. Besser 6 exakt implementierte Tatbestände als 30 halbkorrekte.