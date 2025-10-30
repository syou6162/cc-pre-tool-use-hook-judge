"""Main entry point for cc-pre-tool-use-hook-judge CLI."""

import json
import sys
from typing import Any

from src.judge import judge_pretooluse
from src.schema import validate_pretooluse_input

# Constants for hook output
HOOK_EVENT_NAME = "PreToolUse"
PERMISSION_DENY = "deny"

# Error message patterns for classification
ERROR_PATTERN_INVALID_JSON = "Failed to parse valid JSON"
ERROR_PATTERN_NO_RESPONSE = "No response received"


def create_error_output(reason: str) -> dict[str, Any]:
    """Create error output in PreToolUse hook format.

    Args:
        reason: The reason for denying the operation

    Returns:
        Error output dictionary with deny decision
    """
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": PERMISSION_DENY,
            "permissionDecisionReason": reason,
        }
    }


def main() -> None:
    """Read PreToolUse input from stdin and output judgment to stdout."""
    try:
        # Read input from stdin
        input_json = sys.stdin.read()

        # Parse JSON
        input_data = json.loads(input_json)

        # Validate input
        input_data = validate_pretooluse_input(input_data)

        # Judge the input
        output_data = judge_pretooluse(input_data)

        # Output result to stdout
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    except ValueError as e:
        # Output validation error to stdout with user-friendly message
        error_message = str(e)
        if ERROR_PATTERN_INVALID_JSON in error_message:
            reason = "判定システムが正しいJSON形式で応答できませんでした。安全のため操作を拒否します。"
        elif ERROR_PATTERN_NO_RESPONSE in error_message:
            reason = "判定システムから応答がありませんでした。安全のため操作を拒否します。"
        else:
            reason = f"入力検証エラー: {error_message}"

        error_output = create_error_output(reason)
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
    except Exception as e:
        # Output unexpected error to stdout
        error_output = create_error_output(f"予期しないエラーが発生しました: {str(e)}")
        print(json.dumps(error_output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
