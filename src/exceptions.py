"""Custom exception classes for the application."""


class JudgeError(Exception):
    """Base exception for judgment errors."""

    pass


class InvalidJSONError(JudgeError):
    """JSON parsing failed."""

    pass


class InvalidResponseFormatError(JudgeError):
    """Base exception for response format errors."""

    pass


class CodeFenceInResponseError(InvalidResponseFormatError):
    """Response contains markdown code fences (```)."""

    def __str__(self) -> str:
        """Return detailed error message with examples."""
        return """Your response contains markdown code fences (```).
Do NOT wrap the JSON in markdown code blocks like ```json ... ```.
Return ONLY the raw JSON object.

WRONG:
```json
{"permissionDecision": "allow"}
```

CORRECT:
{"permissionDecision": "allow"}"""


class InvalidJSONPrefixError(InvalidResponseFormatError):
    """Response has invalid characters before the JSON object (e.g., emoji, text)."""

    def __str__(self) -> str:
        """Return detailed error message with examples."""
        return """Your response has invalid characters before the JSON object.

Do NOT include:
- Emojis (⏺, ✓, etc.)
- Explanatory text ('Sure!', 'Here is the result:', etc.)
- Any other characters

Your response must start directly with {.

WRONG:
⏺ {'permissionDecision': 'allow'}
Sure! Here is the JSON: {'permissionDecision': 'allow'}

CORRECT:
{'permissionDecision': 'allow'}"""


class InvalidJSONSuffixError(InvalidResponseFormatError):
    """Response has text after the closing brace of JSON object."""

    def __str__(self) -> str:
        """Return detailed error message with examples."""
        return """Your response has text after the closing }.

Do NOT include explanatory text after the JSON.

WRONG:
{'permissionDecision': 'allow'}
Hope this helps!

CORRECT:
{'permissionDecision': 'allow'}"""


class NoResponseError(JudgeError):
    """No response received from judgment system."""

    pass


class SchemaValidationError(JudgeError):
    """Schema validation failed."""

    pass
