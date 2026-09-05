#!/usr/bin/env python3
"""
Opioid Equianalgesic Conversion & Rotation Calculator

Real clinical calculations for opioid dose conversion, rotation, tapering,
and morphine milligram equivalent (MME) calculation.

Equianalgesic table (oral morphine equivalents):
- Morphine PO 30mg = Morphine IV 10mg = Fentanyl IV 100mcg
- Fentanyl patch 25mcg/hr ≈ Morphine PO 60mg/day
- Hydromorphone PO 7.5mg = Hydromorphone IV 1.5mg = Morphine PO 30mg
- Oxycodone PO 20mg = Morphine PO 30mg
- Hydrocodone PO 30mg = Morphine PO 30mg
- Codeine PO 200mg = Morphine PO 30mg
- Tramadol PO 100mg = Morphine PO 15-20mg
- Methadone: Complex (varies by total daily MME)

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
# Equianalgesic Table
# ============================================================================

# All doses in mg (or mcg for fentanyl) equianalgesic to 30mg oral morphine
EQUIANALGESIC_TABLE = {
    "morphine_po": {
        "dose": 30.0,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 1.0,  # MME per mg
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 3.5
    },
    "morphine_iv": {
        "dose": 10.0,
        "unit": "mg",
        "route": "iv",
        "mme_factor": 3.0,  # 1mg IV = 3mg PO MME
        "onset_minutes": 5,
        "duration_hours": 4,
        "half_life_hours": 3.5
    },
    "morphine_sq": {
        "dose": 10.0,
        "unit": "mg",
        "route": "subcutaneous",
        "mme_factor": 3.0,
        "onset_minutes": 15,
        "duration_hours": 4,
        "half_life_hours": 3.5
    },
    "fentanyl_iv": {
        "dose": 100.0,
        "unit": "mcg",
        "route": "iv",
        "mme_factor": 0.1,  # 1mcg IV ≈ 0.1mg PO morphine equivalent
        "onset_minutes": 1,
        "duration_hours": 1,
        "half_life_hours": 3.0
    },
    "fentanyl_patch": {
        "dose": 25.0,
        "unit": "mcg/hr",
        "route": "transdermal",
        "mme_factor": 2.4,  # 1mcg/hr patch ≈ 2.4mg/hr PO morphine... simplified
        "onset_minutes": 720,  # 12 hours to full effect
        "duration_hours": 72,
        "half_life_hours": 17.0,
        "mme_per_mcg_hr_per_day": 2.4  # 1 mcg/hr = 2.4 MME/day (approximate)
    },
    "hydromorphone_po": {
        "dose": 7.5,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 4.0,  # 1mg PO = 4mg PO morphine equivalent
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 2.5
    },
    "hydromorphone_iv": {
        "dose": 1.5,
        "unit": "mg",
        "route": "iv",
        "mme_factor": 20.0,  # 1mg IV = 20mg PO morphine equivalent
        "onset_minutes": 5,
        "duration_hours": 4,
        "half_life_hours": 2.5
    },
    "oxycodone_po": {
        "dose": 20.0,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 1.5,  # 1mg PO = 1.5mg PO morphine equivalent
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 3.5
    },
    "hydrocodone_po": {
        "dose": 30.0,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 1.0,  # 1mg PO = 1mg PO morphine equivalent
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 4.0
    },
    "codeine_po": {
        "dose": 200.0,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 0.15,  # 1mg PO = 0.15mg PO morphine equivalent
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 3.0
    },
    "tramadol_po": {
        "dose": 100.0,
        "unit": "mg",
        "route": "oral",
        "mme_factor": 0.15,  # 1mg PO ≈ 0.1-0.2mg PO morphine equivalent
        "onset_minutes": 60,
        "duration_hours": 6,
        "half_life_hours": 6.0
    },
    "methadone_po": {
        "dose": 20.0,  # Variable - depends on total MME
        "unit": "mg",
        "route": "oral",
        "mme_factor": 3.0,  # Highly variable
        "onset_minutes": 30,
        "duration_hours": 8,
        "half_life_hours": 24.0,
        "note": "Methadone conversion is complex and varies with total daily MME"
    },
    "morphine_rectal": {
        "dose": 20.0,
        "unit": "mg",
        "route": "rectal",
        "mme_factor": 1.5,
        "onset_minutes": 30,
        "duration_hours": 4,
        "half_life_hours": 3.5
    }
}

# Methadone conversion factors (complex, varies by total MME)
# Based on published equianalgesic ratios
METHADONE_CONVERSION_FACTORS = {
    # (min_mme, max_mme): ratio (morphine PO mg : methadone mg)
    (0, 100): 4,       # <100 MME: 4:1
    (100, 300): 8,     # 100-300 MME: 8:1
    (300, 600): 12,    # 300-600 MME: 12:1
    (600, 1000): 15,   # 600-1000 MME: 15:1
    (1000, float('inf')): 20  # >1000 MME: 20:1
}


# ============================================================================
# MME Calculation
# ============================================================================

def calculate_mme(opioid_doses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total daily Morphine Milligram Equivalents (MME).
    
    Args:
        opioid_doses: List of dicts with keys:
            - opioid: str (e.g., "morphine_po", "oxycodone_po")
            - dose_mg: float (dose per administration)
            - doses_per_day: int (number of administrations per day)
            OR
            - dose_mcg_per_hr: float (for fentanyl patch)
        
    Returns:
        Dictionary with MME calculation
    """
    if not opioid_doses:
        raise ValueError("Must provide at least one opioid dose")
    
    total_mme = 0.0
    components = []
    
    for entry in opioid_doses:
        opioid = entry.get("opioid", "").lower().strip()
        
        if opioid not in EQUIANALGESIC_TABLE:
            raise ValueError(f"Unknown opioid: {opioid}. Available: {list(EQUIANALGESIC_TABLE.keys())}")
        
        info = EQUIANALGESIC_TABLE[opioid]
        
        # Handle fentanyl patch specially
        if opioid == "fentanyl_patch":
            mcg_per_hr = entry.get("dose_mcg_per_hr", 0)
            if mcg_per_hr <= 0:
                raise ValueError("Fentanyl patch dose must be positive")
            mme = mcg_per_hr * info.get("mme_per_mcg_hr_per_day", 2.4)
            components.append({
                "opioid": opioid,
                "dose": f"{mcg_per_hr} mcg/hr",
                "daily_mme": round(mme, 1),
                "calculation": f"{mcg_per_hr} mcg/hr * {info['mme_per_mcg_hr_per_day']} MME/mcg/hr/day"
            })
        else:
            dose_mg = entry.get("dose_mg", 0)
            doses_per_day = entry.get("doses_per_day", 1)

            if not isinstance(dose_mg, (int, float)) or not isinstance(doses_per_day, (int, float)):
                raise ValueError(f"Dose and doses_per_day for {opioid} must be numeric")

            if dose_mg <= 0:
                raise ValueError(f"Dose for {opioid} must be positive")
            if doses_per_day <= 0:
                raise ValueError(f"Doses per day for {opioid} must be positive")
            if doses_per_day > 100:
                raise ValueError(f"Doses per day for {opioid} exceeds maximum (100)")

            daily_dose = dose_mg * doses_per_day
            mme = daily_dose * info["mme_factor"]
            
            components.append({
                "opioid": opioid,
                "dose_per_admin": f"{dose_mg} {info['unit']}",
                "doses_per_day": doses_per_day,
                "daily_dose": f"{daily_dose} {info['unit']}/day",
                "mme_factor": info["mme_factor"],
                "daily_mme": round(mme, 1),
                "calculation": f"{daily_dose} {info['unit']} * {info['mme_factor']} = {round(mme, 1)} MME"
            })
        
        total_mme += mme
    
    # Risk stratification
    if total_mme >= 200:
        risk = "VERY_HIGH"
        risk_note = "MME >=200: Very high overdose risk. Strongly consider naloxone co-prescribing and pain specialist referral."
    elif total_mme >= 90:
        risk = "HIGH"
        risk_note = "MME >=90: High overdose risk. CDC recommends careful justification and naloxone co-prescribing."
    elif total_mme >= 50:
        risk = "MODERATE"
        risk_note = "MME >=50: Increased overdose risk. Consider naloxone co-prescribing."
    else:
        risk = "LOW"
        risk_note = "MME <50: Lower risk. Continue monitoring."
    
    return {
        "total_daily_mme": round(total_mme, 1),
        "components": components,
        "risk_level": risk,
        "risk_note": risk_note,
        "num_opioids": len(opioid_doses),
        "polypharmacy_warning": len(opioid_doses) > 1
    }


