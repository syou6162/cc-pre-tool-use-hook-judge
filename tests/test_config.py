"""Tests for YAML configuration loading."""

from pathlib import Path

import pytest

from src.config import ConfigError, load_builtin_config, load_config


class TestBuiltinConfigLoading:
    """Test builtin configuration loading."""

    def test_load_builtin_config_success(self) -> None:
        """ビルトイン設定（validate_bq_query.yaml）が正しく読み込めることを確認"""
        config = load_builtin_config("validate_bq_query")

        assert "prompt" in config
        assert isinstance(config["prompt"], str)
        assert len(config["prompt"]) > 0

    def test_load_nonexistent_builtin_config(self) -> None:
        """存在しないビルトイン設定を読み込もうとした場合にConfigErrorを返すことを確認"""
        with pytest.raises(ConfigError, match="Builtin config .* not found"):
            load_builtin_config("nonexistent_config")


class TestExternalConfigLoading:
    """Test external YAML configuration loading."""

    def test_load_valid_external_config(self, tmp_path: Path) -> None:
        """有効な外部YAML設定ファイルが正しく読み込めることを確認"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
prompt: "Test validation prompt"
model: "sonnet"
allowed_tools:
  - Bash
  - Read
""")

        config = load_config(config_file)

        assert config["prompt"] == "Test validation prompt"
        assert config["model"] == "sonnet"
        assert config["allowed_tools"] == ["Bash", "Read"]

    def test_load_minimal_external_config(self, tmp_path: Path) -> None:
        """必須フィールドのみを持つ外部YAML設定ファイルが正しく読み込めることを確認"""
        config_file = tmp_path / "minimal_config.yaml"
        config_file.write_text("""
prompt: "Minimal prompt"
""")

        config = load_config(config_file)

        assert config["prompt"] == "Minimal prompt"
        assert "model" not in config
        assert "allowed_tools" not in config

    def test_load_config_with_multiline_prompt(self, tmp_path: Path) -> None:
        """複数行のpromptを持つ外部YAML設定ファイルが正しく読み込めることを確認"""
        config_file = tmp_path / "multiline_config.yaml"
        config_file.write_text("""
prompt: |
  You are a BigQuery query validator.
  Check if the query is safe.
  Deny dangerous operations.
model: "haiku"
""")

        config = load_config(config_file)

        assert "You are a BigQuery query validator" in config["prompt"]
        assert "Check if the query is safe" in config["prompt"]
        assert config["model"] == "haiku"

    def test_load_nonexistent_file(self) -> None:
        """存在しないファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        nonexistent_file = Path("/nonexistent/path/config.yaml")

        with pytest.raises(ConfigError, match="Config file .* not found"):
            load_config(nonexistent_file)

    def test_load_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """不正なYAML構文のファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "invalid_syntax.yaml"
        config_file.write_text("""
prompt: "Test prompt
model: unquoted value with spaces
  - this is wrong indentation
""")

        with pytest.raises(ConfigError, match="Failed to parse"):
            load_config(config_file)

    def test_load_config_missing_required_field(self, tmp_path: Path) -> None:
        """必須フィールド（prompt）が欠けている設定ファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "missing_prompt.yaml"
        config_file.write_text("""
model: "sonnet"
allowed_tools:
  - Bash
""")

        with pytest.raises(ConfigError, match="prompt"):
            load_config(config_file)

    def test_load_config_invalid_model_name(self, tmp_path: Path) -> None:
        """無効なモデル名を持つ設定ファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "invalid_model.yaml"
        config_file.write_text("""
prompt: "Test prompt"
model: "invalid-model-name"
""")

        with pytest.raises(ConfigError, match="Validation failed"):
            load_config(config_file)

    def test_load_config_invalid_prompt_type(self, tmp_path: Path) -> None:
        """promptフィールドの型が不正な設定ファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "invalid_prompt_type.yaml"
        config_file.write_text("""
prompt: 12345
""")

        with pytest.raises(ConfigError, match="Validation failed"):
            load_config(config_file)

    def test_load_config_invalid_allowed_tools_type(self, tmp_path: Path) -> None:
        """allowed_toolsフィールドの型が不正な設定ファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "invalid_tools_type.yaml"
        config_file.write_text("""
prompt: "Test prompt"
allowed_tools: "not an array"
""")

        with pytest.raises(ConfigError, match="Validation failed"):
            load_config(config_file)

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """空のファイルを読み込もうとした場合にConfigErrorを返すことを確認"""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ConfigError):
            load_config(config_file)
