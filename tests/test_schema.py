"""Tests for PreToolUse JSON schema validation."""

import json
import pytest

from src.schema import validate_pretooluse_input, validate_pretooluse_output


class TestPreToolUseInputValidation:
    """Test PreToolUse input JSON validation."""

    def test_invalid_json_string_raises_error(self) -> None:
        """不正なJSON文字列に対してエラーを返すことを確認"""
        invalid_json = "not a json"

        with pytest.raises(json.JSONDecodeError):
            validate_pretooluse_input(invalid_json)

    def test_missing_required_field_session_id(self) -> None:
        """必須フィールドsession_idが欠けている場合にエラーを返すことを確認"""
        input_data = {
            "transcript_path": "/path/to/session.jsonl",
            "cwd": "/path/to/cwd",
            "permission_mode": "default",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/test.txt", "content": "test"}
        }

        with pytest.raises(ValueError, match="session_id"):
            validate_pretooluse_input(json.dumps(input_data))

    def test_missing_required_field_hook_event_name(self) -> None:
        """必須フィールドhook_event_nameが欠けている場合にエラーを返すことを確認"""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/path/to/session.jsonl",
            "cwd": "/path/to/cwd",
            "permission_mode": "default",
            "tool_name": "Write",
            "tool_input": {"file_path": "/test.txt", "content": "test"}
        }

        with pytest.raises(ValueError, match="hook_event_name"):
            validate_pretooluse_input(json.dumps(input_data))

    def test_invalid_hook_event_name(self) -> None:
        """hook_event_nameが"PreToolUse"でない場合にエラーを返すことを確認"""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/path/to/session.jsonl",
            "cwd": "/path/to/cwd",
            "permission_mode": "default",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/test.txt", "content": "test"}
        }

        with pytest.raises(ValueError, match="PreToolUse"):
            validate_pretooluse_input(json.dumps(input_data))

    def test_missing_required_field_tool_name(self) -> None:
        """必須フィールドtool_nameが欠けている場合にエラーを返すことを確認"""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/path/to/session.jsonl",
            "cwd": "/path/to/cwd",
            "permission_mode": "default",
            "hook_event_name": "PreToolUse",
            "tool_input": {"file_path": "/test.txt", "content": "test"}
        }

        with pytest.raises(ValueError, match="tool_name"):
            validate_pretooluse_input(json.dumps(input_data))

    def test_valid_pretooluse_input(self) -> None:
        """有効なPreToolUse入力に対してバリデーションが成功することを確認"""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/Users/test/.claude/projects/test/session.jsonl",
            "cwd": "/Users/test",
            "permission_mode": "default",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/path/to/file.txt",
                "content": "file content"
            }
        }

        result = validate_pretooluse_input(json.dumps(input_data))
        assert result == input_data

    def test_empty_string_raises_error(self) -> None:
        """空文字列に対してエラーを返すことを確認"""
        with pytest.raises(json.JSONDecodeError):
            validate_pretooluse_input("")

    def test_whitespace_only_string_raises_error(self) -> None:
        """空白のみの文字列に対してエラーを返すことを確認"""
        with pytest.raises(json.JSONDecodeError):
            validate_pretooluse_input("   ")

    def test_number_string_raises_error(self) -> None:
        """数値文字列に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input("12345")

    def test_null_string_raises_error(self) -> None:
        """null文字列に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input("null")

    def test_array_instead_of_object_raises_error(self) -> None:
        """配列が渡された場合にエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input("[]")

    def test_boolean_string_raises_error(self) -> None:
        """真偽値文字列に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input("true")


class TestPreToolUseOutputValidation:
    """Test PreToolUse output JSON validation."""

    def test_valid_output_with_allow_decision(self) -> None:
        """permissionDecisionがallowの有効な出力に対してバリデーションが成功することを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "This is a safe operation"
            }
        }

        result = validate_pretooluse_output(json.dumps(output_data))
        assert result == output_data

    def test_valid_output_with_deny_decision(self) -> None:
        """permissionDecisionがdenyの有効な出力に対してバリデーションが成功することを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "This operation is not allowed"
            }
        }

        result = validate_pretooluse_output(json.dumps(output_data))
        assert result == output_data

    def test_valid_output_with_ask_decision(self) -> None:
        """permissionDecisionがaskの有効な出力に対してバリデーションが成功することを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "User confirmation required"
            }
        }

        result = validate_pretooluse_output(json.dumps(output_data))
        assert result == output_data

    def test_valid_output_with_updated_input(self) -> None:
        """updatedInputを含む有効な出力に対してバリデーションが成功することを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Modified input",
                "updatedInput": {
                    "file_path": "/modified/path.txt"
                }
            }
        }

        result = validate_pretooluse_output(json.dumps(output_data))
        assert result == output_data

    def test_invalid_permission_decision_value(self) -> None:
        """permissionDecisionが不正な値の場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "maybe",
                "permissionDecisionReason": "Unsure"
            }
        }

        with pytest.raises(ValueError):
            validate_pretooluse_output(json.dumps(output_data))

    def test_missing_hook_specific_output(self) -> None:
        """hookSpecificOutputが欠けている場合にエラーを返すことを確認"""
        output_data = {}

        with pytest.raises(ValueError, match="hookSpecificOutput"):
            validate_pretooluse_output(json.dumps(output_data))

    def test_missing_permission_decision(self) -> None:
        """permissionDecisionが欠けている場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecisionReason": "Reason"
            }
        }

        with pytest.raises(ValueError, match="permissionDecision"):
            validate_pretooluse_output(json.dumps(output_data))

    def test_missing_permission_decision_reason(self) -> None:
        """permissionDecisionReasonが欠けている場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }

        with pytest.raises(ValueError, match="permissionDecisionReason"):
            validate_pretooluse_output(json.dumps(output_data))

    def test_invalid_hook_event_name_in_output(self) -> None:
        """hookEventNameが不正な値の場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Reason"
            }
        }

        with pytest.raises(ValueError, match="PreToolUse"):
            validate_pretooluse_output(json.dumps(output_data))
