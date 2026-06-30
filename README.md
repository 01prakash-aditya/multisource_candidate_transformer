# Multi-Source Candidate Data Transformer

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project implements a robust ETL pipeline designed to ingest candidate data from multiple noisy, disjointed sources (CSV, ATS JSON, GitHub API, Resume PDFs/DOCXs), merge them intelligently, resolve conflicts, and project the canonical data into a custom, strictly validated JSON format.

<img width="1725" height="887" alt="image" src="https://github.com/user-attachments/assets/89f30f40-5134-4ef6-abd2-35d402f6e637" />

<img width="1767" height="547" alt="image" src="https://github.com/user-attachments/assets/e9af6661-ec03-401f-a686-3fa16f70465f" />


## Features

- **Source Extractors**: Adapters for CSV, custom JSON, GitHub REST API, and Resume documents (`.pdf`, `.docx`).
- **Data Normalization Layer**: Standardizes phone numbers to E.164 (`phonenumbers`), cleans dates to `YYYY-MM` (`dateparser`), standardizes country codes, and canonicalizes skill aliases.
- **Identity Resolution & Merge Engine**: Uses candidate emails (primary) or name+phone combinations to link records across sources.
- **Conflict Resolution**: Resolves scalar conflicts using a strict source-priority table (e.g., ATS > Resume > GitHub > CSV).
- **Confidence Scoring**: Dynamically calculates confidence based on source reliability, data staleness, and rewards data points that have consensus across multiple sources.
- **Config-Driven Projection**: Projects the unified `CanonicalProfile` into any required JSON schema at runtime using a JSON-path evaluator.
- **Schema Validation**: Dynamically builds a JSON schema (`jsonschema`) from the runtime config to ensure every output record perfectly complies before it is written.
- **Interfaces**: Includes both a robust CLI (`run.py`) and a Graphical Web UI (`app.py`).



## Installation

Ensure you have Python 3.12+ installed.

1. Activate your virtual environment (if you have one).
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage (CLI)

The CLI allows you to execute the entire end-to-end pipeline with a single command.

```bash
python run.py \
  --csv recruiter.csv \
  --json ats.json \
  --github usernames.txt \
  --resumes ./resumes/ \
  --config config.json \
  --out output.json
```

**Arguments:**
- `--csv`: Path to recruiter CSV file.
- `--json`: Path to ATS JSON blob file.
- `--github`: Path to a text file containing GitHub usernames (one per line).
- `--resumes`: Path to a directory containing resume `.pdf` or `.docx` files.
- `--config` **(Required)**: Path to runtime configuration JSON file.
- `--out` **(Required)**: Path to write the final output JSON file.

## Usage (Web UI)

For a simple graphical demonstration, you can launch the thin I/O surface powered by Gradio:

```bash
python app.py
```

This will launch a local web server (usually at `http://localhost:7860`). You can upload your raw source files and your `config.json` via the web interface and click **Transform & Merge** to instantly view the canonical JSON output.

## Runtime Configuration (`config.json`)

The pipeline relies on a `config.json` to determine the shape of the final output. Here is an example config:

```json
{
  "fields": [
    { "path": "name", "from": "full_name", "type": "string", "required": true },
    { "path": "primary_email", "from": "emails[0]", "type": "string" },
    { "path": "top_skill", "from": "skills[0].name", "type": "string" }
  ],
  "include_confidence": true,
  "on_missing": "null"
}
```

- **`on_missing`**: Can be set to `"null"`, `"omit"`, or `"error"`.

## Testing

You can run the comprehensive test suites using `pytest`:

```bash
pytest tests/
```
