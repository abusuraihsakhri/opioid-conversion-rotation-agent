# Opioid Equianalgesic Conversion & Rotation Calculator

Real clinical calculator for opioid dose conversion, rotation, tapering, and Morphine Milligram Equivalent (MME) calculation.

## Clinical Background

Opioid rotation involves converting from one opioid to another to improve pain control or reduce side effects. Key principles:
- **Equianalgesic doses** provide approximately equal analgesia
- **Cross-tolerance reduction** (25-50%) accounts for incomplete cross-tolerance between opioids
- **Methadone conversion** is non-linear and requires specialist guidance
- **MME calculation** is used for overdose risk assessment

## Equianalgesic Table

All doses equivalent to **30mg oral morphine**:

| Opioid | Route | Equianalgesic Dose | MME Factor |
|--------|-------|-------------------|------------|
| Morphine | PO | 30 mg | 1.0 |
| Morphine | IV | 10 mg | 3.0 |
| Oxycodone | PO | 20 mg | 1.5 |
| Hydrocodone | PO | 30 mg | 1.0 |
| Hydromorphone | PO | 7.5 mg | 4.0 |
| Hydromorphone | IV | 1.5 mg | 20.0 |
| Fentanyl | IV | 100 mcg | 0.1/mcg |
| Fentanyl patch | TD | 25 mcg/hr | 2.4/mcg/hr/day |
| Codeine | PO | 200 mg | 0.15 |
| Tramadol | PO | 100 mg | 0.15 |
| Methadone | PO | 20 mg* | 3.0* |

*Methadone conversion varies significantly by total daily MME.

## MME Risk Stratification

| Daily MME | Risk Level | Action |
|-----------|-----------|--------|
| <50 | Low | Continue monitoring |
| 50-89 | Moderate | Consider naloxone co-prescribing |
| 90-199 | High | Careful justification, naloxone co-prescribe |
| ≥200 | Very High | Pain specialist referral, naloxone required |

## Installation

```bash
# No dependencies required - Python 3.8+ stdlib only
cd opioid-conversion-rotation-agent
```

## Usage

### Calculate MME
```bash
python cli.py mme --opioid morphine_po --dose 15 --times 4
python cli.py mme --opioid oxycodone_po --dose 10 --times 4
```

### Convert Between Opioids
```bash
python cli.py convert --from morphine_po --from-dose 15 --from-times 4 --to oxycodone_po
python cli.py convert --from oxycodone_po --from-dose 10 --from-times 4 --to hydromorphone_po --reduction 0.25
```

### Convert to Methadone
```bash
python cli.py methadone --mme 200
python cli.py methadone --mme 500 --reduction 0.50
```

### Convert to Fentanyl Patch
```bash
python cli.py fentanyl-patch --mme 120
```

### Generate Taper Schedule
```bash
python cli.py taper --mme 100
python cli.py taper --mme 200 --target 50 --reduction 10 --interval 7
```

### Full Assessment
```bash
python cli.py assess --from morphine_po --from-dose 15 --from-times 4 --to oxycodone_po
```

### List Available Opioids
```bash
python cli.py list
```

## Output Format

All commands output JSON. Example MME calculation:
```json
{
  "total_daily_mme": 60.0,
  "components": [
    {
      "opioid": "morphine_po",
      "dose_per_admin": "15.0 mg",
      "doses_per_day": 4,
      "daily_dose": "60.0 mg/day",
      "mme_factor": 1.0,
      "daily_mme": 60.0
    }
  ],
  "risk_level": "MODERATE",
  "risk_note": "MME >=50: Increased overdose risk. Consider naloxone co-prescribing."
}
```

## Tests

```bash
python -m pytest test_opioid_rotate.py -v
```

## Disclaimer

**FOR EDUCATIONAL AND RESEARCH USE ONLY.** Opioid management requires clinical expertise. Equianalgesic conversions are estimates and individual response varies significantly. Methadone conversions should only be performed by experienced clinicians.

## References

- Dowell D, et al. CDC Clinical Practice Guideline for Prescribing Opioids for Pain. *MMWR Recomm Rep*. 2022;71(3):1-95.
- Pereira J, et al. Opioid conversion ratios for palliative care. *J Palliat Med*. 2001;4(2):231-247.
- Fine PG, Portenoy RK. Opioid rotation: the science and the practice. *Pain Clinical Updates*. 2006;12(3):1-8.

## License

MIT License. See [LICENSE](LICENSE) for details.
