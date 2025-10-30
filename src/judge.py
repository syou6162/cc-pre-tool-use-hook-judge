"""Main judgment logic for PreToolUse hook validation."""

import json
from typing import Any

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)

from src.schema import (
    PRETOOLUSE_INPUT_SCHEMA,
    PRETOOLUSE_OUTPUT_SCHEMA,
    validate_pretooluse_input,
)

# Maximum number of retry attempts for JSON parsing
MAX_RETRY_ATTEMPTS = 3

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

    # Configure Claude Agent options with retry support
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        max_turns=MAX_RETRY_ATTEMPTS,
    )

    # Use ClaudeSDKClient for bidirectional conversation
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        # Try to get valid JSON response with retry
        for attempt in range(MAX_RETRY_ATTEMPTS):
            response_text = ""

            # Receive response
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text

            # Check if we got any response
            if not response_text:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await client.query(
                        "Please provide a response in valid JSON format."
                    )
                    continue
                raise ValueError("No response received from Claude Agent SDK")

            # Try to parse JSON
            try:
                output_data = json.loads(response_text)

                # Wrap in hookSpecificOutput if not already wrapped
                if "hookSpecificOutput" not in output_data:
                    output_data = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": output_data.get(
                                "permissionDecision", "allow"
                            ),
                            "permissionDecisionReason": output_data.get(
                                "permissionDecisionReason", "Operation allowed"
                            ),
                        }
                    }

                return output_data

            except json.JSONDecodeError as e:
                # If this is not the last attempt, ask for correction
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await client.query(
                        f"Your previous response was not valid JSON. Error: {str(e)}. "
                        "Please return ONLY raw JSON without any markdown formatting or code blocks."
                    )
                    continue
                # Last attempt failed
                raise ValueError(
                    f"Failed to parse valid JSON after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
                )

        # Should never reach here as all paths return or raise
        raise AssertionError("Unexpected: loop completed without return or raise")

    # Should never reach here - async with block always returns or raises
    raise AssertionError("Unexpected: async context exited without return or raise")


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
