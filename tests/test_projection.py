import pytest
from src.models import CanonicalProfile, Location, Skill
from src.projection import project, MissingValueError
from src.validator import generate_schema_from_config, validate_projection

@pytest.fixture
def dummy_record():
    return CanonicalProfile(
        candidate_id="12345",
        full_name="John Doe",
        emails=["john@example.com"],
        phones=["+16502530000"],
        skills=[
            Skill(name="Python", confidence=0.9, sources=["github"]),
            Skill(name="React", confidence=0.8, sources=["csv"])
        ],
        overall_confidence=0.85
    )

def test_projection_logic(dummy_record):
    config = {
        "fields": [
            {"path": "name", "from": "full_name", "type": "string", "required": True},
            {"path": "primary_email", "from": "emails[0]", "type": "string"},
            {"path": "top_skill", "from": "skills[0].name", "type": "string"},
            {"path": "missing_field", "from": "headline", "type": "string"}
        ],
        "include_confidence": True,
        "on_missing": "null" # null, omit, error
    }
    
    output = project(dummy_record, config)
    
    assert output["name"] == "John Doe"
    assert output["primary_email"] == "john@example.com"
    assert output["top_skill"] == "Python"
    assert output["missing_field"] is None
    assert output["overall_confidence"] == 0.85

def test_projection_on_missing(dummy_record):
    config_omit = {
        "fields": [{"path": "missing_field", "from": "headline"}],
        "on_missing": "omit"
    }
    output_omit = project(dummy_record, config_omit)
    assert "missing_field" not in output_omit
    
    config_error = {
        "fields": [{"path": "missing_field", "from": "headline"}],
        "on_missing": "error"
    }
    with pytest.raises(MissingValueError):
        project(dummy_record, config_error)

def test_validation(dummy_record):
    config = {
        "fields": [
            {"path": "name", "from": "full_name", "type": "string", "required": True},
            {"path": "email", "from": "emails[0]", "type": "string"}
        ]
    }
    
    schema = generate_schema_from_config(config)
    assert "name" in schema["required"]
    
    projected = project(dummy_record, config)
    is_valid = validate_projection(projected, config)
    assert is_valid is True
    
    # Test invalid data manually
    invalid_data = {"email": "john@example.com"} # Missing required 'name'
    assert validate_projection(invalid_data, config) is False
