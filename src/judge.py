"""Main judgment logic for PreToolUse hook validation."""

import json
from typing import Any

import anyio
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from src.schema import (
    PRETOOLUSE_INPUT_SCHEMA,
    PRETOOLUSE_OUTPUT_SCHEMA,
    validate_pretooluse_input,
)

# System prompt with JSON schemas
SYSTEM_PROMPT = f"""You are a PreToolUse hook validator for Claude Code.

Your task is to validate tool usage and return a decision.

# Input JSON Schema
{json.dumps(PRETOOLUSE_INPUT_SCHEMA, indent=2)}

# Output JSON Schema
{json.dumps(PRETOOLUSE_OUTPUT_SCHEMA, indent=2)}

For now, always return a decision to ALLOW the operation with a simple reason.

IMPORTANT: Return ONLY raw JSON. Do NOT wrap it in markdown code blocks (```json or ```).

Return ONLY a valid JSON matching the output schema, with:
- permissionDecision: "allow"
- permissionDecisionReason: A brief explanation

Output JSON only, no other text, no code blocks, no formatting."""


async def judge_pretooluse_async(input_json: str) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (async).

    Args:
        input_json: PreToolUse hook input as JSON string

    Returns:
        PreToolUse hook output dictionary

    Raises:
        ValueError: If input validation fails or JSON parsing fails after retries
    """
    # Validate input
    input_data = validate_pretooluse_input(input_json)

    # Extract tool information
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]

    # Create user prompt with current tool usage
    prompt = f"""# Current Tool Usage
Tool: {tool_name}
Input: {json.dumps(tool_input, indent=2)}"""

    # Configure Claude Agent options
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        max_turns=1,  # Single-turn judgment
    )

    # Call Claude Agent SDK for judgment
    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    # Check if we got any response
    if not response_text:
        raise ValueError("No response received from Claude Agent SDK")

    # Parse and validate output
    output_data = json.loads(response_text)

    # Wrap in hookSpecificOutput if not already wrapped
    if "hookSpecificOutput" not in output_data:
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": output_data.get("permissionDecision", "allow"),
                "permissionDecisionReason": output_data.get(
                    "permissionDecisionReason", "Operation allowed"
                ),
            }
        }

    return output_data


def judge_pretooluse(input_json: str) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (sync wrapper).

    Args:
        input_json: PreToolUse hook input as JSON string

    Returns:
        PreToolUse hook output dictionary

    Raises:
        ValueError: If input validation fails
    """
    return anyio.run(judge_pretooluse_async, input_json)
