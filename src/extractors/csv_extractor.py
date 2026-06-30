import csv
from typing import List, Any
import logging
from .base import BaseExtractor, RawRecord

logger = logging.getLogger(__name__)

class CSVExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[RawRecord]:
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Normalize headers: lower case, strip whitespace, replace spaces with underscores
                if reader.fieldnames:
                    reader.fieldnames = [
                        str(field).strip().lower().replace(" ", "_") if field else f"unnamed_{i}" 
                        for i, field in enumerate(reader.fieldnames)
                    ]
                
                for line_num, row in enumerate(reader, start=2):
                    # Basic tolerant parsing: Skip rows that are empty or have missing critical data
                    # Let's say if the row is entirely empty values, skip it
                    if not any(row.values()):
                        logger.warning(f"Skipping empty row {line_num} in {file_path}")
                        continue
                        
                    records.append(RawRecord(
                        source_type="csv",
                        source_identifier=file_path,
                        raw_data=dict(row)
                    ))
        except Exception as e:
            logger.error(f"Failed to process CSV {file_path}: {e}")
            # Graceful degradation, don't crash
        
        return records
