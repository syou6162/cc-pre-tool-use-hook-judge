"""Tests for PreToolUse JSON schema validation."""

import pytest

from src.schema import (
    validate_config_yaml,
    validate_pretooluse_input,
    validate_pretooluse_output,
)


class TestPreToolUseInputValidation:
    """Test PreToolUse input JSON validation."""

    def test_invalid_data_type_raises_error(self) -> None:
        """不正なデータ型（文字列）に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input("not a dict")  # type: ignore

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
            validate_pretooluse_input(input_data)

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
            validate_pretooluse_input(input_data)

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
            validate_pretooluse_input(input_data)

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
            validate_pretooluse_input(input_data)

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

        result = validate_pretooluse_input(input_data)
        assert result == input_data

    def test_empty_dict_raises_error(self) -> None:
        """空の辞書に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input({})

    def test_number_raises_error(self) -> None:
        """数値に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input(12345)  # type: ignore

    def test_none_raises_error(self) -> None:
        """Noneに対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input(None)  # type: ignore

    def test_array_instead_of_object_raises_error(self) -> None:
        """配列が渡された場合にエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input([])  # type: ignore

    def test_boolean_raises_error(self) -> None:
        """真偽値に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_pretooluse_input(True)  # type: ignore


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

        result = validate_pretooluse_output(output_data)
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

        result = validate_pretooluse_output(output_data)
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

        result = validate_pretooluse_output(output_data)
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

        result = validate_pretooluse_output(output_data)
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
            validate_pretooluse_output(output_data)

    def test_missing_hook_specific_output(self) -> None:
        """hookSpecificOutputが欠けている場合にエラーを返すことを確認"""
        output_data: dict[str, object] = {}

        with pytest.raises(ValueError, match="hookSpecificOutput"):
            validate_pretooluse_output(output_data)

    def test_missing_permission_decision(self) -> None:
        """permissionDecisionが欠けている場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecisionReason": "Reason"
            }
        }

        with pytest.raises(ValueError, match="permissionDecision"):
            validate_pretooluse_output(output_data)

    def test_missing_permission_decision_reason(self) -> None:
        """permissionDecisionReasonが欠けている場合にエラーを返すことを確認"""
        output_data = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }

        with pytest.raises(ValueError, match="permissionDecisionReason"):
            validate_pretooluse_output(output_data)

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
            validate_pretooluse_output(output_data)


class TestConfigYamlValidation:
    """Test YAML configuration schema validation."""

    def test_valid_config_with_prompt_only(self) -> None:
        """必須promptフィールドのみを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": "Validate BigQuery queries for safety"
        }

        result = validate_config_yaml(config_data)
        assert result == config_data

    def test_valid_config_with_all_fields(self) -> None:
        """全フィールドを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": "Validate BigQuery queries",
            "model": "claude-sonnet-4-20250514",
            "allowed_tools": ["Bash", "Read", "Write"]
        }

        result = validate_config_yaml(config_data)
        assert result == config_data

    def test_valid_config_with_model_field(self) -> None:
        """promptとmodelフィールドを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": "Validate queries",
            "model": "claude-opus-4-20250514"
        }

        result = validate_config_yaml(config_data)
        assert result == config_data

    def test_valid_config_with_allowed_tools_field(self) -> None:
        """promptとallowed_toolsフィールドを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": "Validate queries",
            "allowed_tools": ["Bash"]
        }

        result = validate_config_yaml(config_data)
        assert result == config_data

    def test_valid_config_with_empty_allowed_tools(self) -> None:
        """空のallowed_toolsリストを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": "Validate queries",
            "allowed_tools": []
        }

        result = validate_config_yaml(config_data)
        assert result == config_data

    def test_missing_required_prompt_field(self) -> None:
        """必須promptフィールドが欠けている場合にエラーを返すことを確認"""
        config_data = {
            "model": "claude-sonnet-4-20250514"
        }

        with pytest.raises(ValueError, match="prompt"):
            validate_config_yaml(config_data)

    def test_empty_dict_raises_error(self) -> None:
        """空の辞書に対してエラーを返すことを確認"""
        with pytest.raises(ValueError, match="prompt"):
            validate_config_yaml({})

    def test_invalid_prompt_type(self) -> None:
        """promptフィールドの型が不正な場合にエラーを返すことを確認"""
        config_data = {
            "prompt": 123  # 数値は不正
        }

        with pytest.raises(ValueError):
            validate_config_yaml(config_data)

    def test_invalid_model_type(self) -> None:
        """modelフィールドの型が不正な場合にエラーを返すことを確認"""
        config_data = {
            "prompt": "Valid prompt",
            "model": ["not", "a", "string"]  # 配列は不正
        }

        with pytest.raises(ValueError):
            validate_config_yaml(config_data)

    def test_invalid_allowed_tools_type(self) -> None:
        """allowed_toolsフィールドの型が不正な場合にエラーを返すことを確認"""
        config_data = {
            "prompt": "Valid prompt",
            "allowed_tools": "not an array"  # 文字列は不正
        }

        with pytest.raises(ValueError):
            validate_config_yaml(config_data)

    def test_invalid_allowed_tools_item_type(self) -> None:
        """allowed_tools配列の要素の型が不正な場合にエラーを返すことを確認"""
        config_data = {
            "prompt": "Valid prompt",
            "allowed_tools": ["Bash", 123, "Write"]  # 数値要素は不正
        }

        with pytest.raises(ValueError):
            validate_config_yaml(config_data)

    def test_invalid_data_type_raises_error(self) -> None:
        """不正なデータ型（文字列）に対してエラーを返すことを確認"""
        with pytest.raises(ValueError):
            validate_config_yaml("not a dict")  # type: ignore

    def test_multiline_prompt(self) -> None:
        """複数行のpromptを持つ有効な設定に対してバリデーションが成功することを確認"""
        config_data = {
            "prompt": """You are a BigQuery query validator.
Check if the query is safe.
Deny dangerous operations like DROP, DELETE, UPDATE."""
        }

        result = validate_config_yaml(config_data)
        assert result == config_data
