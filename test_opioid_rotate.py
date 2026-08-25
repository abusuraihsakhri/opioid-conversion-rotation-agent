"""
Tests for Opioid Equianalgesic Conversion & Rotation Calculator.
"""
import pytest
from opioid_rotate import (
    calculate_mme,
    convert_opioid,
    convert_to_methadone,
    generate_taper_schedule,
    convert_to_fentanyl_patch,
    full_conversion_assessment,
    main,
    EQUIANALGESIC_TABLE,
)


# ============================================================================
# MME Calculation Tests
# ============================================================================

class TestMME:
    def test_morphine_po_standard(self):
        # 30mg PO morphine * 4 times/day = 120mg/day * 1.0 = 120 MME
        result = calculate_mme([{"opioid": "morphine_po", "dose_mg": 30, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 120.0) < 0.1

    def test_oxycodone_po(self):
        # 10mg * 4 = 40mg/day * 1.5 = 60 MME
        result = calculate_mme([{"opioid": "oxycodone_po", "dose_mg": 10, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 60.0) < 0.1

    def test_hydrocodone_po(self):
        # 10mg * 4 = 40mg/day * 1.0 = 40 MME
        result = calculate_mme([{"opioid": "hydrocodone_po", "dose_mg": 10, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 40.0) < 0.1

    def test_hydromorphone_po(self):
        # 4mg * 4 = 16mg/day * 4.0 = 64 MME
        result = calculate_mme([{"opioid": "hydromorphone_po", "dose_mg": 4, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 64.0) < 0.1

    def test_fentanyl_patch(self):
        # 50 mcg/hr * 2.4 = 120 MME/day
        result = calculate_mme([{"opioid": "fentanyl_patch", "dose_mcg_per_hr": 50}])
        assert abs(result["total_daily_mme"] - 120.0) < 0.1

    def test_codeine_po(self):
        # 60mg * 4 = 240mg/day * 0.15 = 36 MME
        result = calculate_mme([{"opioid": "codeine_po", "dose_mg": 60, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 36.0) < 0.1

    def test_tramadol_po(self):
        # 50mg * 4 = 200mg/day * 0.15 = 30 MME
        result = calculate_mme([{"opioid": "tramadol_po", "dose_mg": 50, "doses_per_day": 4}])
        assert abs(result["total_daily_mme"] - 30.0) < 0.1

    def test_multiple_opioids(self):
        result = calculate_mme([
            {"opioid": "morphine_po", "dose_mg": 15, "doses_per_day": 4},
            {"opioid": "oxycodone_po", "dose_mg": 5, "doses_per_day": 2}
        ])
        # Morphine: 15*4*1.0 = 60, Oxycodone: 5*2*1.5 = 15, Total = 75
        assert abs(result["total_daily_mme"] - 75.0) < 0.1
        assert result["num_opioids"] == 2
        assert result["polypharmacy_warning"] is True

    def test_risk_levels(self):
        # Low risk
        result = calculate_mme([{"opioid": "morphine_po", "dose_mg": 5, "doses_per_day": 4}])
        assert result["risk_level"] == "LOW"

        # Moderate risk (50+ MME)
        result = calculate_mme([{"opioid": "morphine_po", "dose_mg": 15, "doses_per_day": 4}])
        assert result["risk_level"] == "MODERATE"

        # High risk (90+ MME)
        result = calculate_mme([{"opioid": "morphine_po", "dose_mg": 25, "doses_per_day": 4}])
        assert result["risk_level"] == "HIGH"

        # Very high risk (200+ MME)
        result = calculate_mme([{"opioid": "morphine_po", "dose_mg": 60, "doses_per_day": 4}])
        assert result["risk_level"] == "VERY_HIGH"

    def test_unknown_opioid(self):
        with pytest.raises(ValueError):
            calculate_mme([{"opioid": "unknown_opioid", "dose_mg": 10, "doses_per_day": 1}])

    def test_empty_list(self):
        with pytest.raises(ValueError):
            calculate_mme([])

    def test_invalid_dose(self):
        with pytest.raises(ValueError):
            calculate_mme([{"opioid": "morphine_po", "dose_mg": 0, "doses_per_day": 1}])


# ============================================================================
# Opioid Conversion Tests
# ============================================================================

class TestConversion:
    def test_morphine_to_oxycodone(self):
        result = convert_opioid("morphine_po", 15, 4, "oxycodone_po")
        # 15*4 = 60mg morphine PO = 60 MME
        # 60 MME / 1.5 = 40mg oxycodone/day
        # With 25% reduction: 30mg/day
        assert result["source"]["daily_mme"] == 60.0
        assert result["target"]["reduced_daily_dose_mg"] == 30.0

    def test_oxycodone_to_morphine(self):
        result = convert_opioid("oxycodone_po", 10, 4, "morphine_po")
        # 10*4 = 40mg oxycodone * 1.5 = 60 MME
        # 60 MME / 1.0 = 60mg morphine/day
        # With 25% reduction: 45mg/day
        assert result["source"]["daily_mme"] == 60.0
        assert result["target"]["reduced_daily_dose_mg"] == 45.0

    def test_cross_tolerance_reduction(self):
        no_reduction = convert_opioid("morphine_po", 15, 4, "oxycodone_po", cross_tolerance_reduction=0.0)
        with_reduction = convert_opioid("morphine_po", 15, 4, "oxycodone_po", cross_tolerance_reduction=0.25)
        assert no_reduction["target"]["reduced_daily_dose_mg"] > with_reduction["target"]["reduced_daily_dose_mg"]

    def test_higher_reduction(self):
        result_25 = convert_opioid("morphine_po", 15, 4, "oxycodone_po", cross_tolerance_reduction=0.25)
        result_50 = convert_opioid("morphine_po", 15, 4, "oxycodone_po", cross_tolerance_reduction=0.50)
        assert result_25["target"]["reduced_daily_dose_mg"] > result_50["target"]["reduced_daily_dose_mg"]

    def test_morphine_to_hydromorphone(self):
        result = convert_opioid("morphine_po", 15, 4, "hydromorphone_po")
        # 60 MME / 4.0 = 15mg hydromorphone/day
        # With 25% reduction: 11.25mg/day
        assert abs(result["target"]["equianalgesic_daily_dose_mg"] - 15.0) < 0.1

    def test_unknown_source(self):
        with pytest.raises(ValueError):
            convert_opioid("unknown", 10, 4, "morphine_po")

    def test_unknown_target(self):
        with pytest.raises(ValueError):
            convert_opioid("morphine_po", 10, 4, "unknown")

    def test_invalid_reduction(self):
        with pytest.raises(ValueError):
            convert_opioid("morphine_po", 10, 4, "oxycodone_po", cross_tolerance_reduction=1.5)


# ============================================================================
# Methadone Conversion Tests
# ============================================================================

class TestMethadoneConversion:
    def test_low_mme(self):
        result = convert_to_methadone(80)
        assert result["conversion_ratio"] == "4:1 (morphine:methadone)"
        assert result["reduced_daily_dose_mg"] > 0

    def test_moderate_mme(self):
        result = convert_to_methadone(200)
        assert result["conversion_ratio"] == "8:1 (morphine:methadone)"

    def test_high_mme(self):
        result = convert_to_methadone(500)
        assert result["conversion_ratio"] == "12:1 (morphine:methadone)"

    def test_very_high_mme(self):
        result = convert_to_methadone(800)
        assert result["conversion_ratio"] == "15:1 (morphine:methadone)"

    def test_extreme_mme(self):
        result = convert_to_methadone(1200)
        assert result["conversion_ratio"] == "20:1 (morphine:methadone)"

    def test_cross_tolerance_applied(self):
        result = convert_to_methadone(200, cross_tolerance_reduction=0.50)
        assert result["cross_tolerance_reduction_percent"] == 50.0

    def test_critical_warnings_present(self):
        result = convert_to_methadone(200)
        assert len(result["critical_warnings"]) > 0

    def test_invalid_mme(self):
        with pytest.raises(ValueError):
            convert_to_methadone(0)


# ============================================================================
# Fentanyl Patch Tests
# ============================================================================

class TestFentanylPatch:
    def test_conversion(self):
        result = convert_to_fentanyl_patch(120)
        # 120 / 2.4 = 50 mcg/hr
        assert abs(result["equianalgesic_mcg_per_hr"] - 50.0) < 0.1

    def test_cross_tolerance(self):
        result = convert_to_fentanyl_patch(120, cross_tolerance_reduction=0.25)
        # 50 * 0.75 = 37.5 mcg/hr
        assert abs(result["reduced_mcg_per_hr"] - 37.5) < 0.1

    def test_available_sizes(self):
        result = convert_to_fentanyl_patch(120)
        assert 25 in result["available_sizes"]
        assert 50 in result["available_sizes"]

    def test_warnings_present(self):
        result = convert_to_fentanyl_patch(120)
        assert len(result["warnings"]) > 0

    def test_invalid_mme(self):
        with pytest.raises(ValueError):
            convert_to_fentanyl_patch(0)


# ============================================================================
# Tapering Tests
# ============================================================================

class TestTapering:
    def test_basic_taper(self):
        result = generate_taper_schedule(100, 0, 10.0, 7)
        assert result["total_steps"] > 1
        assert result["schedule"][0]["mme"] == 100.0
        assert result["schedule"][-1]["mme"] == 0.0

    def test_partial_taper(self):
        result = generate_taper_schedule(100, 50, 10.0, 7)
        assert result["schedule"][-1]["mme"] == 50.0

    def test_slow_taper(self):
        result = generate_taper_schedule(100, 0, 10.0, 28)
        assert result["taper_speed"] == "SLOW (recommended for long-term use)"

    def test_fast_taper(self):
        result = generate_taper_schedule(100, 0, 10.0, 3)
        assert result["taper_speed"] == "FAST (higher withdrawal risk)"

    def test_monitoring_notes(self):
        result = generate_taper_schedule(100, 0)
        assert len(result["monitoring_notes"]) > 0

    def test_invalid_target(self):
        with pytest.raises(ValueError):
            generate_taper_schedule(100, 150)

    def test_invalid_reduction(self):
        with pytest.raises(ValueError):
            generate_taper_schedule(100, 0, 100.0)


# ============================================================================
# Equianalgesic Table Tests
# ============================================================================

class TestEquianalgesicTable:
    def test_morphine_po_is_baseline(self):
        assert EQUIANALGESIC_TABLE["morphine_po"]["dose"] == 30.0
        assert EQUIANALGESIC_TABLE["morphine_po"]["mme_factor"] == 1.0

    def test_morphine_iv_ratio(self):
        # 30mg PO = 10mg IV
        assert EQUIANALGESIC_TABLE["morphine_iv"]["dose"] == 10.0
        assert EQUIANALGESIC_TABLE["morphine_iv"]["mme_factor"] == 3.0

    def test_oxycodone_ratio(self):
        # 30mg morphine PO = 20mg oxycodone PO
        assert EQUIANALGESIC_TABLE["oxycodone_po"]["dose"] == 20.0
        assert EQUIANALGESIC_TABLE["oxycodone_po"]["mme_factor"] == 1.5

    def test_hydromorphone_ratio(self):
        assert EQUIANALGESIC_TABLE["hydromorphone_po"]["dose"] == 7.5
        assert EQUIANALGESIC_TABLE["hydromorphone_po"]["mme_factor"] == 4.0

    def test_codeine_ratio(self):
        assert EQUIANALGESIC_TABLE["codeine_po"]["dose"] == 200.0
        assert EQUIANALGESIC_TABLE["codeine_po"]["mme_factor"] == 0.15

    def test_tramadol_ratio(self):
        assert EQUIANALGESIC_TABLE["tramadol_po"]["dose"] == 100.0

    def test_fentanyl_patch(self):
        assert EQUIANALGESIC_TABLE["fentanyl_patch"]["dose"] == 25.0


# ============================================================================
# Full Assessment Tests
# ============================================================================

class TestFullAssessment:
    def test_basic_assessment(self):
        result = full_conversion_assessment("morphine_po", 15, 4, "oxycodone_po")
        assert "mme_calculation" in result
        assert "conversion" in result
        assert "taper_schedule_preview" in result
        assert "safety_alerts" in result

    def test_disclaimer_present(self):
        result = full_conversion_assessment("morphine_po", 15, 4, "oxycodone_po")
        assert "disclaimer" in result


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLI:
    def test_mme_command(self):
        ret = main(["mme", "--opioid", "morphine_po", "--dose", "15", "--times", "4"])
        assert ret == 0

    def test_convert_command(self):
        ret = main(["convert", "--from", "morphine_po", "--from-dose", "15",
                     "--from-times", "4", "--to", "oxycodone_po"])
        assert ret == 0

    def test_methadone_command(self):
        ret = main(["methadone", "--mme", "200"])
        assert ret == 0

    def test_fentanyl_patch_command(self):
        ret = main(["fentanyl-patch", "--mme", "120"])
        assert ret == 0

    def test_taper_command(self):
        ret = main(["taper", "--mme", "100"])
        assert ret == 0

    def test_list_command(self):
        ret = main(["list"])
        assert ret == 0

    def test_assess_command(self):
        ret = main(["assess", "--from", "morphine_po", "--from-dose", "15",
                     "--from-times", "4", "--to", "oxycodone_po"])
        assert ret == 0
