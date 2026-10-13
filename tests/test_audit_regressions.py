"""Security, validation, and batch parsing regression tests."""
import pytest

from agents.base import AuditTrail
from opioid_conversion_rotation_agent.cli import parse_csv_boolean


def test_hmac_verification_detects_changed_signature():
    audit = AuditTrail("this-is-a-test-key-32-characters")
    audit.log("tester", "supervisor", "EVENT", {"case_id": "CASE-1"})
    assert audit.verify_integrity()
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_hmac_verification_detects_metadata_change():
    audit = AuditTrail("this-is-a-test-key-32-characters")
    audit.log("tester", "supervisor", "EVENT", {"case_id": "CASE-1"})
    audit.logs[0]["actor"] = "intruder"
    assert not audit.verify_integrity()


def test_audit_snapshot_is_not_mutable_state():
    audit = AuditTrail("this-is-a-test-key-32-characters")
    audit.log("tester", "supervisor", "EVENT", {"case_id": "CASE-1"})
    snapshot = audit.get_trail()
    snapshot[0]["current_hash"] = "0" * 64
    snapshot.append({})
    assert audit.verify_integrity()
    assert len(audit.get_trail()) == 1


@pytest.mark.parametrize("raw,expected", [
    ("true", True), ("yes", True), ("1", True), ("TRUE", True),
    ("false", False), ("no", False), ("0", False), ("False", False),
    ("", False), (None, False), (True, True), (False, False),
])
def test_csv_boolean_parsing(raw, expected):
    assert parse_csv_boolean(raw) is expected


def test_csv_boolean_unknown_value_rejected():
    with pytest.raises(ValueError):
        parse_csv_boolean("maybe")


def test_numeric_audits_reject_non_finite_metrics():
    from opioid_conversion_rotation_agent.models import ClinicalCasePayload
    from opioid_conversion_rotation_agent.agents import OpioidRotateCoordinator
    from agents.models import SystemTaskPayload
    from pydantic import ValidationError

    case = ClinicalCasePayload(
        case_id="DEMO-1", patient_synthetic_id="SYN-1",
        primary_metric=float("nan"), secondary_metric=0.0, status_flag="NORMAL"
    )
    with pytest.raises(ValueError, match="finite"):
        OpioidRotateCoordinator().process_case(case)
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="DEMO-1", target_identifier="SYN-1",
                          primary_metric=float("inf"))
