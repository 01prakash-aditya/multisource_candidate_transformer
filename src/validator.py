import jsonschema
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def generate_schema_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically generates a JSON Schema based on the runtime projection config.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
    
    for field in config.get("fields", []):
        field_name = field.get("path")
        field_type = field.get("type", "string")
        
        # Simple mapping from config types to JSON schema types
        if field_type == "string[]":
            schema["properties"][field_name] = {
                "type": ["array", "null"],
                "items": {"type": "string"}
            }
        elif field_type == "number":
            schema["properties"][field_name] = {"type": ["number", "null"]}
        else: # Default to string
            schema["properties"][field_name] = {"type": ["string", "null"]}
            
        if field.get("required"):
            schema["required"].append(field_name)
            
    if config.get("include_confidence"):
        schema["properties"]["overall_confidence"] = {"type": "number"}
        
    if config.get("include_provenance"):
        schema["properties"]["provenance"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "source": {"type": "string"},
                    "method": {"type": "string"}
                }
            }
        }
        
    return schema

def validate_projection(projected_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Validates a single projected record against the config's derived schema.
    Returns True if valid, False otherwise. Does not crash on failure.
    """
    schema = generate_schema_from_config(config)
    try:
        jsonschema.validate(instance=projected_data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation failed for candidate: {e.message}")
        return False
