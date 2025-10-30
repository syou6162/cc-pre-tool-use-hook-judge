"""JSON schema validation for PreToolUse hook inputs and outputs."""

from functools import partial
from typing import Any

import jsonschema
from jsonschema import ValidationError

# PreToolUse hook output schema
# Based on: https://docs.claude.com/en/docs/claude-code/hooks#pretooluse-decision-control
PRETOOLUSE_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["hookSpecificOutput"],
    "properties": {
        "hookSpecificOutput": {
            "type": "object",
            "required": [
                "hookEventName",
                "permissionDecision",
                "permissionDecisionReason"
            ],
            "properties": {
                "hookEventName": {
                    "type": "string",
                    "const": "PreToolUse"
                },
                "permissionDecision": {
                    "type": "string",
                    "enum": ["allow", "deny", "ask"]
                },
                "permissionDecisionReason": {
                    "type": "string"
                },
                "updatedInput": {
                    "type": "object"
                }
            },
            "additionalProperties": False
        },
        "continue": {
            "type": "boolean"
        },
        "stopReason": {
            "type": "string"
        },
        "suppressOutput": {
            "type": "boolean"
        },
        "systemMessage": {
            "type": "string"
        }
    },
    "additionalProperties": True
}

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


def _validate_with_schema(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate data against a JSON schema.

    Args:
        data: Dictionary to validate
        schema: JSON schema to validate against

    Returns:
        The validated data dictionary (unchanged)

    Raises:
        ValueError: If validation fails
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
    except ValidationError as e:
        # Convert jsonschema.ValidationError to ValueError for consistency
        raise ValueError(str(e.message)) from e
    return data


# Create schema-specific validators using partial application
validate_pretooluse_input = partial(_validate_with_schema, schema=PRETOOLUSE_INPUT_SCHEMA)
validate_pretooluse_output = partial(_validate_with_schema, schema=PRETOOLUSE_OUTPUT_SCHEMA)
