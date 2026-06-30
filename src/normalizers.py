import re
import json
import os
import phonenumbers
import dateparser
import logging

logger = logging.getLogger(__name__)

# Very basic lookup for countries, ideally this would be a larger comprehensive map
COUNTRY_MAP = {
    "united states": "US",
    "usa": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "india": "IN",
    "canada": "CA"
}

SKILL_ALIASES = {
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "python3": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java8": "Java",
    "c++": "C++",
    "cpp": "C++",
    "golang": "Go"
}

def normalize_phone(phone_str: str, default_region: str = "US") -> str:
    if not phone_str:
        return None
    try:
        parsed = phonenumbers.parse(phone_str, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return None

def normalize_date(date_str: str) -> str:
    if not date_str:
        return None
        
    date_str_clean = date_str.strip().lower()
    if date_str_clean in ['present', 'current', 'now']:
        return "Present"
        
    try:
        # dateparser is good for things like "Oct 2021"
        parsed = dateparser.parse(date_str)
        if parsed:
            return parsed.strftime("%Y-%m")
    except Exception:
        pass
    return None

def normalize_country(country_str: str) -> str:
    if not country_str:
        return None
    cleaned = country_str.strip().lower()
    
    if cleaned in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned]
        
    # If already a 2-letter code, just uppercase it
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned.upper()
    return None

def normalize_skill(skill_str: str) -> str:
    if not skill_str:
        return None
    cleaned = skill_str.strip().lower()
    return SKILL_ALIASES.get(cleaned, skill_str.strip())
