from typing import Dict, Any, List
import logging
from .models import CanonicalProfile

logger = logging.getLogger(__name__)

class MissingValueError(Exception):
    pass

def _resolve_path(data: Any, path: str) -> Any:
    """
    Evaluates a simple path like 'emails[0]' or 'skills[].name' on a dictionary.
    """
    if not path:
        return data
        
    parts = path.replace(']', '').split('[')
    # For a path like skills[].name, we have parts: "skills", "", ".name"
    # Or "emails", "0"
    
    current = data
    path_segments = path.split('.')
    
    for segment in path_segments:
        if current is None:
            return None
            
        # Check for array indexing e.g. emails[0] or skills[]
        if '[' in segment and segment.endswith(']'):
            base = segment[:segment.index('[')]
            idx_str = segment[segment.index('[')+1:-1]
            
            if base:
                if isinstance(current, dict):
                    current = current.get(base)
                else:
                    current = getattr(current, base, None)
                    
            if current is None:
                return None
                
            if idx_str == '': # e.g. skills[]
                # We need to map the REST of the path over this array
                return current # Handled specially below if needed
            else:
                idx = int(idx_str)
                if isinstance(current, list) and len(current) > idx:
                    current = current[idx]
                else:
                    return None
        else:
            if isinstance(current, dict):
                current = current.get(segment)
            elif isinstance(current, list):
                # if current is a list and segment is a key, extract that key from all dicts
                current = [item.get(segment) if isinstance(item, dict) else getattr(item, segment, None) for item in current]
            else:
                current = getattr(current, segment, None)
                
    return current

def project(record: CanonicalProfile, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stateless projection function that emits a custom view based on config.
    """
    output = {}
    record_dict = record.model_dump()
    
    on_missing = config.get("on_missing", "null") # "null", "omit", "error"
    
    for field_conf in config.get("fields", []):
        out_path = field_conf.get("path")
        from_path = field_conf.get("from", out_path)
        
        value = _resolve_path(record_dict, from_path)
        
        if value is None or (isinstance(value, list) and len(value) == 0):
            if on_missing == "error":
                raise MissingValueError(f"Required field {from_path} is missing.")
            elif on_missing == "omit":
                continue
            elif on_missing == "null":
                output[out_path] = None
        else:
            output[out_path] = value
            
    if config.get("include_confidence", False):
        output["overall_confidence"] = record.overall_confidence
        
    if config.get("include_provenance", False):
        output["provenance"] = record_dict.get("provenance", [])
        
    return output
