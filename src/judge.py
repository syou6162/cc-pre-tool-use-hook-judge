"""Main judgment logic for PreToolUse hook validation."""

import json
from typing import Any

import anyio
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from claude_agent_sdk.types import SystemPromptPreset

from src.exceptions import NoResponseError, SchemaValidationError
from src.schema import PRETOOLUSE_INPUT_SCHEMA, PRETOOLUSE_OUTPUT_SCHEMA

# Simplified system prompt (schema is specified via output_format)
SYSTEM_PROMPT_TEMPLATE = """You are a PreToolUse hook validator for Claude Code.

Your task is to validate tool usage and return a decision based on the validation rules provided in <custom_validation_rules>.

The input structure is:
<input_json_schema>
{input_schema}
</input_json_schema>

If you cannot determine whether to allow or deny based on the provided rules, default to DENY for safety."""


async def judge_pretooluse_async(
    input_data: dict[str, Any],
    prompt: str,
    model: str | None = None,
    allowed_tools: list[str] | None = None,
) -> dict[str, Any]:
    """Judge PreToolUse hook input and return decision (async).

    Uses Claude Agent SDK's structured output feature to automatically
    validate and retry JSON schema compliance.

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
        NoResponseError: If no result message is received
        SchemaValidationError: If structured output generation fails after retries
    """
    user_prompt = f"""# Current Tool Usage
{json.dumps(input_data, indent=2)}"""

    system_prompt_text = SYSTEM_PROMPT_TEMPLATE.format(
        input_schema=json.dumps(PRETOOLUSE_INPUT_SCHEMA, indent=2)
    )
    system_prompt_text = f"""<system_instructions>
{system_prompt_text}
</system_instructions>

<custom_validation_rules>
{prompt}
</custom_validation_rules>"""

    system_prompt = SystemPromptPreset(
        type="preset", preset="claude_code", append=system_prompt_text
    )

    # Build options with structured output
    options_dict: dict[str, Any] = {
        "system_prompt": system_prompt,
        "output_format": {"type": "json_schema", "schema": PRETOOLUSE_OUTPUT_SCHEMA},
    }
    if model is not None:
        options_dict["model"] = model
    if allowed_tools is not None:
        options_dict["allowed_tools"] = allowed_tools

    options = ClaudeAgentOptions(**options_dict)

    # Use query() function with structured output
    result_message: ResultMessage | None = None
    async for message in query(prompt=user_prompt, options=options):
        if isinstance(message, ResultMessage):
            result_message = message

    # Validate result
    if result_message is None:
        raise NoResponseError("No result message received from Claude Agent SDK")

    if result_message.is_error:
        raise SchemaValidationError(
            f"Failed to generate valid structured output: {result_message.result}"
        )

    if result_message.structured_output is None:
        raise SchemaValidationError("No structured output in result message")

    return result_message.structured_output


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
