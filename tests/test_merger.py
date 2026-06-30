import pytest
from src.normalizers import normalize_phone, normalize_date, normalize_country, normalize_skill
from src.confidence import calculate_confidence
from src.merger import MergeEngine
from src.extractors.base import RawRecord

def test_normalizers():
    assert normalize_phone("+1 650 253 0000") == "+16502530000"
    assert normalize_phone("invalid phone") is None
    
    assert normalize_date("Oct 2021") == "2021-10"
    assert normalize_date("Present") == "Present"
    assert normalize_date("now") == "Present"
    assert normalize_date("invalid date xyz") is None
    
    assert normalize_country("United States") == "US"
    assert normalize_country("uk") == "GB"
    assert normalize_country("US") == "US"
    
    assert normalize_skill("React.js") == "React"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("unknown_skill") == "unknown_skill"

def test_confidence():
    # Only 1 source, no staleness -> base score
    assert calculate_confidence(["ats_json"]) == 0.9
    
    # 2 sources agreement -> base + bonus
    assert calculate_confidence(["ats_json", "github"]) == min(1.0, 0.9 + 0.15)
    
    # Stale penalty
    assert calculate_confidence(["csv"], is_stale=True) == 0.7 - 0.1

def test_merge_engine():
    records = [
        RawRecord(
            source_type="csv",
            source_identifier="data.csv",
            raw_data={
                "email": "test@example.com",
                "full_name": "John Doe",
                "phone": "650-253-0000",
                "skills": "ReactJS, Python"
            }
        ),
        RawRecord(
            source_type="github",
            source_identifier="github.com/jdoe",
            raw_data={
                "email": "test@example.com",
                "name": "Johnathon Doe", # Lower priority than CSV/ATS ? Actually github is higher than CSV
                "extracted_languages": ["Python", "Rust"]
            }
        )
    ]
    
    merger = MergeEngine()
    merger.add_records(records)
    
    profiles = merger.merge_all()
    assert len(profiles) == 1
    
    p = profiles[0]
    assert p.candidate_id is not None
    assert p.full_name == "Johnathon Doe" # GitHub (priority 2) beats CSV (priority 3)
    assert "+16502530000" in p.phones
    assert "test@example.com" in p.emails
    
    skill_names = [s.name for s in p.skills]
    assert "React" in skill_names
    assert "Python" in skill_names
    assert "Rust" in skill_names
    
    # Check provenance
    # Johnathon Doe from github
    name_prov = [prov for prov in p.provenance if prov.field == "full_name"]
    assert name_prov[0].source == "github"
    assert name_prov[0].method == "priority_merge"
