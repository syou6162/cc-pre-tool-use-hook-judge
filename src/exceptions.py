"""Custom exception classes for the application."""


class JudgeError(Exception):
    """Base exception for judgment errors."""

    pass


class InvalidJSONError(JudgeError):
    """JSON parsing failed."""

    pass


class NoResponseError(JudgeError):
    """No response received from judgment system."""

    pass


class SchemaValidationError(JudgeError):
    """Schema validation failed."""

    pass
