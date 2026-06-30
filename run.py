import argparse
import json
import logging
import os
from src.extractors.csv_extractor import CSVExtractor
from src.extractors.json_extractor import JSONExtractor
from src.extractors.github_extractor import GitHubExtractor
from src.extractors.resume_extractor import ResumeExtractor
from src.merger import MergeEngine
from src.projection import project
from src.validator import validate_projection

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", help="Path to recruiter CSV file")
    parser.add_argument("--json", help="Path to ATS JSON blob file")
    parser.add_argument("--github", help="Path to text file containing GitHub usernames/URLs (one per line)")
    parser.add_argument("--resumes", help="Path to a directory containing resume PDFs/DOCXs")
    parser.add_argument("--config", required=True, help="Path to runtime configuration JSON")
    parser.add_argument("--out", required=True, help="Path to write the final output JSON")
    
    args = parser.parse_args()
    
    # Load config
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    merger = MergeEngine()
    
    # Extract CSV
    if args.csv:
        logger.info(f"Extracting from CSV: {args.csv}")
        extractor = CSVExtractor()
        merger.add_records(extractor.extract(args.csv))
        
    # Extract JSON
    if args.json:
        logger.info(f"Extracting from JSON: {args.json}")
        # Assuming a basic mapping for demonstration
        mapping = {
            "Contact": "email",
            "ContactEmail": "email",
            "CandidateName": "full_name",
            "Name": "full_name",
            "Telephone": "phone",
            "PhoneNumber": "phone",
            "Skills": "skills",
            "CurrentTitle": "headline"
        }
        extractor = JSONExtractor(field_mapping=mapping)
        merger.add_records(extractor.extract(args.json))
        
    # Extract GitHub
    if args.github:
        logger.info(f"Extracting from GitHub usernames list: {args.github}")
        extractor = GitHubExtractor()
        try:
            with open(args.github, 'r', encoding='utf-8') as f:
                for line in f:
                    username = line.strip()
                    if username:
                        merger.add_records(extractor.extract(username))
        except Exception as e:
            logger.error(f"Failed to read GitHub list: {e}")
            
    # Extract Resumes
    if args.resumes:
        logger.info(f"Extracting from Resumes directory: {args.resumes}")
        extractor = ResumeExtractor()
        if os.path.isdir(args.resumes):
            for filename in os.listdir(args.resumes):
                if filename.lower().endswith(('.pdf', '.docx')):
                    file_path = os.path.join(args.resumes, filename)
                    merger.add_records(extractor.extract(file_path))
        else:
            logger.warning(f"Resumes path {args.resumes} is not a directory.")
            
    # Merge
    logger.info("Merging records and resolving conflicts...")
    canonical_profiles = merger.merge_all()
    logger.info(f"Generated {len(canonical_profiles)} canonical candidate profiles.")
    
    # Project & Validate
    logger.info("Projecting and validating against runtime config...")
    final_output = []
    
    for profile in canonical_profiles:
        try:
            projected = project(profile, config)
            if validate_projection(projected, config):
                final_output.append(projected)
        except Exception as e:
            logger.error(f"Failed to project/validate candidate {profile.candidate_id}: {e}")
            
    # Write output
    logger.info(f"Writing {len(final_output)} valid records to {args.out}")
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)
        
if __name__ == "__main__":
    main()
