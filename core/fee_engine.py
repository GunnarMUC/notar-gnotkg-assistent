"""GNotKG Fee Engine – Deterministische Gebührenberechnung (Tabelle B).

KEINE LLM-Aufrufe. Alle Beträge basieren auf den versionierten Tabellen.
"""

from pathlib import Path

from core.config import get_settings
from core.models import FeeCalculation


class FeeEngine:
    """Deterministische GNotKG-Gebührenberechnung nach Anlage 1+2."""

    # Gebührentabelle B (Anlage 2 GNotKG) – Stand 2026
    # Format: (bis_Wert_in_EUR, Gebühr_bei_10/10_voller_Gebühr)
    TABLE_B = [
        (1500.0, 23.0),
        (3000.0, 38.0),
        (6000.0, 58.0),
        (13000.0, 83.0),
        (25000.0, 124.0),
        (50000.0, 200.0),
        (75000.0, 276.0),
        (100000.0, 354.0),
        (125000.0, 432.0),
        (155000.0, 510.0),
        (200000.0, 620.0),
        (250000.0, 730.0),
        (300000.0, 840.0),
        (350000.0, 950.0),
        (400000.0, 1060.0),
        (450000.0, 1170.0),
        (500000.0, 1280.0),
        (550000.0, 1390.0),
        (650000.0, 1570.0),
        (750000.0, 1750.0),
        (850000.0, 1930.0),
        (950000.0, 2110.0),
        (1100000.0, 2360.0),
        (1300000.0, 2640.0),
        (1500000.0, 2920.0),
        (1750000.0, 3290.0),
        (2000000.0, 3660.0),
        (2250000.0, 4060.0),
        (2500000.0, 4460.0),
        (2750000.0, 4860.0),
        (3000000.0, 5260.0),
        (3500000.0, 5910.0),
        (4000000.0, 6560.0),
        (4500000.0, 7210.0),
        (5000000.0, 7860.0),
        (5500000.0, 8510.0),
        (6000000.0, 9160.0),
        (6500000.0, 9810.0),
        (7000000.0, 10460.0),
        (7500000.0, 11110.0),
        (8000000.0, 11760.0),
        (8500000.0, 12410.0),
        (9000000.0, 13060.0),
        (9500000.0, 13710.0),
        (10000000.0, 14360.0),
        (15000000.0, 20360.0),
        (20000000.0, 26360.0),
        (25000000.0, 32360.0),
        (30000000.0, 38360.0),
        (35000000.0, 44360.0),
        (40000000.0, 50360.0),
        (45000000.0, 56360.0),
        (50000000.0, 62360.0),
        (60000000.0, 74360.0),
    ]

    # KV-Nummern-Definitionen (Kostenverzeichnis Anlage 1, Auszug)
    KV_DEFINITIONS = {
        "21200": {
            "description": "Beurkundungsverfahren",
            "fee_type": "value_based",
            "rate": 1.0,
            "table": "B",
            "min_fee": 120.0,
        },
        "21201": {
            "description": "Beurkundung bei verschiedenen Vertragsteilen",
            "fee_type": "value_based",
            "rate": 1.0,
            "table": "B",
        },
        "22110": {
            "description": "Vollzug im Grundbuch",
            "fee_type": "value_based",
            "rate": 0.5,
            "table": "B",
            "min_fee": 60.0,
            "max_fee": 1000.0,
        },
        "22114": {
            "description": "Elektronischer Vollzug und XML-Strukturdaten",
            "fee_type": "flat",
            "flat_fee": 15.0,
        },
        "22125": {
            "description": "Betreuungstätigkeit (2,0)",
            "fee_type": "value_based",
            "rate": 2.0,
            "table": "B",
            "min_fee": 60.0,
        },
        "22200": {
            "description": "Treuhandauftrag",
            "fee_type": "value_based",
            "rate": 1.0,
            "table": "B",
        },
        "23300": {
            "description": "Grundschuldbestellung (0,5)",
            "fee_type": "value_based",
            "rate": 0.5,
            "table": "B",
            "min_fee": 60.0,
        },
        "24102": {
            "description": "Beratung",
            "fee_type": "value_based",
            "rate": 0.75,
            "table": "B",
            "max_fee": 1000.0,
        },
        "25100": {
            "description": "Beglaubigung",
            "fee_type": "value_based",
            "rate": 0.2,
            "table": "B",
            "min_fee": 20.0,
            "max_fee": 750.0,
        },
        "25200": {
            "description": "Bescheinigung",
            "fee_type": "flat",
            "flat_fee": 30.0,
        },
    }

    def __init__(self, table_version: str = "v2026_01"):
        self.version = f"GNotKG_Stand_2026-01-01_{table_version}"

    def calculate_position(
        self,
        kv_number: str,
        business_value: float | None = None,
        multiplier: float = 1.0,
    ) -> FeeCalculation:
        """Berechnet eine einzelne Gebührenposition.

        Args:
            kv_number: KV-Nummer aus dem Kostenverzeichnis (z.B. '21200').
            business_value: Geschäftswert in EUR.
            multiplier: Gebührensatz-Multiplikator (default 1.0).

        Returns:
            FeeCalculation mit exaktem Betrag und Berechnungsgrundlage.
        """
        kv_def = self.KV_DEFINITIONS.get(kv_number)
        if kv_def is None:
            return FeeCalculation(
                kv_number=kv_number,
                description=f"Unbekannte KV-Nr. {kv_number} – bitte manuell prüfen",
                business_value=business_value,
                fee_amount=0.0,
                calculation_basis="Nicht definiert",
                notes="Diese KV-Nummer ist nicht in der Fee-Engine hinterlegt.",
            )

        description = kv_def["description"]
        fee_type = kv_def["fee_type"]

        if fee_type == "flat":
            flat_fee = kv_def.get("flat_fee", 0.0)
            return FeeCalculation(
                kv_number=kv_number,
                description=description,
                business_value=None,
                fee_amount=round(flat_fee, 2),
                calculation_basis=f"Pauschalgebühr nach KV {kv_number}",
            )

        if fee_type == "value_based" and business_value is not None:
            if business_value <= 0:
                return FeeCalculation(
                    kv_number=kv_number,
                    description=description,
                    business_value=business_value,
                    fee_amount=0.0,
                    calculation_basis="Ungültiger Geschäftswert (≤ 0)",
                    notes="Der Geschäftswert muss größer als 0 sein.",
                )
            if business_value > 100_000_000:
                return FeeCalculation(
                    kv_number=kv_number,
                    description=description,
                    business_value=business_value,
                    fee_amount=0.0,
                    calculation_basis="Geschäftswert außerhalb des Bereichs",
                    notes=(
                        f"Geschäftswert {business_value:,.2f} € übersteigt "
                        f"100 Mio. € – bitte manuell prüfen."
                    ),
                )
            rate = kv_def.get("rate", 1.0) * multiplier
            table_fee = self._lookup_table_b(business_value)
            fee = round(table_fee * rate, 2)

            min_fee = kv_def.get("min_fee")
            max_fee = kv_def.get("max_fee")
            if min_fee is not None:
                fee = max(fee, min_fee)
            if max_fee is not None:
                fee = min(fee, max_fee)

            return FeeCalculation(
                kv_number=kv_number,
                description=description,
                business_value=business_value,
                fee_amount=fee,
                calculation_basis=(
                    f"Tabelle B, {rate}-fach, "
                    f"Geschäftswert {business_value:,.2f} €"
                ),
            )

        return FeeCalculation(
            kv_number=kv_number,
            description=description,
            business_value=business_value,
            fee_amount=0.0,
            calculation_basis="Kein Geschäftswert – manuell prüfen",
        )

    def _lookup_table_b(self, value: float) -> float:
        """Ermittelt die volle Gebühr (10/10) nach Tabelle B."""
        for bracket_max, fee in self.TABLE_B:
            if value <= bracket_max:
                return fee
        # Jenseits der letzten Staffel: linear extrapolieren oder letzten Wert
        return self.TABLE_B[-1][1] + (value - self.TABLE_B[-1][0]) * 0.006

    def calculate_invoice_total(
        self,
        positions: list[FeeCalculation],
        auslagen: float = 0.0,
        vat_rate: float = 0.19,
    ) -> dict:
        """Berechnet Endsummen inkl. Auslagen und USt."""
        total_fees = sum(p.fee_amount for p in positions)
        total_net = total_fees + auslagen
        vat_amount = round(total_net * vat_rate, 2)
        total_gross = total_net + vat_amount
        return {
            "total_fees": total_fees,
            "auslagen": auslagen,
            "total_net": total_net,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "total_gross": total_gross,
            "fee_engine_version": self.version,
        }

    def get_available_kv_numbers(self) -> list[str]:
        return sorted(self.KV_DEFINITIONS.keys())

    def validate_combination(self, positions: list[FeeCalculation]) -> list[str]:
        """Gibt Warnungen bei unüblichen Kombinationen zurück."""
        warnings = []
        kv_numbers = [p.kv_number for p in positions]
        if "21200" in kv_numbers and "22114" not in kv_numbers:
            warnings.append(
                "Beurkundung (21200) ohne elektronischen Vollzug (22114) – "
                "bitte prüfen."
            )
        return warnings
