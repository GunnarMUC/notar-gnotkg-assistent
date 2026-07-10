"""GNotKG Fee Engine – Deterministische Gebührenberechnung (Tabelle B).

KEINE LLM-Aufrufe. Alle Beträge basieren auf den versionierten JSON-Tabellen.
"""

import json
from typing import Any, cast

from loguru import logger

from core.config import get_settings
from core.models import FeeCalculation


class FeeEngineError(RuntimeError):
    """Fehler beim Laden oder Verarbeiten der Gebührentabelle."""


class FeeEngine:
    """Deterministische GNotKG-Gebührenberechnung nach Anlage 1+2."""

    def __init__(self, table_version: str = "v2026_01"):
        self.table_version = table_version
        self._data: dict[str, Any] = self._load_table(table_version)
        self.version = self._data.get("version", f"GNotKG_{table_version}")

    @staticmethod
    def _load_table(table_version: str) -> dict[str, Any]:
        """Lädt die Gebührentabelle aus einer versionierten JSON-Datei.

        Args:
            table_version: Versionsbezeichner (z.B. 'v2026_01').

        Returns:
            Geladene Tabelle als Dictionary.
        """
        settings = get_settings()
        table_path = settings.fee_tables_dir_path / f"{table_version}.json"

        if not table_path.exists():
            logger.error(f"Gebührentabelle nicht gefunden: {table_path}")
            raise FeeEngineError(
                f"Gebührentabelle für Version '{table_version}' nicht gefunden: {table_path}"
            )

        try:
            with table_path.open(encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen der Gebührentabelle: {e}")
            raise FeeEngineError(
                f"Gebührentabelle '{table_version}' enthält ungültiges JSON"
            ) from e

        if "table" not in data or "brackets" not in data["table"]:
            raise FeeEngineError(
                f"Gebührentabelle '{table_version}' enthält keinen 'table.brackets'-Block"
            )
        if "kv_definitions" not in data:
            raise FeeEngineError(
                f"Gebührentabelle '{table_version}' enthält keine 'kv_definitions'"
            )

        return data

    @property
    def _brackets(self) -> list[dict[str, float]]:
        return cast(list[dict[str, float]], self._data["table"]["brackets"])

    @property
    def _extrapolation_rate(self) -> float:
        return cast(float, self._data["table"].get("extrapolation_rate", 0.006))

    @property
    def _kv_definitions(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._data["kv_definitions"])

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
        kv_def = self._kv_definitions.get(kv_number)
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
                    f"Tabelle B, {rate}-fach, Geschäftswert {business_value:,.2f} €"
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
        for bracket in self._brackets:
            if value <= bracket["max_value"]:
                return bracket["fee"]
        # Jenseits der letzten Staffel: linear extrapolieren oder letzten Wert
        last_bracket = self._brackets[-1]
        return (
            cast(float, last_bracket["fee"])
            + (value - cast(float, last_bracket["max_value"])) * self._extrapolation_rate
        )

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
        return sorted(self._kv_definitions.keys())

    def validate_combination(self, positions: list[FeeCalculation]) -> list[str]:
        """Gibt Warnungen bei unüblichen Kombinationen zurück."""
        warnings = []
        kv_numbers = [p.kv_number for p in positions]
        if "21200" in kv_numbers and "22114" not in kv_numbers:
            warnings.append(
                "Beurkundung (21200) ohne elektronischen Vollzug (22114) – bitte prüfen."
            )
        return warnings

    def get_table_metadata(self) -> dict:
        """Gibt Metadaten der geladenen Gebührentabelle zurück."""
        return {
            "version": self.version,
            "description": self._data.get("description", ""),
            "valid_from": self._data.get("valid_from", ""),
            "source": self._data.get("source", ""),
            "currency": self._data.get("currency", "EUR"),
            "table_name": self._data.get("table", {}).get("name", ""),
        }