# ============================================================================
# Opioid Conversion
# ============================================================================

def convert_opioid(
    source_opioid: str,
    source_dose_mg: float,
    source_doses_per_day: int,
    target_opioid: str,
    cross_tolerance_reduction: float = 0.25,
    doses_per_day_target: int = 4
) -> Dict[str, Any]:
    """
    Convert from one opioid to another with equianalgesic dosing.
    
    Args:
        source_opioid: Source opioid name (e.g., "morphine_po")
        source_dose_mg: Source dose per administration in mg
        source_doses_per_day: Number of source doses per day
        target_opioid: Target opioid name
        cross_tolerance_reduction: Reduction for incomplete cross-tolerance (0.25-0.50)
        doses_per_day_target: Target number of doses per day
        
    Returns:
        Dictionary with conversion details
    """
    source_key = source_opioid.lower().strip()
    target_key = target_opioid.lower().strip()
    
    if source_key not in EQUIANALGESIC_TABLE:
        raise ValueError(f"Unknown source opioid: {source_opioid}")
    if target_key not in EQUIANALGESIC_TABLE:
        raise ValueError(f"Unknown target opioid: {target_opioid}")
    if not isinstance(source_dose_mg, (int, float)) or source_dose_mg <= 0:
        raise ValueError("Source dose must be a positive number")
    if not isinstance(source_doses_per_day, int) or source_doses_per_day <= 0:
        raise ValueError("Source doses per day must be a positive integer")
    if cross_tolerance_reduction < 0 or cross_tolerance_reduction >= 1:
        raise ValueError("Cross-tolerance reduction must be between 0 and 1")
    if not isinstance(doses_per_day_target, int) or doses_per_day_target <= 0:
        raise ValueError("Target doses per day must be a positive integer")

    source_info = EQUIANALGESIC_TABLE[source_key]
    target_info = EQUIANALGESIC_TABLE[target_key]
    
    # Step 1: Calculate total daily source dose
    daily_source_dose = source_dose_mg * source_doses_per_day
    
    # Step 2: Convert to morphine PO equivalents (MME)
    daily_mme = daily_source_dose * source_info["mme_factor"]
    
    # Step 3: Convert MME to target opioid daily dose
    target_daily_dose = daily_mme / target_info["mme_factor"]
    
    # Step 4: Apply cross-tolerance reduction
    reduced_daily_dose = target_daily_dose * (1 - cross_tolerance_reduction)
    
    # Step 5: Calculate per-dose amount
    target_dose_per_admin = reduced_daily_dose / doses_per_day_target
    
    return {
        "source": {
            "opioid": source_opioid,
            "dose_per_admin_mg": source_dose_mg,
            "doses_per_day": source_doses_per_day,
            "daily_dose_mg": daily_source_dose,
            "daily_mme": round(daily_mme, 1)
        },
        "target": {
            "opioid": target_opioid,
            "equianalgesic_daily_dose_mg": round(target_daily_dose, 1),
            "reduced_daily_dose_mg": round(reduced_daily_dose, 1),
            "cross_tolerance_reduction_percent": cross_tolerance_reduction * 100,
            "dose_per_admin_mg": round(target_dose_per_admin, 1),
            "doses_per_day": doses_per_day_target
        },
        "safety_notes": [
            f"Cross-tolerance reduction: {cross_tolerance_reduction * 100:.0f}%",
            "Monitor for over-sedation and respiratory depression",
            "Consider patient-specific factors (age, renal/hepatic function, concurrent medications)",
            "Methadone conversions require specialist guidance"
        ],
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Opioid rotation requires clinical expertise."
    }


