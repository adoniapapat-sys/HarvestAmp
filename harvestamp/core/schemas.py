# harvestamp/core/schemas.py
"""Schema validation utility for HarvestAmp.

Validates dict structures against YAML schema files.
"""
import os
import yaml
from typing import Any, Dict, List, Tuple

# Locate schemas directory
SCHEMAS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "schemas"))

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Loads a YAML schema file from the schemas folder."""
    filename = f"{schema_name}.schema.yaml"
    path = os.path.join(SCHEMAS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def validate_object(obj: Any, schema: Dict[str, Any], path: str = "root") -> Tuple[bool, List[str]]:
    """Validates a dictionary object against a schema definition.
    
    Returns (is_valid, error_messages).
    """
    errors = []
    
    if not isinstance(obj, dict):
        return False, [f"[{path}] Expected object, got {type(obj).__name__}"]
        
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in obj:
            errors.append(f"[{path}] Missing required field: '{field}'")
            
    # Check properties types
    properties = schema.get("properties", {})
    additional_properties = schema.get("additionalProperties")
    
    for field, val in obj.items():
        if field not in properties:
            if isinstance(additional_properties, dict):
                # Validate additional properties values
                sub_valid, sub_errors = validate_object(val, additional_properties, f"{path}.{field}")
                if not sub_valid:
                    errors.extend(sub_errors)
            continue
            
        prop_schema = properties[field]
        expected_type = prop_schema.get("type")
        
        # Helper to validate a single type choice
        def check_type(v: Any, t: str) -> bool:
            if t == "string":
                return isinstance(v, str)
            elif t == "number":
                return isinstance(v, (int, float)) and not isinstance(v, bool)
            elif t == "boolean":
                return isinstance(v, bool)
            elif t == "array":
                return isinstance(v, list)
            elif t == "object":
                return isinstance(v, dict)
            elif t == "null":
                return v is None
            return True
            
        if isinstance(expected_type, list):
            type_ok = any(check_type(val, t) for t in expected_type)
            if not type_ok:
                errors.append(f"[{path}.{field}] Expected one of {expected_type}, got {type(val).__name__}")
        else:
            if expected_type == "string":
                if not isinstance(val, str):
                    errors.append(f"[{path}.{field}] Expected string, got {type(val).__name__}")
            elif expected_type == "number":
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    errors.append(f"[{path}.{field}] Expected number, got {type(val).__name__}")
            elif expected_type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"[{path}.{field}] Expected boolean, got {type(val).__name__}")
            elif expected_type == "array":
                if not isinstance(val, list):
                    errors.append(f"[{path}.{field}] Expected array, got {type(val).__name__}")
                else:
                    items_schema = prop_schema.get("items", {})
                    item_type = items_schema.get("type")
                    for i, item in enumerate(val):
                        if item_type == "string" and not isinstance(item, str):
                            errors.append(f"[{path}.{field}[{i}]] Expected string, got {type(item).__name__}")
                        elif item_type == "number" and (not isinstance(item, (int, float)) or isinstance(item, bool)):
                            errors.append(f"[{path}.{field}[{i}]] Expected number, got {type(item).__name__}")
                        elif item_type == "object" and not isinstance(item, dict):
                            errors.append(f"[{path}.{field}[{i}]] Expected object, got {type(item).__name__}")
                        elif item_type == "object" and isinstance(item, dict):
                            sub_valid, sub_errors = validate_object(item, items_schema, f"{path}.{field}[{i}]")
                            if not sub_valid:
                                errors.extend(sub_errors)
            elif expected_type == "object":
                if not isinstance(val, dict):
                    errors.append(f"[{path}.{field}] Expected object, got {type(val).__name__}")
                else:
                    sub_valid, sub_errors = validate_object(val, prop_schema, f"{path}.{field}")
                    if not sub_valid:
                        errors.extend(sub_errors)
            
        # Check enum constraints if present
        if "enum" in prop_schema:
            if val not in prop_schema["enum"]:
                errors.append(f"[{path}.{field}] Value '{val}' is not one of allowed values: {prop_schema['enum']}")
                    
    return len(errors) == 0, errors

def validate_domain_rules(obj: Any, schema_name: str) -> Tuple[bool, List[str]]:
    """Enforces cross-field / domain constraints for HarvestAmp schemas."""
    errors = []
    if not isinstance(obj, dict):
        return True, []

    if schema_name == "harvest_event":
        marketable = obj.get("marketable_quantity", 0)
        cull = obj.get("cull_quantity", 0)
        harvested = obj.get("quantity_harvested", 0)
        if marketable + cull > harvested:
            errors.append(f"[{schema_name}] Marketable quantity ({marketable}) + cull quantity ({cull}) cannot exceed quantity harvested ({harvested})")
            
    elif schema_name == "yield_record":
        gross = obj.get("gross_quantity")
        adjusted = obj.get("adjusted_quantity")
        if gross is not None and adjusted is not None:
            if adjusted > gross:
                errors.append(f"[{schema_name}] Adjusted quantity ({adjusted}) cannot exceed gross quantity ({gross})")
                
    elif schema_name == "post_harvest_inventory":
        committed = obj.get("committed_quantity", 0)
        uncommitted = obj.get("uncommitted_quantity", 0)
        available = obj.get("quantity_available", 0)
        if committed + uncommitted > available:
            errors.append(f"[{schema_name}] Committed quantity ({committed}) + uncommitted quantity ({uncommitted}) cannot exceed quantity available ({available})")
            
    return len(errors) == 0, errors

def validate_by_name(obj: Any, schema_name: str) -> Tuple[bool, List[str]]:
    """Loads a schema by name and validates the object against it."""
    try:
        schema = load_schema(schema_name)
        valid, errors = validate_object(obj, schema, schema_name)
        if valid:
            domain_valid, domain_errors = validate_domain_rules(obj, schema_name)
            if not domain_valid:
                return False, domain_errors
        return valid, errors
    except Exception as e:
        return False, [f"Validation failed due to error loading schema: {e}"]

