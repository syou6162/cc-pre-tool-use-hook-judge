"""Main judgment logic for PreToolUse hook validation."""

import json
import re
from typing import Any

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)
from claude_agent_sdk.types import SystemPromptPreset

from src.constants import (
    DEFAULT_PERMISSION_DECISION,
    DEFAULT_PERMISSION_REASON,
    HOOK_EVENT_NAME,
    MAX_RETRY_ATTEMPTS,
)
from src.exceptions import (
    CodeFenceInResponseError,
    InvalidJSONError,
    InvalidJSONPrefixError,
    InvalidJSONSuffixError,
    InvalidResponseFormatError,
    NoResponseError,
    SchemaValidationError,
)
from src.schema import (
    PRETOOLUSE_INPUT_SCHEMA,
    PRETOOLUSE_OUTPUT_SCHEMA,
    validate_pretooluse_output,
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


async def _receive_text_response(client: ClaudeSDKClient) -> str:
    """Receive text response from Claude Agent SDK.

    Args:
        client: Claude SDK client instance

    Returns:
        Combined text from all text blocks in the response
    """
    response_text = ""
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text
    return response_text


def _validate_response_format(text: str) -> None:
    """Validate response text format before JSON parsing.

    Checks for common formatting issues and raises specific errors:
    - Code fences (```json or ```)
    - Leading emoji or special characters before {
    - Text before or after JSON

    Args:
        text: Response text to validate

    Raises:
        CodeFenceInResponseError: If response contains markdown code fences
        InvalidJSONPrefixError: If response has invalid prefix before JSON
        InvalidJSONSuffixError: If response has text after JSON
    """
    text_stripped = text.strip()

    # Check for code fences - most specific check first
    if re.search(r'```', text_stripped):
        raise CodeFenceInResponseError(CodeFenceInResponseError.create_message())

    # Check for leading characters before {
    # JSON should start with { (after whitespace)
    if text_stripped and not re.match(r'^\s*\{', text_stripped):
        leading_chars = text_stripped[:50]
        raise InvalidJSONPrefixError(InvalidJSONPrefixError.create_message(leading_chars))

    # Check for text after the closing }
    last_brace_pos = text_stripped.rfind('}')
    if last_brace_pos != -1:
        text_after = text_stripped[last_brace_pos + 1:].strip()
        if text_after:
            raise InvalidJSONSuffixError(InvalidJSONSuffixError.create_message(text_after))


def _wrap_output_if_needed(output_data: dict[str, Any]) -> dict[str, Any]:
    """Wrap output data in hookSpecificOutput format if not already wrapped.

    Args:
        output_data: Raw output data from Claude Agent SDK

    Returns:
        Output data wrapped in hookSpecificOutput format
    """
    if "hookSpecificOutput" not in output_data:
        return {
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT_NAME,
                "permissionDecision": output_data.get(
                    "permissionDecision", DEFAULT_PERMISSION_DECISION
                ),
                "permissionDecisionReason": output_data.get(
                    "permissionDecisionReason", DEFAULT_PERMISSION_REASON
                ),
            }
        }
    return output_data


async def judge_pretooluse_async(input_data: dict[str, Any], prompt: str | None = None, model: str | None = None, allowed_tools: list[str] | None = None) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (async).

    Args:
        input_data: Validated PreToolUse hook input dictionary
        prompt: Optional custom prompt to append to the default system prompt.
                If None, uses SYSTEM_PROMPT as-is.
        model: Optional model name to use for the judgment.
               If None, uses the default model.
        allowed_tools: Optional list of allowed tool names for Claude Agent SDK.
                       If None, uses the default allowed tools.

    Returns:
        PreToolUse hook output dictionary

    Raises:
        ValueError: If JSON parsing fails after retries
    """
    # Extract tool information
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]

    # Create user prompt with current tool usage
    user_prompt = f"""# Current Tool Usage
Tool: {tool_name}
Input: {json.dumps(tool_input, indent=2)}"""

    # Determine system prompt based on whether custom prompt is provided
    system_prompt: str | SystemPromptPreset
    if prompt is None:
        system_prompt = SYSTEM_PROMPT
    else:
        # Use SystemPromptPreset when custom prompt is provided
        # Add JSON output instructions to custom prompt
        json_instructions = f"""

# Output JSON Schema
{json.dumps(PRETOOLUSE_OUTPUT_SCHEMA, indent=2)}

IMPORTANT: Return ONLY raw JSON. Do NOT wrap it in markdown code blocks (```json or ```).

Return ONLY a valid JSON matching the output schema, with:
- permissionDecision: "allow", "deny", or "ask"
- permissionDecisionReason: A brief explanation

Output JSON only, no other text, no code blocks, no formatting."""

        system_prompt = SystemPromptPreset(
            type="preset",
            preset="claude_code",
            append=prompt + json_instructions
        )

    # Configure Claude Agent options with retry support
    # Note: Only pass allowed_tools if explicitly set (not None) to preserve SDK defaults
    options_dict: dict[str, Any] = {
        "system_prompt": system_prompt,
        "max_turns": MAX_RETRY_ATTEMPTS,
    }
    if model is not None:
        options_dict["model"] = model
    if allowed_tools is not None:
        options_dict["allowed_tools"] = allowed_tools

    options = ClaudeAgentOptions(**options_dict)

    # Use ClaudeSDKClient for bidirectional conversation
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_prompt)

        # Try to get valid JSON response with retry
        for attempt in range(MAX_RETRY_ATTEMPTS):
            # Receive response
            response_text = await _receive_text_response(client)

            # Check if we got any response
            if not response_text:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await client.query(
                        "Please provide a response in valid JSON format."
                    )
                    continue
                raise NoResponseError(
                    f"No response received from Claude Agent SDK after {MAX_RETRY_ATTEMPTS} attempts"
                )

            # Try to parse JSON and validate output
            try:
                output_data = json.loads(response_text)
                output_data = _wrap_output_if_needed(output_data)
                # Validate output against schema
                validate_pretooluse_output(output_data)
                return output_data

            except json.JSONDecodeError as e:
                # JSON parsing failed
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await client.query(
                        f"Your previous response was not valid JSON. Error: {str(e)}. "
                        "Please return ONLY raw JSON without any markdown formatting or code blocks."
                    )
                    continue
                raise InvalidJSONError(
                    f"Failed to parse valid JSON after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
                )
            except ValueError as e:
                # Schema validation failed
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await client.query(
                        f"Your previous response did not match the required schema. Error: {str(e)}. "
                        "Please return a valid response matching the output schema."
                    )
                    continue
                raise SchemaValidationError(
                    f"Failed to get valid output after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
                )

    # This line is unreachable but required for mypy type checking
    raise AssertionError("Unreachable code")


def judge_pretooluse(input_data: dict[str, Any], prompt: str | None = None, model: str | None = None, allowed_tools: list[str] | None = None) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (sync wrapper).

    Args:
        input_data: Validated PreToolUse hook input dictionary
        prompt: Optional custom prompt to append to the default system prompt.
                If None, uses SYSTEM_PROMPT as-is.
        model: Optional model name to use for the judgment.
               If None, uses the default model.
        allowed_tools: Optional list of allowed tool names for Claude Agent SDK.
                       If None, uses the default allowed tools.

    Returns:
        PreToolUse hook output dictionary

    Raises:
        ValueError: If JSON parsing fails after retries
    """
    return anyio.run(judge_pretooluse_async, input_data, prompt, model, allowed_tools)
