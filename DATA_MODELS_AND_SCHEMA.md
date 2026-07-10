# Datenmodelle & Schema – Notar GNotKG Assistent

## Pydantic-Modelle (core/models.py)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

class NotaryProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    firm_name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    bank_name: str
    iban: str
    bic: Optional[str] = None
    logo_path: Optional[str] = None          # lokaler Pfad oder Base64
    updated_at: datetime = Field(default_factory=datetime.now)

class ExtractedPosition(BaseModel):
    kv_number: Optional[str] = None
    description: str
    business_value_eur: Optional[float] = None
    source_reference: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    llm_suggestion: bool = True

class FinalInvoicePosition(BaseModel):
    kv_number: str
    description: str
    business_value_eur: Optional[float]
    fee_amount: float
    source_reference: str
    was_overridden: bool = False
    override_reason: Optional[str] = None
    calculation_details: str               # z.B. "Tabelle B, 1,0-fach"

class GeneratedInvoice(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    notary: NotaryProfile
    original_document: str                 # Dateiname oder Hash
    positions: list[FinalInvoicePosition]
    total_net: float
    vat_rate: float = 0.19
    vat_amount: float
    total_gross: float
    output_formats: list[Literal["docx", "rtf", "txt"]]
    fee_engine_version: str
    disclaimer: str = "Diese Rechnung wurde mit Unterstützung eines KI-Tools erstellt. Die alleinige Verantwortung liegt beim Notar."

class AuditLogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    invoice_id: UUID
    timestamp: datetime
    action: Literal["extraction", "edit", "confirmation", "generation"]
    llm_model: Optional[str] = None
    positions_before: Optional[list] = None
    positions_after: Optional[list] = None
    user: str = "Notar"                    # oder aus Profil
    notes: Optional[str] = None
```

## SQLite-Schema (empfohlen)

Tabelle `invoices`:
```sql
CREATE TABLE invoices (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    original_document TEXT,
    total_gross REAL,
    fee_engine_version TEXT,
    json_data TEXT                  -- vollständiges GeneratedInvoice als JSON
);
```

Tabelle `audit_logs`:
```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    invoice_id TEXT,
    timestamp TEXT,
    action TEXT,
    llm_model TEXT,
    details TEXT,                   -- JSON mit Before/After etc.
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);
```

Tabelle `notary_profile` (Singleton):
```sql
CREATE TABLE notary_profile (
    id TEXT PRIMARY KEY,
    json_data TEXT
);
```

## Dateisystem-Struktur (neben SQLite)

```
data/
├── notary_profile.json
├── fee_tables/
│   └── v2026_01.json
├── generated_invoices/
│   └── {invoice_id}/
│       ├── Rechnung_....docx
│       ├── Rechnung_....rtf
│       └── Traceability_....xlsx
└── history/
    └── audit_full.jsonl            # append-only Log (einfach zu parsen)
```

---

Diese Modelle und Schemata bilden die Grundlage für typsichere, auditierbare Datenverarbeitung.