def convert_to_methadone(
    total_daily_mme: float,
    cross_tolerance_reduction: float = 0.50
) -> Dict[str, Any]:
    """
    Convert total daily MME to methadone dose.
    
    Methadone conversion is complex and non-linear.
    The ratio increases with higher MME doses.
    
    Args:
        total_daily_mme: Total daily morphine milligram equivalents
        cross_tolerance_reduction: Cross-tolerance reduction (default 50% for methadone)
        
    Returns:
        Dictionary with methadone conversion
    """
    if total_daily_mme <= 0:
        raise ValueError("Total MME must be positive")
    
    # Find appropriate conversion ratio
    ratio = 4  # Default
    for (min_mme, max_mme), r in METHADONE_CONVERSION_FACTORS.items():
        if min_mme <= total_daily_mme < max_mme:
            ratio = r
            break
    
    # Calculate methadone dose
    methadone_daily = total_daily_mme / ratio
    
    # Apply cross-tolerance reduction (more aggressive for methadone)
    reduced_dose = methadone_daily * (1 - cross_tolerance_reduction)
    
    # Split into 2-3 daily doses (methadone has long/variable half-life)
    dose_per_admin = reduced_dose / 3  # TID dosing initially
    
    return {
        "total_daily_mme": total_daily_mme,
        "conversion_ratio": f"{ratio}:1 (morphine:methadone)",
        "equianalgesic_methadone_daily_mg": round(methadone_daily, 1),
        "cross_tolerance_reduction_percent": cross_tolerance_reduction * 100,
        "reduced_daily_dose_mg": round(reduced_dose, 1),
        "dosing_schedule": {
            "dose_per_admin_mg": round(dose_per_admin, 1),
            "frequency": "TID (every 8 hours)",
            "note": "Start with TID dosing; may consolidate to BID or daily once stable"
        },
        "critical_warnings": [
            "Methadone has a LONG and VARIABLE half-life (15-60+ hours)",
            "Risk of delayed respiratory depression and accumulation",
            "QTc prolongation risk - obtain baseline ECG",
            "Must be initiated by or under supervision of experienced clinician",
            "Conversion ratios are estimates - individual response varies greatly",
            "Reassess in 5-7 days due to accumulation"
        ],
        "disclaimer": "METHADONE CONVERSION REQUIRES SPECIALIST GUIDANCE. High risk of fatal accumulation."
    }


