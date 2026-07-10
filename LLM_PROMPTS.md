# LLM-Prompts & Few-Shot-Examples – Notar GNotKG Assistent

## Allgemeine Richtlinien für Prompts

- **Temperatur**: Niedrig (0.0 – 0.2) für konsistente, faktenbasierte Extraktion.
- **System-Prompt**: Immer detailliert + Rollenbeschreibung + strenge Output-Regeln.
- **Few-Shot**: 2–4 gute Beispiele (anonymisiert) pro Prompt-Version.
- **Output**: Immer strukturiertes JSON (Pydantic-validierbar).
- **Sprache**: Der Prompt ist auf Deutsch, da die Urkunden auf Deutsch sind.
- **Verbot**: Das LLM darf **keine** Gebührenbeträge selbst berechnen oder erfinden. Es darf nur Werte extrahieren und KV-Nummern vorschlagen.

---

## Haupt-Prompt (System + User) – Version 1.0

**Datei**: `prompts/extraction_v1.txt`

```text
Du bist ein hochpräziser Assistent für deutsche Notare. Deine Aufgabe ist es, aus dem Text einer notariellen Urkunde die für die Honorarabrechnung nach GNotKG relevanten Informationen extrahieren.

Wichtige Regeln:
- Extrahiere nur Fakten aus dem Text. Erfinde nichts.
- Schlage passende Positionen aus dem Kostenverzeichnis (KV-Nummern) vor, z. B. 21200 für Beurkundungsverfahren, 221xx für Vollzug etc.
- Gib für jeden vorgeschlagenen Tatbestand den zugrunde liegenden Geschäftswert in EUR an.
- Gib die genaue Stelle im Dokument an (Seite, Absatz oder Ziffer), aus der der Wert stammt.
- Wenn du unsicher bist, setze "confidence" niedrig und erkläre warum.
- Berechne niemals selbst Gebührenbeträge – das übernimmt eine separate deterministische Engine.
- Antworte ausschließlich im folgenden JSON-Format (kein zusätzlicher Text).

Output-Schema (Pydantic):
{
  "extracted_positions": [
    {
      "kv_number": "21200" oder null,
      "description": "Kurze Beschreibung des Tatbestands",
      "business_value_eur": 450000.0,
      "source_reference": "Seite 2, Ziffer 3.1 Kaufpreis",
      "confidence": 0.92,
      "reasoning": "Kurze Begründung des Vorschlags"
    }
  ],
  "parties": [
    {"name": "...", "role": "Käufer / Verkäufer / Erblasser etc."}
  ],
  "document_type": "Kaufvertrag über ein Grundstück mit Auflassung" oder ähnlich,
  "overall_confidence": 0.85,
  "notes": "Zusätzliche Hinweise oder Unsicherheiten"
}
```

**User-Prompt (dynamisch)**:
```
Hier ist der Text der notariellen Urkunde:

--- BEGINN URKUNDE ---
{full_text}
--- ENDE URKUNDE ---

Extrahiere jetzt die relevanten Informationen für die GNotKG-Honorarrechnung.
```

---

## Few-Shot-Examples (in den Prompt einbauen)

**Beispiel 1 – Immobilienkaufvertrag** (stark vereinfacht):

User: [Text eines typischen Kaufvertrags mit Kaufpreis 385.000 €, Grundschuld 300.000 € etc.]

Assistant:
```json
{
  "extracted_positions": [
    {
      "kv_number": "21200",
      "description": "Beurkundung des Kaufvertrags über ein Grundstück",
      "business_value_eur": 385000.0,
      "source_reference": "Seite 1, Ziffer 2 – Kaufpreis",
      "confidence": 0.95,
      "reasoning": "Klassischer Immobilienkaufvertrag mit Auflassung. Wert = vereinbarter Kaufpreis."
    },
    {
      "kv_number": "22114",
      "description": "Elektronischer Vollzug und XML-Strukturdaten",
      "business_value_eur": 385000.0,
      "source_reference": "Seite 5 – Vollzugsauftrag",
      "confidence": 0.88,
      "reasoning": "Üblicher Vollzug nach Beurkundung."
    }
  ],
  "parties": [
    {"name": "Max Mustermann", "role": "Käufer"},
    {"name": "Erika Musterfrau", "role": "Verkäuferin"}
  ],
  "document_type": "Kaufvertrag mit Auflassung eines Grundstücks",
  "overall_confidence": 0.91,
  "notes": "Zusätzlich Grundschuldbestellung möglich – im Text nicht explizit erwähnt."
}
```

**Weitere 2–3 Beispiele** (GmbH-Gründung, Testament, Vorsorgevollmacht) sollten in der finalen Prompt-Datei stehen. Sie helfen dem Modell enorm bei der korrekten Klassifikation.

---

## Prompt-Engineering-Tipps für spätere Verbesserungen

1. **Chain-of-Thought** leicht einbauen: „Denke Schritt für Schritt: 1. Welche Tatbestände sind hier relevant? 2. Welche Werte gehören dazu? 3. Welche KV-Nummer passt am besten?“
2. **Self-Consistency**: Bei niedriger Confidence mehrere Samples ziehen und Mehrheit bilden (optional, rechenintensiv).
3. **RAG-Erweiterung** (später): Lokale Embeddings der wichtigsten GNotKG-Abschnitte + Kostenverzeichnis abrufen und in den Prompt injizieren.
4. **Iterative Verbesserung**: Nach realen Tests die Few-Shot-Beispiele mit echten Fehlern/Korrekturen erweitern.

---

## Versionierung der Prompts

- Jede Prompt-Version in `prompts/extraction_vX.txt` speichern.
- In der App die verwendete Prompt-Version mitloggen (Auditierbarkeit).
- Bei schlechter Extraktionsqualität → neue Version mit besseren Examples erstellen.

---

**Hinweis für den Coding-Agent**:  
Der Prompt ist das Herz der Extraktionsqualität. Investiere Zeit in gute Few-Shot-Beispiele aus realen (anonymisierten) Urkunden. Das spart später sehr viel manuelle Nacharbeit durch den Notar.