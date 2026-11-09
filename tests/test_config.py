"""Tests for business config loading and validation."""

import json

import pytest

from voice_receptionist_agent.config import (
    business_profile_from_dict,
    load_business_profile,
    resolve_business_profile,
)
from voice_receptionist_agent.graph import handle_call
from voice_receptionist_agent.models import BusinessProfile, Intent, Route

EXAMPLE = {
    "name": "Bright Smile Dental Clinic",
    "services": ["checkup", "cleaning", "filling", "whitening"],
    "hours": "Monday to Saturday, 9am to 6pm",
    "price_note": "A checkup is 2,000 PKR and a cleaning is 3,500 PKR. Exact prices depend on the treatment.",
    "handoff_message": "I will connect you with a member of our team.",
    "phone": "+92 300 0000000",
}

SALON = {
    "name": "Sunrise Salon",
    "services": ["haircut", "colouring", "facial"],
    "hours": "Every day, 10am to 8pm",
    "price_note": "A haircut is 1,500 PKR and a facial is 3,000 PKR.",
    "handoff_message": "I will connect you with our front desk.",
    "phone": "+92 300 1111111",
}


def test_example_config_loads_and_matches_defaults(tmp_path):
    path = tmp_path / "business.json"
    path.write_text(json.dumps(EXAMPLE), encoding="utf-8")
    profile = load_business_profile(path)
    assert profile == BusinessProfile()


def test_repo_example_file_loads(tmp_path):
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    profile = load_business_profile(repo_root / "business.example.json")
    assert profile == BusinessProfile()


def test_missing_config_file_fails_with_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_business_profile(tmp_path / "missing.json")


def test_invalid_json_fails_with_clear_error(tmp_path):
    path = tmp_path / "business.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_business_profile(path)


def test_missing_field_fails_and_names_it():
    data = dict(EXAMPLE)
    del data["phone"]
    with pytest.raises(ValueError, match="phone"):
        business_profile_from_dict(data)


def test_unknown_field_fails_and_names_it():
    data = dict(EXAMPLE)
    data["phonee"] = "+92 300 0000000"
    with pytest.raises(ValueError, match="phonee"):
        business_profile_from_dict(data)


def test_wrong_type_fails_and_names_it():
    data = dict(EXAMPLE)
    data["services"] = "cleaning"
    with pytest.raises(ValueError, match="services"):
        business_profile_from_dict(data)


def test_empty_services_fails():
    data = dict(EXAMPLE)
    data["services"] = []
    with pytest.raises(ValueError, match="services"):
        business_profile_from_dict(data)


def test_duplicate_service_fails():
    data = dict(EXAMPLE)
    data["services"] = ["cleaning", "Cleaning"]
    with pytest.raises(ValueError, match="services"):
        business_profile_from_dict(data)


def test_non_object_config_fails():
    with pytest.raises(ValueError, match="JSON object"):
        business_profile_from_dict(["not", "an", "object"])


def test_resolve_without_config_uses_default_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_business_profile() == BusinessProfile()


def test_resolve_uses_local_business_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "business.json").write_text(json.dumps(SALON), encoding="utf-8")
    profile = resolve_business_profile()
    assert profile.name == "Sunrise Salon"


def test_different_business_changes_the_answers():
    business = business_profile_from_dict(SALON)
    result = handle_call(
        ["Hi, I want to book a haircut on Friday at 4pm"], business=business
    )
    assert result["intent"] == Intent.BOOKING
    assert result["route"] == Route.BOOK
    assert result["details"]["service"] == "haircut"
    assert "haircut" in result["reply"]
    assert "Sunrise Salon" in result["transcript"][0]["text"]


def test_different_business_changes_pricing_answer():
    business = business_profile_from_dict(SALON)
    result = handle_call(["How much is a facial?"], business=business)
    assert result["intent"] == Intent.PRICING
    assert result["details"]["service"] == "facial"
    assert "3,000" in result["reply"]
    assert "2,000" not in result["reply"]


def test_business_services_are_the_only_bookable_ones():
    business = business_profile_from_dict(SALON)
    result = handle_call(["I want to book a cleaning on Saturday"], business=business)
    assert result["details"].get("service") is None
    assert result["route"] == Route.CLARIFY
    assert "haircut" in result["reply"]
