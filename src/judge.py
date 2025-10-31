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

    if '```' in text_stripped:
        raise CodeFenceInResponseError()

    if text_stripped and not text_stripped.startswith('{'):
        raise InvalidJSONPrefixError()

    if text_stripped and not text_stripped.endswith('}'):
        raise InvalidJSONSuffixError()


def _create_retry_error_message(e: Exception) -> str:
    """Create retry error message based on exception type.

    Args:
        e: The exception that occurred

    Returns:
        Formatted error message for retry
    """
    if isinstance(e, InvalidResponseFormatError):
        return str(e)
    elif isinstance(e, json.JSONDecodeError):
        return (
            f"Your response could not be parsed as JSON.\n"
            f"Error: {str(e)}\n\n"
            f"Please return ONLY a raw JSON object starting with {{ and ending with }}."
        )
    elif isinstance(e, ValueError):
        return (
            f"Your response did not match the required schema.\n"
            f"Error: {str(e)}\n\n"
            f"Please return a valid response matching the output schema."
        )
    else:
        raise TypeError(f"Unexpected exception type: {type(e)}")


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


async def judge_pretooluse_async(input_data: dict[str, Any], prompt: str, model: str | None = None, allowed_tools: list[str] | None = None) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (async).

    Args:
        input_data: Validated PreToolUse hook input dictionary
        prompt: Custom prompt to append to the Claude Code system prompt.
        model: Optional model name to use for the judgment.
               If None, uses the default model.
        allowed_tools: Optional list of allowed tool names for Claude Agent SDK.
                       If None, uses the default allowed tools.

    Returns:
        PreToolUse hook output dictionary

    Raises:
        ValueError: If JSON parsing fails after retries
    """
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]

    user_prompt = f"""# Current Tool Usage
Tool: {tool_name}
Input: {json.dumps(tool_input, indent=2)}"""

    system_prompt = SystemPromptPreset(
        type="preset",
        preset="claude_code",
        append=SYSTEM_PROMPT + "\n\n" + prompt
    )

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

    async with ClaudeSDKClient(options=options) as client:
        query_message = user_prompt

        for attempt in range(MAX_RETRY_ATTEMPTS):
            await client.query(query_message)
            response_text = await _receive_text_response(client)

            if not response_text:
                query_message = "Please provide a response in valid JSON format."
                continue

            try:
                _validate_response_format(response_text)
                output_data = json.loads(response_text)
                output_data = _wrap_output_if_needed(output_data)
                validate_pretooluse_output(output_data)
                return output_data

            except (InvalidResponseFormatError, json.JSONDecodeError, ValueError) as e:
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    if isinstance(e, ValueError):
                        raise SchemaValidationError(
                            f"Failed to get valid output after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
                        )
                    elif isinstance(e, json.JSONDecodeError):
                        raise InvalidJSONError(
                            f"Failed to parse JSON after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
                        )
                    else:
                        raise

                query_message = _create_retry_error_message(e)
                continue

        raise NoResponseError(
            f"No response received from Claude Agent SDK after {MAX_RETRY_ATTEMPTS} attempts"
        )

    raise AssertionError("Unreachable: async with block should always return or raise")


def judge_pretooluse(input_data: dict[str, Any], prompt: str, model: str | None = None, allowed_tools: list[str] | None = None) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (sync wrapper).

    Args:
        input_data: Validated PreToolUse hook input dictionary
        prompt: Custom prompt to append to the Claude Code system prompt.
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
