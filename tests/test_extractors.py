import pytest
import os
import json
import csv
from unittest.mock import patch, MagicMock

from src.extractors.csv_extractor import CSVExtractor
from src.extractors.json_extractor import JSONExtractor
from src.extractors.github_extractor import GitHubExtractor
from src.extractors.resume_extractor import ResumeExtractor

def test_csv_extractor(tmp_path):
    # Setup test file
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.csv"
    with open(p, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["First Name ", "Email "])
        writer.writerow(["John Doe", "john@example.com"])
        writer.writerow(["", ""]) # Should be skipped
    
    extractor = CSVExtractor()
    records = extractor.extract(str(p))
    
    assert len(records) == 1
    assert records[0].source_type == "csv"
    assert records[0].raw_data["first_name"] == "John Doe"
    assert records[0].raw_data["email"] == "john@example.com"

def test_json_extractor(tmp_path):
    # Setup test file
    d = tmp_path / "sub2"
    d.mkdir()
    p = d / "ats.json"
    data = [
        {"FirstName": "Jane", "LastName": "Doe", "Contact": "jane@example.com"}
    ]
    with open(p, "w") as f:
        json.dump(data, f)
        
    mapping = {
        "FirstName": "first_name",
        "LastName": "last_name",
        "Contact": "email"
    }
    extractor = JSONExtractor(field_mapping=mapping)
    records = extractor.extract(str(p))
    
    assert len(records) == 1
    assert records[0].source_type == "ats_json"
    assert records[0].raw_data["first_name"] == "Jane"
    assert records[0].raw_data["email"] == "jane@example.com"

@patch('requests.get')
def test_github_extractor(mock_get):
    # Mock responses
    mock_profile_resp = MagicMock()
    mock_profile_resp.status_code = 200
    mock_profile_resp.json.return_value = {"name": "Octocat", "bio": "A cat"}
    
    mock_repos_resp = MagicMock()
    mock_repos_resp.status_code = 200
    mock_repos_resp.json.return_value = [{"language": "Python"}, {"language": "Rust"}]
    
    mock_get.side_effect = [mock_profile_resp, mock_repos_resp]
    
    extractor = GitHubExtractor()
    records = extractor.extract("https://github.com/octocat")
    
    assert len(records) == 1
    assert records[0].source_type == "github"
    assert records[0].raw_data["username"] == "octocat"
    assert records[0].raw_data["name"] == "Octocat"
    assert set(records[0].raw_data["extracted_languages"]) == {"Python", "Rust"}

def test_resume_extractor_parsing():
    extractor = ResumeExtractor()
    
    dummy_text = """
    John Doe
    
    EXPERIENCE
    Software Engineer at Tech Corp
    
    EDUCATION
    BS Computer Science
    
    SKILLS
    Python, Java
    """
    
    # Mock the _extract_text method
    extractor._extract_text = MagicMock(return_value=dummy_text)
    
    records = extractor.extract("dummy.pdf")
    
    assert len(records) == 1
    sections = records[0].raw_data["parsed_sections"]
    assert "Software Engineer at Tech Corp" in sections["experience"]
    assert "BS Computer Science" in sections["education"]
    assert "Python, Java" in sections["skills"]
    assert "John Doe" in sections["other"]