# ============================================================================
# Tapering Schedule
# ============================================================================

def generate_taper_schedule(
    current_daily_mme: float,
    target_daily_mme: float = 0.0,
    reduction_percent: float = 10.0,
    interval_days: int = 7,
    min_step_mme: float = 5.0
) -> Dict[str, Any]:
    """
    Generate a gradual opioid tapering schedule.
    
    CDC recommends:
    - Reduce by 10% per month for patients on opioids >1 year
    - Reduce by 10% per week for patients on opioids <1 year
    - Slower tapers (5-10% monthly) for patients on high doses
    
    Args:
        current_daily_mme: Current total daily MME
        target_daily_mme: Target daily MME (0 for complete taper)
        reduction_percent: Percentage to reduce at each step
        interval_days: Days between reductions
        min_step_mme: Minimum reduction per step in MME
        
    Returns:
        Dictionary with tapering schedule
    """
    if current_daily_mme <= 0:
        raise ValueError("Current MME must be positive")
    if target_daily_mme < 0:
        raise ValueError("Target MME must be non-negative")
    if target_daily_mme >= current_daily_mme:
        raise ValueError("Target must be less than current for tapering")
    if reduction_percent <= 0 or reduction_percent >= 100:
        raise ValueError("Reduction percent must be between 0 and 100")
    
    steps = []
    current = current_daily_mme
    day = 0
    
    while current > target_daily_mme + min_step_mme:
        reduction = max(current * reduction_percent / 100, min_step_mme)
        new_dose = max(current - reduction, target_daily_mme)
        
        steps.append({
            "step": len(steps) + 1,
            "day": day,
            "mme": round(current, 1),
            "reduction_mme": round(current - new_dose, 1),
            "percent_of_original": round((current / current_daily_mme) * 100, 1)
        })
        
        current = new_dose
        day += interval_days
    
    # Add final target
    steps.append({
        "step": len(steps) + 1,
        "day": day,
        "mme": round(target_daily_mme, 1),
        "reduction_mme": 0,
        "percent_of_original": round((target_daily_mme / current_daily_mme) * 100, 1) if current_daily_mme > 0 else 0
    })
    
    # Taper speed assessment
    if reduction_percent <= 10 and interval_days >= 28:
        speed = "SLOW (recommended for long-term use)"
    elif reduction_percent <= 10 and interval_days >= 7:
        speed = "MODERATE"
    else:
        speed = "FAST (higher withdrawal risk)"
    
    return {
        "current_daily_mme": current_daily_mme,
        "target_daily_mme": target_daily_mme,
        "reduction_percent_per_step": reduction_percent,
        "interval_days": interval_days,
        "total_steps": len(steps),
        "total_taper_days": day,
        "taper_speed": speed,
        "schedule": steps,
        "monitoring_notes": [
            "Monitor for withdrawal symptoms: anxiety, insomnia, diaphoresis, pain exacerbation",
            "Reassess pain and function at each step",
            "Consider adjunctive non-opioid therapies",
            "Slow taper if withdrawal symptoms occur"
        ]
    }


# ============================================================================
# Fentanyl Patch Conversion
# ============================================================================

