import logging
import re
from typing import List
from .base import BaseExtractor, RawRecord

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)

class ResumeExtractor(BaseExtractor):
    def extract(self, file_path: str) -> List[RawRecord]:
        text = self._extract_text(file_path)
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return []

        raw_data = {
            "full_text": text,
            "parsed_sections": self._heuristically_parse_sections(text)
        }

        return [RawRecord(
            source_type="resume",
            source_identifier=file_path,
            raw_data=raw_data
        )]

    def _extract_text(self, file_path: str) -> str:
        text = ""
        try:
            if file_path.lower().endswith('.pdf'):
                if pdfplumber is None:
                    logger.error("pdfplumber is not installed.")
                    return ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
            elif file_path.lower().endswith('.docx'):
                if Document is None:
                    logger.error("python-docx is not installed.")
                    return ""
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
            else:
                logger.error(f"Unsupported resume format: {file_path}")
        except Exception as e:
            logger.error(f"Failed to read resume {file_path}: {e}")
            # Gracefully degrade to empty string
        return text.strip()

    def _heuristically_parse_sections(self, text: str) -> dict:
        """
        Light rule-based parser for sections (Experience/Education/Skills headers).
        """
        sections = {
            "experience": "",
            "education": "",
            "skills": "",
            "other": ""
        }
        
        # Very simple heuristic: look for lines that are exactly these words, or start with them.
        current_section = "other"
        
        for line in text.split('\n'):
            line_clean = line.strip().lower()
            if not line_clean:
                continue
                
            if re.match(r'^(work\s+)?experience(s)?$', line_clean):
                current_section = "experience"
                continue
            elif re.match(r'^education$', line_clean):
                current_section = "education"
                continue
            elif re.match(r'^skills( & technologies)?$', line_clean):
                current_section = "skills"
                continue
                
            sections[current_section] += line + "\n"
            
        return {k: v.strip() for k, v in sections.items() if v.strip()}
