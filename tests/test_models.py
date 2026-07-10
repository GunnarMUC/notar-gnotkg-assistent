"""Tests für Konfiguration und Models."""

from core.config import get_settings
from core.models import (
    ExtractedPosition,
    FeeCalculation,
    GeneratedInvoice,
    NotaryProfile,
)


class TestSettings:
    def test_defaults(self):
        s = get_settings()
        assert s.ollama_host == "localhost"
        assert s.ollama_port == 11434
        assert s.app_default_output_format == "docx"

    def test_ollama_url(self):
        s = get_settings()
        assert s.ollama_url == "http://localhost:11434"


class TestModels:
    def test_notary_profile_minimal(self):
        p = NotaryProfile(
            name="Test Notar",
            firm_name="Kanzlei Test",
            address="Teststr. 1, 80333 München",
            bank_name="Testbank",
            iban="DE12345678901234567890",
        )
        assert p.name == "Test Notar"

    def test_extracted_position(self):
        p = ExtractedPosition(
            kv_number="21200",
            description="Beurkundung",
            business_value_eur=385000.0,
            source_reference="Seite 1",
            confidence=0.95,
            reasoning="Test",
        )
        assert p.kv_number == "21200"

    def test_fee_calculation(self):
        c = FeeCalculation(
            kv_number="21200",
            description="Test",
            business_value=100000,
            fee_amount=354.0,
            calculation_basis="Tabelle B, 1,0-fach",
        )
        assert c.fee_amount == 354.0

    def test_generated_invoice_defaults(self):
        p = NotaryProfile(name="T", firm_name="K", address="A", bank_name="B", iban="I")
        invoice = GeneratedInvoice(notary=p)
        assert invoice.vat_rate == 0.19
        assert invoice.total_gross == 0.0
        assert "alleinige Verantwortung" in invoice.disclaimer