def convert_to_fentanyl_patch(
    total_daily_mme: float,
    cross_tolerance_reduction: float = 0.25
) -> Dict[str, Any]:
    """
    Convert total daily MME to fentanyl transdermal patch dose.
    
    Approximate: 1 mcg/hr fentanyl patch ≈ 2.4 MME/day
    (varies by source, 2.0-3.0 range)
    
    Args:
        total_daily_mme: Total daily morphine milligram equivalents
        cross_tolerance_reduction: Cross-tolerance reduction
        
    Returns:
        Dictionary with fentanyl patch conversion
    """
    if total_daily_mme <= 0:
        raise ValueError("Total MME must be positive")
    
    # Convert MME to mcg/hr
    # 1 mcg/hr ≈ 2.4 MME/day
    mcg_per_hr = total_daily_mme / 2.4
    
    # Apply cross-tolerance reduction
    reduced_mcg_per_hr = mcg_per_hr * (1 - cross_tolerance_reduction)
    
    # Round to available patch sizes (12, 25, 50, 75, 100 mcg/hr)
    available_sizes = [12, 25, 50, 75, 100]
    rounded_mcg = min(available_sizes, key=lambda x: abs(x - reduced_mcg_per_hr))
    
    return {
        "total_daily_mme": total_daily_mme,
        "equianalgesic_mcg_per_hr": round(mcg_per_hr, 1),
        "cross_tolerance_reduction_percent": cross_tolerance_reduction * 100,
        "reduced_mcg_per_hr": round(reduced_mcg_per_hr, 1),
        "recommended_patch_mcg_per_hr": rounded_mcg,
        "available_sizes": available_sizes,
        "application_notes": [
            "Apply to clean, dry, hairless skin on torso or upper arm",
            "Onset: 12-24 hours to full effect",
            "Change patch every 72 hours",
            "Do not cut patches",
            "Store unused patches at room temperature",
            "Dispose of used patches by folding and flushing"
        ],
        "warnings": [
            "Fentanyl patches are for opioid-tolerant patients only",
            "Not for acute or postoperative pain",
            "Heat exposure can increase absorption (fever, heating pads, hot baths)",
            "Risk of fatal respiratory depression if used in opioid-naive patients"
        ],
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Fentanyl patch conversion requires clinical expertise."
    }


# ============================================================================
# Full Assessment
# ============================================================================

def full_conversion_assessment(
    source_opioid: str,
    source_dose_mg: float,
    source_doses_per_day: int,
    target_opioid: str,
    cross_tolerance_reduction: float = 0.25,
    target_doses_per_day: int = 4
) -> Dict[str, Any]:
    """
    Complete opioid conversion assessment.
    
    Args:
        source_opioid: Source opioid name
        source_dose_mg: Source dose per administration
        source_doses_per_day: Source doses per day
        target_opioid: Target opioid name
        cross_tolerance_reduction: Cross-tolerance reduction (0.25-0.50)
        target_doses_per_day: Target doses per day
        
    Returns:
        Complete assessment dictionary
    """
    # Calculate MME
    mme_result = calculate_mme([{
        "opioid": source_opioid,
        "dose_mg": source_dose_mg,
        "doses_per_day": source_doses_per_day
    }])
    
    # Convert opioid
    conversion = convert_opioid(
        source_opioid, source_dose_mg, source_doses_per_day,
        target_opioid, cross_tolerance_reduction, target_doses_per_day
    )
    
    # Generate taper schedule from current MME
    taper = generate_taper_schedule(mme_result["total_daily_mme"])
    
    return {
        "mme_calculation": mme_result,
        "conversion": conversion,
        "taper_schedule_preview": {
            "total_steps": taper["total_steps"],
            "total_days": taper["total_taper_days"],
            "first_3_steps": taper["schedule"][:3]
        },
        "safety_alerts": _generate_safety_alerts(mme_result["total_daily_mme"]),
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Opioid management requires clinical expertise."
    }


def _generate_safety_alerts(total_mme: float) -> List[str]:
    """Generate safety alerts based on MME level."""
    alerts = []
    
    if total_mme >= 200:
        alerts.append("CRITICAL: MME >=200. Strongly consider pain specialist referral.")
        alerts.append("CRITICAL: Co-prescribe naloxone. Educate patient and family on overdose response.")
    elif total_mme >= 90:
        alerts.append("WARNING: MME >=90. CDC recommends careful justification of dose.")
        alerts.append("WARNING: Consider naloxone co-prescribing.")
    elif total_mme >= 50:
        alerts.append("CAUTION: MME >=50. Increased overdose risk.")
    
    alerts.append("Assess for sleep apnea and respiratory depression risk factors.")
    alerts.append("Avoid concurrent benzodiazepines, gabapentinoids, and other CNS depressants.")
    alerts.append("Monitor for signs of opioid use disorder.")
    
    return alerts


