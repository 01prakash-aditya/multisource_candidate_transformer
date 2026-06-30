from typing import List, Dict
from collections import defaultdict
from .models import CanonicalProfile, Provenance, generate_candidate_id, Location, Skill
from .normalizers import normalize_phone, normalize_date, normalize_country, normalize_skill
from .confidence import calculate_confidence
from .extractors.base import RawRecord

# Priority table for conflict resolution (lower index = higher priority)
SOURCE_PRIORITY = ["ats_json", "resume", "github", "csv", "notes"]

def get_source_priority(source_type: str) -> int:
    try:
        return SOURCE_PRIORITY.index(source_type)
    except ValueError:
        return 999

class MergeEngine:
    def __init__(self):
        self.records_by_id = defaultdict(list)
    
    def add_records(self, records: List[RawRecord]):
        for record in records:
            # Identity Resolution
            email = record.raw_data.get("email")
            name = record.raw_data.get("full_name") or record.raw_data.get("name") or record.raw_data.get("first_name")
            phone = record.raw_data.get("phone")
            
            cand_id = generate_candidate_id(email=email, name=name, phone=phone)
            self.records_by_id[cand_id].append(record)
            
    def merge_all(self) -> List[CanonicalProfile]:
        profiles = []
        for cand_id, records in self.records_by_id.items():
            profiles.append(self._merge_candidate(cand_id, records))
        return profiles
        
    def _merge_candidate(self, cand_id: str, records: List[RawRecord]) -> CanonicalProfile:
        merged_data = {
            "candidate_id": cand_id,
            "emails": set(),
            "phones": set(),
            "skills_map": defaultdict(list), # skill_name -> list of sources
            "provenance": []
        }
        
        # We need to resolve scalar fields like full_name, headline using priority
        scalar_fields = {
            "full_name": {"value": None, "priority": 9999, "sources": []},
            "headline": {"value": None, "priority": 9999, "sources": []}
        }
        
        for record in records:
            src_type = record.source_type
            src_priority = get_source_priority(src_type)
            raw = record.raw_data
            
            # Emails
            if raw.get("email"):
                merged_data["emails"].add(raw["email"].strip().lower())
                merged_data["provenance"].append(Provenance(field="emails", source=src_type, method="exact_match"))
                
            # Phones
            if raw.get("phone"):
                norm_phone = normalize_phone(raw["phone"])
                if norm_phone:
                    merged_data["phones"].add(norm_phone)
                    merged_data["provenance"].append(Provenance(field="phones", source=src_type, method="phonenumbers_e164"))
            
            # Skills
            # From ATS/CSV
            if raw.get("skills"):
                # assume comma separated if string
                skills_raw = raw["skills"].split(',') if isinstance(raw["skills"], str) else raw["skills"]
                for s in skills_raw:
                    ns = normalize_skill(s)
                    if ns:
                        merged_data["skills_map"][ns].append(src_type)
            
            # From GitHub
            if raw.get("extracted_languages"):
                for lang in raw["extracted_languages"]:
                    ns = normalize_skill(lang)
                    if ns:
                        merged_data["skills_map"][ns].append(src_type)
                        
            # Scalar resolution (full_name, headline)
            name = raw.get("full_name") or raw.get("name") or raw.get("first_name")
            if name and src_priority < scalar_fields["full_name"]["priority"]:
                scalar_fields["full_name"]["value"] = name
                scalar_fields["full_name"]["priority"] = src_priority
                scalar_fields["full_name"]["sources"].append(src_type)
                
            headline = raw.get("headline") or raw.get("bio")
            if headline and src_priority < scalar_fields["headline"]["priority"]:
                scalar_fields["headline"]["value"] = headline
                scalar_fields["headline"]["priority"] = src_priority
                scalar_fields["headline"]["sources"].append(src_type)
                
        # Build final skills list
        final_skills = []
        for skill_name, sources in merged_data["skills_map"].items():
            conf = calculate_confidence(sources)
            final_skills.append(Skill(name=skill_name, confidence=conf, sources=list(set(sources))))
            
        # Overall confidence could be average of skill confidences or just a base score of the highest priority source
        source_types_present = list(set([r.source_type for r in records]))
        overall_conf = calculate_confidence(source_types_present)
            
        # Add scalar provenance
        if scalar_fields["full_name"]["value"]:
            merged_data["provenance"].append(Provenance(field="full_name", source=scalar_fields["full_name"]["sources"][-1], method="priority_merge"))
        if scalar_fields["headline"]["value"]:
            merged_data["provenance"].append(Provenance(field="headline", source=scalar_fields["headline"]["sources"][-1], method="priority_merge"))
            
        return CanonicalProfile(
            candidate_id=cand_id,
            full_name=scalar_fields["full_name"]["value"] or "Unknown",
            emails=list(merged_data["emails"]),
            phones=list(merged_data["phones"]),
            headline=scalar_fields["headline"]["value"],
            skills=final_skills,
            provenance=merged_data["provenance"],
            overall_confidence=overall_conf
        )
