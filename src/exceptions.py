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

    @staticmethod
    def create_message() -> str:
        """Create detailed error message for code fence error.

        Returns:
            Formatted error message with examples
        """
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

    @staticmethod
    def create_message(leading_chars: str) -> str:
        """Create detailed error message for invalid prefix error.

        Args:
            leading_chars: The leading characters found before JSON

        Returns:
            Formatted error message with examples
        """
        return f"""Your response has invalid characters before the JSON object.
Found: {repr(leading_chars)}

Do NOT include:
- Emojis (⏺, ✓, etc.)
- Explanatory text ('Sure!', 'Here is the result:', etc.)
- Any other characters

Your response must start directly with {{}}.

WRONG:
⏺ {{'permissionDecision': 'allow'}}
Sure! Here is the JSON: {{'permissionDecision': 'allow'}}

CORRECT:
{{'permissionDecision': 'allow'}}"""


class InvalidJSONSuffixError(InvalidResponseFormatError):
    """Response has text after the closing brace of JSON object."""

    @staticmethod
    def create_message(trailing_text: str) -> str:
        """Create detailed error message for invalid suffix error.

        Args:
            trailing_text: The trailing text found after JSON

        Returns:
            Formatted error message with examples
        """
        return f"""Your response has text after the closing }}.
Found: {repr(trailing_text)}

Do NOT include explanatory text after the JSON.

WRONG:
{{'permissionDecision': 'allow'}}
Hope this helps!

CORRECT:
{{'permissionDecision': 'allow'}}"""


class NoResponseError(JudgeError):
    """No response received from judgment system."""

    pass


class SchemaValidationError(JudgeError):
    """Schema validation failed."""

    pass


class ConfigError(JudgeError):
    """Configuration file loading or validation failed."""

    pass
