"""Tests for _validate_response_format function."""

import pytest

from src.exceptions import (
    CodeFenceInResponseError,
    InvalidJSONPrefixError,
    InvalidJSONSuffixError,
)
from src.judge import _validate_response_format


class TestValidateResponseFormat:
    """Tests for _validate_response_format function."""

    def test_valid_json_passes(self) -> None:
        """Valid JSON without formatting issues should pass validation."""
        valid_json = '{"permissionDecision": "allow", "permissionDecisionReason": "test"}'
        # Should not raise any exception
        _validate_response_format(valid_json)

    def test_valid_json_with_newlines_passes(self) -> None:
        """Valid JSON with newlines should pass validation."""
        valid_json = """{
  "permissionDecision": "allow",
  "permissionDecisionReason": "test"
}"""
        # Should not raise any exception
        _validate_response_format(valid_json)

    def test_valid_json_with_leading_whitespace_passes(self) -> None:
        """Valid JSON with leading whitespace should pass validation."""
        valid_json = '   \n\t{"permissionDecision": "allow"}'
        # Should not raise any exception
        _validate_response_format(valid_json)

    def test_code_fence_raises_specific_error(self) -> None:
        """Response with code fences should raise CodeFenceInResponseError."""
        response_with_fence = '```json\n{"permissionDecision": "allow"}\n```'
        with pytest.raises(CodeFenceInResponseError):
            _validate_response_format(response_with_fence)

    def test_code_fence_without_language_raises_specific_error(self) -> None:
        """Response with code fences without language tag should raise error."""
        response_with_fence = '```\n{"permissionDecision": "allow"}\n```'
        with pytest.raises(CodeFenceInResponseError):
            _validate_response_format(response_with_fence)

    def test_emoji_prefix_raises_specific_error(self) -> None:
        """Response with emoji prefix should raise InvalidJSONPrefixError."""
        response_with_emoji = '⏺ {"permissionDecision": "allow"}'
        with pytest.raises(InvalidJSONPrefixError):
            _validate_response_format(response_with_emoji)

    def test_text_prefix_raises_specific_error(self) -> None:
        """Response with text prefix should raise InvalidJSONPrefixError."""
        response_with_text = 'Sure! Here is the JSON:\n{"permissionDecision": "allow"}'
        with pytest.raises(InvalidJSONPrefixError):
            _validate_response_format(response_with_text)

    def test_text_suffix_raises_specific_error(self) -> None:
        """Response with text suffix should raise InvalidJSONSuffixError."""
        response_with_suffix = '{"permissionDecision": "allow"}\nHope this helps!'
        with pytest.raises(InvalidJSONSuffixError):
            _validate_response_format(response_with_suffix)

    def test_empty_string_passes(self) -> None:
        """Empty string should pass (will fail at JSON parsing stage)."""
        # Empty string doesn't match any of our format validation patterns
        # It will fail later at JSON parsing stage with JSONDecodeError
        _validate_response_format("")

    def test_whitespace_only_passes(self) -> None:
        """Whitespace-only string should pass (will fail at JSON parsing stage)."""
        # Whitespace-only doesn't match any of our format validation patterns
        # It will fail later at JSON parsing stage with JSONDecodeError
        _validate_response_format("   \n\t")

    def test_multiple_issues_detects_first_one(self) -> None:
        """When multiple issues exist, should detect code fence first."""
        # Code fence check happens before prefix check
        response = '⏺ ```json\n{"permissionDecision": "allow"}\n```\nExtra text'
        with pytest.raises(CodeFenceInResponseError):
            _validate_response_format(response)
