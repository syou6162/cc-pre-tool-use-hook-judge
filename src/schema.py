"""JSON schema validation for PreToolUse hook inputs and outputs."""

import json
from typing import Any

import jsonschema
from jsonschema import ValidationError

# PreToolUse hook input schema
# Based on: https://docs.claude.com/en/docs/claude-code/hooks#pretooluse-decision-control
PRETOOLUSE_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "session_id",
        "transcript_path",
        "cwd",
        "permission_mode",
        "hook_event_name",
        "tool_name",
        "tool_input"
    ],
    "properties": {
        "session_id": {"type": "string"},
        "transcript_path": {"type": "string"},
        "cwd": {"type": "string"},
        "permission_mode": {
            "type": "string",
            "enum": ["default", "plan", "acceptEdits", "bypassPermissions"]
        },
        "hook_event_name": {
            "type": "string",
            "const": "PreToolUse"
        },
        "tool_name": {"type": "string"},
        "tool_input": {"type": "object"}
    },
    "additionalProperties": True
}


def validate_pretooluse_input(json_string: str) -> dict[str, Any]:
    """Validate PreToolUse hook input JSON using JSON Schema.

    Args:
        json_string: JSON string to validate

    Returns:
        Parsed and validated input data as dictionary

    Raises:
        json.JSONDecodeError: If json_string is not valid JSON
        ValueError: If required fields are missing or invalid
    """
    # Parse JSON
    data = json.loads(json_string)

    # Validate using JSON Schema
    try:
        jsonschema.validate(instance=data, schema=PRETOOLUSE_INPUT_SCHEMA)
    except ValidationError as e:
        # Convert jsonschema.ValidationError to ValueError for consistency
        raise ValueError(str(e.message)) from e

    return data
