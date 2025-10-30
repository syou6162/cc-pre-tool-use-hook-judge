"""Main entry point for cc-pre-tool-use-hook-judge CLI."""

import json
import sys
from typing import Any

from src.judge import judge_pretooluse
from src.schema import validate_pretooluse_input


def create_error_output(reason: str) -> dict[str, Any]:
    """Create error output in PreToolUse hook format.

    Args:
        reason: The reason for denying the operation

    Returns:
        Error output dictionary with deny decision
    """
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
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
        # Output validation error to stderr with user-friendly message
        error_message = str(e)
        if "Failed to parse valid JSON" in error_message:
            reason = "判定システムが正しいJSON形式で応答できませんでした。安全のため操作を拒否します。"
        elif "No response received" in error_message:
            reason = "判定システムから応答がありませんでした。安全のため操作を拒否します。"
        else:
            reason = f"入力検証エラー: {error_message}"

        error_output = create_error_output(reason)
        print(json.dumps(error_output, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Output unexpected error to stderr
        error_output = create_error_output(f"予期しないエラーが発生しました: {str(e)}")
        print(json.dumps(error_output, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
