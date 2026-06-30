import pytest
import json
from src.models import CanonicalProfile, generate_candidate_id, Location

def test_generate_candidate_id():
    email = "test@example.com"
    # Same email should produce same hash
    id1 = generate_candidate_id(email=email)
    id2 = generate_candidate_id(email=email)
    assert id1 == id2
    
    # Different email should produce different hash
    id3 = generate_candidate_id(email="other@example.com")
    assert id1 != id3
    
    # Fallback to name and phone
    id4 = generate_candidate_id(name="John Doe", phone="+1234567890")
    id5 = generate_candidate_id(name="John Doe", phone="+1234567890")
    assert id4 == id5
    assert id4 != id1

def test_canonical_profile_schema_generation():
    # Pydantic v2 uses model_json_schema()
    schema = CanonicalProfile.model_json_schema()
    assert "title" in schema
    assert schema["title"] == "CanonicalProfile"
    assert "properties" in schema
    assert "candidate_id" in schema["properties"]
    assert "full_name" in schema["properties"]
    assert "emails" in schema["properties"]
    
def test_canonical_profile_instantiation():
    profile = CanonicalProfile(
        candidate_id=generate_candidate_id(email="test@example.com"),
        full_name="Test User",
        emails=["test@example.com"],
        phones=["+1234567890"],
        location=Location(country="US"),
        overall_confidence=0.9
    )
    assert profile.full_name == "Test User"
    assert profile.overall_confidence == 0.9
    assert profile.location.country == "US"
