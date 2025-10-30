"""Main entry point for cc-pre-tool-use-hook-judge CLI."""

import json
import sys

from src.judge import judge_pretooluse


def main() -> None:
    """Read PreToolUse input from stdin and output judgment to stdout."""
    try:
        # Read input from stdin
        input_json = sys.stdin.read()

        # Judge the input
        output_data = judge_pretooluse(input_json)

        # Output result to stdout
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    except Exception as e:
        # Output error to stderr
        error_output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Validation error: {str(e)}",
            }
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
