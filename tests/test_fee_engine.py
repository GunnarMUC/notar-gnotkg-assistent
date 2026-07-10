"""Tests für die Fee Engine – deterministische GNotKG-Berechnung."""

import pytest

from core.fee_engine import FeeEngine


@pytest.fixture
def engine() -> FeeEngine:
    return FeeEngine()


class TestFeeEngineLookup:
    def test_lowest_bracket(self, engine):
        assert engine._lookup_table_b(500) == 23.0

    def test_second_bracket(self, engine):
        assert engine._lookup_table_b(2000) == 38.0

    def test_mid_bracket(self, engine):
        assert engine._lookup_table_b(25000) == 124.0

    def test_boundary_exact(self, engine):
        assert engine._lookup_table_b(1500) == 23.0

    def test_high_value(self, engine):
        assert engine._lookup_table_b(1000000) == 2360.0


class TestFeeEngineCalculate:
    def test_beurkundung_simple(self, engine):
        calc = engine.calculate_position("21200", 385000)
        assert calc.kv_number == "21200"
        assert calc.fee_amount == 1060.0
        assert "1.0-fach" in calc.calculation_basis

    def test_vollzug_flattax(self, engine):
        calc = engine.calculate_position("22114", None)
        assert calc.fee_amount == 15.0
        assert "Pauschalgebühr" in calc.calculation_basis

    def test_betreuung_2fach(self, engine):
        calc = engine.calculate_position("22125", 385000)
        assert calc.fee_amount == 2120.0  # 1060 * 2.0

    def test_grundschuld_half(self, engine):
        calc = engine.calculate_position("23300", 300000)
        assert calc.fee_amount == 420.0  # 840 * 0.5

    def test_unknown_kv(self, engine):
        calc = engine.calculate_position("99999", 1000)
        assert calc.fee_amount == 0.0
        assert "Unbekannte KV" in calc.description

    def test_value_based_no_value(self, engine):
        calc = engine.calculate_position("21200", None)
        assert calc.fee_amount == 0.0

    def test_min_fee_enforced(self, engine):
        calc = engine.calculate_position("25100", 100)
        # 0.2 * 23 = 4.60 → min 20.0
        assert calc.fee_amount == 20.0

    def test_max_fee_enforced(self, engine):
        calc = engine.calculate_position("24102", 10_000_000)
        # 0.75 * 14360 = 10770 → max 1000.0
        assert calc.fee_amount == 1000.0


class TestFeeEngineTotals:
    def test_invoice_total(self, engine):
        calcs = [
            engine.calculate_position("21200", 385000),
            engine.calculate_position("22114", None),
        ]
        total = engine.calculate_invoice_total(calcs, auslagen=5.0)
        assert total["total_fees"] == 1075.0  # 1060 + 15
        assert total["total_net"] == 1080.0   # 1075 + 5
        assert total["vat_amount"] == 205.2   # 1080 * 0.19
        assert total["total_gross"] == 1285.2


class TestFeeEngineValidation:
    def test_missing_vollzug_warning(self, engine):
        calcs = [engine.calculate_position("21200", 100000)]
        warnings = engine.validate_combination(calcs)
        assert len(warnings) == 1
        assert "22114" in warnings[0]

    def test_no_warnings_with_vollzug(self, engine):
        calcs = [
            engine.calculate_position("21200", 100000),
            engine.calculate_position("22114", None),
        ]
        warnings = engine.validate_combination(calcs)
        assert len(warnings) == 0


class TestFeeEngineKvList:
    def test_available_kv_numbers(self, engine):
        kv_numbers = engine.get_available_kv_numbers()
        assert "21200" in kv_numbers
        assert "22114" in kv_numbers
        assert len(kv_numbers) >= 8
