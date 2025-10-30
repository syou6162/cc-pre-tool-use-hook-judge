"""Configuration loading for YAML-based validator settings."""

from importlib import resources
from pathlib import Path

import yaml

from src.models import ConfigDict
from src.schema import validate_config_yaml


class ConfigError(Exception):
    """Exception raised when configuration loading or validation fails."""

    pass


def load_builtin_config(name: str) -> ConfigDict:
    """Load a builtin configuration file from the builtin_configs directory.

    Args:
        name: Name of the builtin config (without .yaml extension)

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigError: If the builtin config file is not found or validation fails

    Example:
        >>> config = load_builtin_config("validate_bq_query")
        >>> print(config["prompt"])
    """
    try:
        # Use importlib.resources to access package data
        config_package = resources.files("builtin_configs")
        config_file = config_package / f"{name}.yaml"

        # Read the configuration file
        config_text = config_file.read_text()
        config_data = yaml.safe_load(config_text)

        if config_data is None:
            raise ConfigError(f"Builtin config '{name}' is empty")

        # Validate the configuration
        try:
            validated_config: ConfigDict = validate_config_yaml(config_data)  # type: ignore
            return validated_config
        except ValueError as e:
            raise ConfigError(f"Validation failed for builtin config '{name}': {e}") from e

    except FileNotFoundError as e:
        raise ConfigError(f"Builtin config '{name}' not found") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse builtin config '{name}': {e}") from e


def load_config(path: Path) -> ConfigDict:
    """Load an external YAML configuration file.

    Args:
        path: Path to the YAML configuration file

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigError: If the file is not found, parsing fails, or validation fails

    Example:
        >>> from pathlib import Path
        >>> config = load_config(Path("my_config.yaml"))
        >>> print(config["prompt"])
    """
    if not path.exists():
        raise ConfigError(f"Config file '{path}' not found")

    try:
        # Read and parse the YAML file
        config_text = path.read_text()
        config_data = yaml.safe_load(config_text)

        if config_data is None:
            raise ConfigError(f"Config file '{path}' is empty")

        # Validate the configuration
        try:
            validated_config: ConfigDict = validate_config_yaml(config_data)  # type: ignore
            return validated_config
        except ValueError as e:
            raise ConfigError(f"Validation failed for config file '{path}': {e}") from e

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file '{path}': {e}") from e
    except OSError as e:
        raise ConfigError(f"Failed to read config file '{path}': {e}") from e
