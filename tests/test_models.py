"""Tests for YAML configuration data models."""

from typing import get_type_hints


from src.models import ConfigDict


class TestConfigDictTypedDict:
    """Test ConfigDict TypedDict型定義."""

    def test_config_dict_can_be_imported(self) -> None:
        """ConfigDict TypedDictが正しくインポートできることを確認"""
        assert ConfigDict is not None

    def test_config_dict_type_hints_exist(self) -> None:
        """ConfigDictの型ヒントが存在することを確認"""
        hints = get_type_hints(ConfigDict)
        assert "prompt" in hints
        assert "model" in hints
        assert "allowed_tools" in hints

    def test_config_dict_with_required_field_only(self) -> None:
        """必須フィールド（prompt）のみを持つConfigDictが作成できることを確認"""
        config: ConfigDict = {
            "prompt": "Test prompt for BigQuery validation"
        }
        assert config["prompt"] == "Test prompt for BigQuery validation"

    def test_config_dict_with_all_fields(self) -> None:
        """全フィールドを持つConfigDictが作成できることを確認"""
        config: ConfigDict = {
            "prompt": "Test prompt",
            "model": "claude-sonnet-4-20250514",
            "allowed_tools": ["Bash", "Read"]
        }
        assert config["prompt"] == "Test prompt"
        assert config["model"] == "claude-sonnet-4-20250514"
        assert config["allowed_tools"] == ["Bash", "Read"]

    def test_config_dict_with_optional_model_field(self) -> None:
        """promptとmodelフィールドを持つConfigDictが作成できることを確認"""
        config: ConfigDict = {
            "prompt": "Test prompt",
            "model": "claude-opus-4-20250514"
        }
        assert config["prompt"] == "Test prompt"
        assert config["model"] == "claude-opus-4-20250514"

    def test_config_dict_with_optional_allowed_tools_field(self) -> None:
        """promptとallowed_toolsフィールドを持つConfigDictが作成できることを確認"""
        config: ConfigDict = {
            "prompt": "Test prompt",
            "allowed_tools": ["Write", "Edit"]
        }
        assert config["prompt"] == "Test prompt"
        assert config["allowed_tools"] == ["Write", "Edit"]

    def test_config_dict_empty_allowed_tools(self) -> None:
        """空のallowed_toolsリストを持つConfigDictが作成できることを確認"""
        config: ConfigDict = {
            "prompt": "Test prompt",
            "allowed_tools": []
        }
        assert config["prompt"] == "Test prompt"
        assert config["allowed_tools"] == []

    def test_config_dict_with_multiline_prompt(self) -> None:
        """複数行のpromptを持つConfigDictが作成できることを確認"""
        multiline_prompt = """
        You are a BigQuery query validator.
        Check if the query is safe.
        Deny dangerous operations.
        """
        config: ConfigDict = {
            "prompt": multiline_prompt
        }
        assert config["prompt"] == multiline_prompt
