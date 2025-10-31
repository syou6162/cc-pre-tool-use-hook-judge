"""Data models for YAML configuration structures.

This module defines TypedDict structures for YAML configuration files
used by the BigQuery query validator and other validators.
"""

from typing import NotRequired, TypedDict


class ConfigDict(TypedDict):
    """YAML configuration structure for custom validators.

    Attributes:
        prompt: The validation prompt to append to the system prompt (required).
        model: The Claude model to use for validation (optional).
        allowed_tools: List of allowed tool names for the validator (optional).

    Example:
        >>> config: ConfigDict = {
        ...     "prompt": "Validate BigQuery queries for safety",
        ...     "model": "claude-sonnet-4-20250514",
        ...     "allowed_tools": ["Bash", "Read"]
        ... }
    """

    prompt: str
    model: NotRequired[str]
    allowed_tools: NotRequired[list[str]]
