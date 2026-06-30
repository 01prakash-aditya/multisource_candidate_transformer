from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import hashlib

class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = Field(None, description="ISO-3166 alpha-2 country code")

class Links(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = Field(default_factory=list)

class Skill(BaseModel):
    name: str = Field(description="Canonical skill name")
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)

class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = Field(None, description="Date as YYYY-MM")
    end: Optional[str] = Field(None, description="Date as YYYY-MM or 'Present'")
    summary: Optional[str] = None

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[str] = None

class Provenance(BaseModel):
    field: str
    source: str
    method: str = Field(description="Method used for extraction/normalization")

class CanonicalProfile(BaseModel):
    candidate_id: str
    full_name: str
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list, description="E.164 format")
    location: Optional[Location] = None
    links: Optional[Links] = None
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[Skill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    provenance: List[Provenance] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)

def generate_candidate_id(email: str = None, name: str = None, phone: str = None) -> str:
    """
    Generate a deterministic candidate ID based on available identity information.
    Prioritizes email. If missing, falls back to normalized name + phone.
    """
    hasher = hashlib.sha256()
    if email:
        hasher.update(email.strip().lower().encode('utf-8'))
    elif name and phone:
        normalized_str = f"{name.strip().lower()}|{phone.strip()}"
        hasher.update(normalized_str.encode('utf-8'))
    else:
        # Fallback if no strong identity keys are present (should be rare)
        import uuid
        return str(uuid.uuid4())
        
    return hasher.hexdigest()
