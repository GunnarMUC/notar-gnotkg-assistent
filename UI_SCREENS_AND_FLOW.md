# UI Screens & User Flow – Notar GNotKG Assistent (Streamlit)

## Gesamter User Flow (MVP)

```
Start App
   │
   ▼
[Sidebar] Notar-Profil + LLM-Auswahl + GNotKG-Status (grün/gelb/rot)
   │
   ▼
[Hauptbereich] Upload-Bereich (Drag & Drop)
   │
   ▼
Nach Upload → Button "Dokument analysieren"
   │
   ▼
Extraktion läuft (Spinner + Fortschritt)
   │
   ▼
Ergebnis-Screen:
   ┌───────────────────────────────┬──────────────────────────────┐
   │ Original-Urkunde (Vorschau /  │ Editierbare Positionen-Tabelle│
   │ "Datei öffnen")               │ (st.data_editor)             │
   │                               │                              │
   │                               │ + Button "Neue Position"     │
   │                               │ + Button "Neu berechnen"     │
   └───────────────────────────────┴──────────────────────────────┘

   Unten: Auslagen-Eingabe + Live-Summe (netto / brutto)

   Button: "Finale Positionen bestätigen"  (Pflicht-Checkbox + Hinweis)
   │
   ▼
Vorschau der Honorarrechnung (HTML-ähnlich oder DOCX-Preview)
   │
   ▼
Auswahl Ausgabeformat (DOCX / RTF / TXT) + "Rechnung + Excel-Log erzeugen"
   │
   ▼
Download-Buttons + Erfolgsmeldung + Link zur Historie
```

## Wichtige Streamlit-Komponenten & Best Practices

- `st.sidebar` für globale Einstellungen und Status
- `st.file_uploader` mit `type=["pdf", "docx", "rtf", "txt"]`
- `st.data_editor` für die zentrale editierbare Tabelle (mit `column_config` für schöne Darstellung)
- `st.columns([2, 3])` für Original vs. Tabelle
- `st.success`, `st.warning`, `st.error` für klare Rückmeldungen
- `st.download_button` für alle generierten Dateien
- Session State Keys: `current_extraction`, `final_positions`, `current_invoice` etc.

## Empfohlene visuelle Gestaltung

- Klare Trennung: **KI-Vorschlag** (hellblau/grau) vs. **Final bestätigt** (grün)
- Bei Overrides: Gelbe Markierung + Tooltip mit Begründung
- Deutlicher roter Disclaimer-Bereich auf jeder generierten Rechnung
- Fortschrittsanzeige bei LLM-Aufrufen und bei längeren Operationen

---

**Ziel der UI**: So einfach wie möglich, aber mit maximaler Transparenz und Kontrolle für den Notar.