def main(argv=None):
    """CLI entry point for opioid conversion calculator."""
    parser = argparse.ArgumentParser(
        prog="opioid-convert",
        description="Opioid Equianalgesic Conversion & Rotation Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- MME command ---
    mme_parser = subparsers.add_parser("mme", help="Calculate total daily MME")
    mme_parser.add_argument("--opioid", required=True, help="Opioid name (e.g., morphine_po)")
    mme_parser.add_argument("--dose", type=float, required=True, help="Dose per administration mg")
    mme_parser.add_argument("--times", type=int, default=1, help="Doses per day")
    
    # --- Convert command ---
    conv_parser = subparsers.add_parser("convert", help="Convert between opioids")
    conv_parser.add_argument("--from", dest="source", required=True, help="Source opioid")
    conv_parser.add_argument("--from-dose", type=float, required=True, help="Source dose mg")
    conv_parser.add_argument("--from-times", type=int, required=True, help="Source doses/day")
    conv_parser.add_argument("--to", dest="target", required=True, help="Target opioid")
    conv_parser.add_argument("--reduction", type=float, default=0.25, help="Cross-tolerance reduction (0-1)")
    conv_parser.add_argument("--to-times", type=int, default=4, help="Target doses/day")
    
    # --- Methadone command ---
    meth_parser = subparsers.add_parser("methadone", help="Convert to methadone")
    meth_parser.add_argument("--mme", type=float, required=True, help="Total daily MME")
    meth_parser.add_argument("--reduction", type=float, default=0.50, help="Cross-tolerance reduction")
    
    # --- Fentanyl patch command ---
    fent_parser = subparsers.add_parser("fentanyl-patch", help="Convert to fentanyl patch")
    fent_parser.add_argument("--mme", type=float, required=True, help="Total daily MME")
    fent_parser.add_argument("--reduction", type=float, default=0.25, help="Cross-tolerance reduction")
    
    # --- Taper command ---
    taper_parser = subparsers.add_parser("taper", help="Generate taper schedule")
    taper_parser.add_argument("--mme", type=float, required=True, help="Current daily MME")
    taper_parser.add_argument("--target", type=float, default=0.0, help="Target MME (default 0)")
    taper_parser.add_argument("--reduction", type=float, default=10.0, help="Reduction %% per step")
    taper_parser.add_argument("--interval", type=int, default=7, help="Days between steps")
    
    # --- Assess command ---
    assess_parser = subparsers.add_parser("assess", help="Full conversion assessment")
    assess_parser.add_argument("--from", dest="source", required=True, help="Source opioid")
    assess_parser.add_argument("--from-dose", type=float, required=True, help="Source dose mg")
    assess_parser.add_argument("--from-times", type=int, required=True, help="Source doses/day")
    assess_parser.add_argument("--to", dest="target", required=True, help="Target opioid")
    assess_parser.add_argument("--reduction", type=float, default=0.25, help="Cross-tolerance reduction")
    
    # --- List command ---
    subparsers.add_parser("list", help="List available opioids")
    
    args = parser.parse_args(argv)
    
    if args.command == "mme":
        result = calculate_mme([{"opioid": args.opioid, "dose_mg": args.dose, "doses_per_day": args.times}])
        print(json.dumps(result, indent=2))
    
    elif args.command == "convert":
        result = convert_opioid(args.source, args.from_dose, args.from_times, args.target, args.reduction, args.to_times)
        print(json.dumps(result, indent=2))
    
    elif args.command == "methadone":
        result = convert_to_methadone(args.mme, args.reduction)
        print(json.dumps(result, indent=2))
    
    elif args.command == "fentanyl-patch":
        result = convert_to_fentanyl_patch(args.mme, args.reduction)
        print(json.dumps(result, indent=2))
    
    elif args.command == "taper":
        result = generate_taper_schedule(args.mme, args.target, args.reduction, args.interval)
        print(json.dumps(result, indent=2))
    
    elif args.command == "assess":
        result = full_conversion_assessment(args.source, args.from_dose, args.from_times, args.target, args.reduction)
        print(json.dumps(result, indent=2))
    
    elif args.command == "list":
        for name, info in EQUIANALGESIC_TABLE.items():
            print(f"  {name}: {info['dose']} {info['unit']} = 30mg morphine PO")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
