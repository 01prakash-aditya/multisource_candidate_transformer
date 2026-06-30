import json
import logging
from typing import List, Dict, Any
from .base import BaseExtractor, RawRecord

logger = logging.getLogger(__name__)

class JSONExtractor(BaseExtractor):
    def __init__(self, field_mapping: Dict[str, str] = None):
        """
        Initialize with a field remapping table (ATS keys -> Canonical keys).
        """
        self.field_mapping = field_mapping or {}

    def extract(self, file_path: str) -> List[RawRecord]:
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Assume data is a list of candidate dictionaries. 
                # If it's a single dict, wrap it in a list.
                if isinstance(data, dict):
                    data = [data]
                    
                for idx, candidate in enumerate(data):
                    if not isinstance(candidate, dict):
                        logger.warning(f"Skipping non-dict candidate at index {idx} in {file_path}")
                        continue
                    
                    # Remap fields using the explicit mapping table
                    remapped_data = {}
                    for ats_key, value in candidate.items():
                        canonical_key = self.field_mapping.get(ats_key, ats_key)
                        remapped_data[canonical_key] = value
                        
                    records.append(RawRecord(
                        source_type="ats_json",
                        source_identifier=file_path,
                        raw_data=remapped_data
                    ))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading JSON {file_path}: {e}")
            
        return records
