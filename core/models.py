"""Pydantic-Modelle für den Notar GNotKG Assistent."""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExtractionQuality(StrEnum):
    GOOD = "good"
    OCR_FALLBACK = "ocr_fallback"
    POOR = "poor"


class ParsedDocument(BaseModel):
    full_text: str
    pages: int
    metadata: dict = Field(default_factory=dict)
    extraction_quality: ExtractionQuality = ExtractionQuality.GOOD


class NotaryProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    firm_name: str
    address: str
    phone: str | None = None
    email: str | None = None
    bank_name: str
    iban: str
    bic: str | None = None
    tax_number: str | None = None
    vat_id: str | None = None
    logo_path: str | None = None
    updated_at: datetime = Field(default_factory=datetime.now)


class ExtractedPosition(BaseModel):
    kv_number: str | None = Field(
        default=None,
        description="KV-Nummer aus dem Kostenverzeichnis, z.B. '21200'",
    )
    description: str = Field(..., description="Beschreibung des Tatbestands")
    business_value_eur: float | None = Field(default=None, description="Geschäftswert in EUR")
    source_reference: str = Field(
        ..., description="Fundstelle im Dokument, z.B. 'Seite 3, Ziffer 4.1'"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Begründung des Vorschlags")
    llm_suggestion: bool = True


class ExtractionResult(BaseModel):
    extracted_positions: list[ExtractedPosition] = Field(default_factory=list)
    parties: list[dict] = Field(default_factory=list)
    document_type: str = ""
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: str = ""


class FinalInvoicePosition(BaseModel):
    kv_number: str
    description: str
    business_value_eur: float | None = None
    fee_amount: float = 0.0
    source_reference: str = ""
    was_overridden: bool = False
    override_reason: str | None = None
    calculation_details: str = ""


class GeneratedInvoice(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    notary: NotaryProfile
    original_document: str = ""
    positions: list[FinalInvoicePosition] = Field(default_factory=list)
    total_net: float = 0.0
    vat_rate: float = Field(default=0.19)
    vat_amount: float = 0.0
    total_gross: float = 0.0
    output_formats: list[Literal["docx", "rtf", "txt"]] = Field(default=["docx"])
    fee_engine_version: str = ""
    disclaimer: str = (
        "Diese Rechnung wurde mit Unterstützung eines KI-Tools erstellt. "
        "Die alleinige Verantwortung für die Richtigkeit und die Einhaltung "
        "des Gerichts- und Notarkostengesetzes (GNotKG) liegt beim Notar."
    )


class AuditLogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    invoice_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)
    action: Literal["extraction", "edit", "confirmation", "generation"]
    llm_model: str | None = None
    positions_before: list | None = None
    positions_after: list | None = None
    user: str = "Notar"
    notes: str | None = None


class FeeCalculation(BaseModel):
    kv_number: str
    description: str
    business_value: float | None = None
    fee_amount: float = 0.0
    calculation_basis: str = ""
    notes: str | None = None


class GnotkgStatus(BaseModel):
    local_version: str
    remote_version: str | None = None
    is_current: bool = True
    checked_at: datetime | None = None
    error: str | None = None
