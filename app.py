import gradio as gr
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_data(csv_file, json_file, github_text, resume_files, config_file):
    merger = MergeEngine()
    
    # Load config
    try:
        if config_file:
            with open(config_file.name, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            return "Error: Config file is required."
    except Exception as e:
        return f"Failed to load config: {e}"

    if csv_file:
        merger.add_records(CSVExtractor().extract(csv_file.name))
        
    if json_file:
        mapping = {
            "Contact": "email", "ContactEmail": "email",
            "CandidateName": "full_name", "Name": "full_name",
            "Telephone": "phone", "PhoneNumber": "phone",
            "Skills": "skills", "CurrentTitle": "headline"
        }
        merger.add_records(JSONExtractor(field_mapping=mapping).extract(json_file.name))
        
    if github_text:
        gh_ext = GitHubExtractor()
        for line in github_text.split('\n'):
            if line.strip():
                merger.add_records(gh_ext.extract(line.strip()))
                
    if resume_files:
        res_ext = ResumeExtractor()
        for resume in resume_files:
            merger.add_records(res_ext.extract(resume.name))
            
    profiles = merger.merge_all()
    
    output = []
    for profile in profiles:
        try:
            projected = project(profile, config)
            if validate_projection(projected, config):
                output.append(projected)
        except Exception as e:
            logger.error(f"Failed to project/validate: {e}")
            
    return json.dumps(output, indent=2)

with gr.Blocks(title="Eightfold Candidate Data Transformer") as demo:
    gr.Markdown("# Multi-Source Candidate Data Transformer")
    gr.Markdown("Upload your raw source files and a runtime configuration to see the unified, canonical JSON output.")
    
    with gr.Row():
        with gr.Column():
            csv_in = gr.File(label="Upload Recruiter CSV")
            json_in = gr.File(label="Upload ATS JSON")
            github_in = gr.Textbox(label="GitHub Usernames (one per line)", lines=3)
            resume_in = gr.File(label="Upload Resumes (PDF/DOCX)", file_count="multiple")
            config_in = gr.File(label="Upload Runtime Config (config.json)")
            submit_btn = gr.Button("Transform & Merge", variant="primary")
            
        with gr.Column():
            json_out = gr.Code(label="Final Canonical JSON Output", language="json", interactive=False)
            
    submit_btn.click(
        fn=process_data,
        inputs=[csv_in, json_in, github_in, resume_in, config_in],
        outputs=[json_out]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
