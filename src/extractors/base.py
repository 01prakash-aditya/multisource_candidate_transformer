from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

class RawRecord(BaseModel):
    """
    Intermediate schema that all extractors output.
    Contains loosely typed raw data and the source metadata.
    """
    source_type: str
    source_identifier: str  # e.g., filename, github url, etc.
    raw_data: Dict[str, Any]

class BaseExtractor:
    """
    Base interface for all source extractors.
    """
    def extract(self, source_input: Any) -> List[RawRecord]:
        """
        Takes raw input (file path, url, string) and returns a list of RawRecords.
        """
        raise NotImplementedError("Subclasses must implement extract()")
