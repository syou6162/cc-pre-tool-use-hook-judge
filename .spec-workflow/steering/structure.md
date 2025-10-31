# Project Structure

## Directory Organization

```
cc-pre-tool-use-hook-judge/
├── src/                         # フラットパッケージ構造
│   ├── __init__.py              # パッケージ初期化
│   ├── __main__.py              # CLIエントリーポイント（argparse統合）
│   ├── config.py                # YAML設定の読み込みとバリデーション
│   ├── constants.py             # 定数定義
│   ├── exceptions.py            # カスタム例外クラス
│   ├── judge.py                 # メイン判定ロジック（Claude Agent SDK統合）
│   ├── schema.py                # JSON schema定義とバリデーション
│   └── models.py                # データモデル（TypedDict型定義）
├── builtin_configs/             # 組み込みYAML設定（パッケージデータ）
│   └── validate_bq_query.yaml   # BigQuery検証設定
├── tests/                       # テストコード
│   ├── __init__.py
│   ├── test_config.py           # 設定読み込みのテスト
│   ├── test_judge.py            # 判定ロジックのテスト
│   ├── test_models.py           # データモデルのテスト
│   ├── test_schema.py           # スキーマ検証のテスト
│   └── fixtures/                # テスト用フィクスチャ
│       └── configs/             # テスト用YAML設定
├── .spec-workflow/              # 仕様管理（spec workflow）
│   ├── steering/
│   ├── specs/
│   └── templates/
├── pyproject.toml               # プロジェクト設定（uv管理）
├── uv.lock                      # 依存関係ロックファイル
├── README.md                    # プロジェクト説明
└── LICENSE                      # ライセンス
```

## Why Flat Package Structure?

このプロジェクトは5-7ファイル程度の小規模CLIツールなので、フラット構造を採用：

- **シンプル**: ネストが浅く、ファイルが見つけやすい
- **import短い**: `from config import load_config` で済む
- **メンテナンス容易**: ファイル数が少ないので整理不要

将来的に大規模化した場合は、機能別サブパッケージへの分割を検討。

## Packaging Requirements

### 必須：`[build-system]`の定義

第三者が`uv tool run --from git+https://...`で実行できるようにするため、パッケージング必須：

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "hook-validator"  # パッケージ名
version = "0.1.0"

[project.scripts]
hook-validator = "__main__:main"  # CLIコマンド名
```

### パッケージ vs 非パッケージ

| | 非パッケージ | パッケージ |
|---|---|---|
| **リポジトリ内実行** | `uv run python script.py` | `uv run hook-validator` |
| **リポジトリ外実行** | ❌ 不可 | ✅ `uv tool run --from git+...` |
| **`[project.scripts]`** | ❌ 使えない | ✅ 使える |
| **用途** | スクリプト集 | CLIツール配布 |

今回は**第三者が簡単に実行できるCLIツール**なので、パッケージ化必須。

## Module Responsibilities

### `__main__.py` - CLIエントリーポイント
- `argparse`を使った引数パース（`--config`, `--builtin`オプション）
- stdin/stdoutでのJSON入出力処理
- エラーハンドリングと結果出力
- 全体の処理フロー統括

### `config.py` - 設定管理
- YAML設定ファイルの読み込み
- 組み込み設定（builtin_configs/）の読み込み
- jsonschemaによる設定バリデーション
- デフォルト値の適用

### `judge.py` - 判定ロジック
- Claude Agent SDKを使ったLLM判定の実行
- カスタムプロンプトの適用（SystemPromptPreset）
- リトライロジックとエラーハンドリング
- 出力のラッピングと検証

### `schema.py` - スキーマ定義とバリデーション
- PreToolUse入出力のJSON schema定義
- YAML設定ファイルのJSON schema定義
- jsonschemaを使った検証関数
- スキーマ検証エラーの処理

### `models.py` - データモデル
- TypedDictを使った型定義
- `ConfigDict`: YAML設定の型定義（prompt, model, allowed_tools）

### `constants.py` - 定数定義
- `HOOK_EVENT_NAME`, `PERMISSION_*`, `DEFAULT_*`
- リトライ回数やタイムアウト値

### `exceptions.py` - カスタム例外
- `JudgeError`: 基底例外クラス
- `InvalidJSONError`, `NoResponseError`, `SchemaValidationError`
- `ConfigError`: 設定読み込みエラー

### `builtin_configs/` - 組み込み設定
- BigQuery検証の設定（validate_bq_query.yaml）
- パッケージデータとして同梱（pyproject.tomlでforce-include）

## Naming Conventions

### Files
- **Modules**: `snake_case.py` (例: `config.py`, `judge.py`)
- **Tests**: `test_[module_name].py` (例: `test_judge.py`)
- **Builtin Configs**: `snake_case.yaml` (例: `validate_bq_query.yaml`)

### Code
- **Classes/Types**: `PascalCase` (例: `ConfigModel`, `ValidationResult`)
- **Functions/Methods**: `snake_case` (例: `load_config()`, `judge_command()`)
- **Constants**: `UPPER_SNAKE_CASE` (例: `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Variables**: `snake_case` (例: `tool_name`, `config_path`)
- **Private**: アンダースコアプレフィックス `_private_function()`

### Type Annotations
- **必須**: 全ての関数・メソッドに型アノテーション必須
- **禁止**: `Any`型の使用を禁止
- **例**:
  ```python
  def judge_command(command: str, config: ConfigModel) -> ValidationResult:
      ...
  ```

## Import Patterns

### Import Order（PEP 8準拠）
1. **標準ライブラリ**: `import json`, `import sys`
2. **サードパーティ**: `import yaml`, `from anthropic import Anthropic`
3. **ローカルモジュール**: `from config import load_config`

### 例
```python
# 標準ライブラリ
import json
import sys
from pathlib import Path
from typing import Dict, List

# サードパーティ
import yaml
from anthropic import Anthropic

# ローカルモジュール
from config import load_config
from models import ValidationResult
```

### Module Organization
- **絶対インポート**: パッケージルートからの絶対パス (`from config import ...`)
- **相対インポート禁止**: 明示性のため相対インポートは使用しない

## Code Structure Patterns

### Module Organization（ファイル内の構成）
1. **Docstring**: モジュールの説明
2. **Imports**: 上記の順序で
3. **Constants**: 定数定義
4. **Type Definitions**: TypeAlias、Protocol等
5. **Classes**: クラス定義
6. **Functions**: 関数定義
7. **Main Guard**: `if __name__ == "__main__":`

### 例
```python
"""Configuration loader for hook validator.

This module handles loading and validating YAML configuration files.
"""

# Imports
import yaml
from pathlib import Path
from typing import Dict, List

# Constants
DEFAULT_CONFIG_PATH: Path = Path("config.yaml")
MAX_FILE_SIZE: int = 1024 * 1024  # 1MB

# Type Definitions
ConfigDict = Dict[str, str]

# Classes
class ConfigLoader:
    ...

# Functions
def load_config(path: Path) -> ConfigDict:
    ...
```

### Function Organization
- **Docstring**: Google形式
- **引数バリデーション**: 最初に実行
- **メインロジック**: 中央に配置
- **エラーハンドリング**: 適切な箇所で例外処理
- **戻り値**: 明確な型で返す

### 例
```python
def judge_command(tool_name: str, command: str, config: ConfigModel) -> ValidationResult:
    """Judge a tool command using LLM judgment.

    Args:
        tool_name: Name of the tool (e.g., "Bash", "Write")
        command: Command string to validate
        config: Configuration model

    Returns:
        ValidationResult containing permission decision and reason

    Raises:
        ValueError: If tool_name is empty
        ConfigError: If config is invalid
    """
    # 引数バリデーション
    if not tool_name:
        raise ValueError("tool_name cannot be empty")

    # メインロジック
    matcher = find_matcher(tool_name, config)
    result = llm_judge(command, matcher.prompt)

    # 戻り値
    return ValidationResult(
        permission=result.permission,
        reason=result.reason
    )
```

## Code Organization Principles

1. **Single Responsibility**: 各モジュールは1つの責務のみ
   - `__main__.py` → CLIエントリーポイントと処理フロー統括
   - `config.py` → YAML設定読み込みとバリデーション
   - `judge.py` → LLM判定ロジックのみ
   - `schema.py` → JSON schema定義とバリデーション
   - `models.py` → 型定義のみ
   - `constants.py` → 定数定義のみ
   - `exceptions.py` → カスタム例外定義のみ

2. **Dependency Direction**: 依存関係は一方向
   ```
   __main__.py (CLI層)
     ↓
   judge.py (判定ロジック層 - LLM呼び出し含む)
     ↓
   Claude Agent SDK (外部依存)

   config.py (設定層) ← __main__.pyから参照
   schema.py (検証層) ← __main__.py, judge.pyから参照
   models.py (モデル層) ← 全ての層から参照可能
   constants.py (定数層) ← 全ての層から参照可能
   exceptions.py (例外層) ← 全ての層から参照可能
   ```

3. **Testability**: 全ての関数は単体でテスト可能
   - 外部依存はインジェクション可能
   - モック可能な設計

4. **Type Safety**: 型アノテーション必須
   - `mypy --strict`でエラーなし
   - `Any`型の使用禁止

## Module Boundaries

### Core vs Configuration
- **Core**: `judge.py`, `schema.py`
  - 判定ロジック（LLM呼び出し含む）
  - スキーマ定義
- **Configuration**: `config.py`
  - YAML読み込み
  - バリデーション
  - デフォルト値設定

### Public API vs Internal
- **Public API**: `__init__.py`でエクスポート
  - `judge()` 関数
  - `load_config()` 関数
  - `ValidationResult` クラス
- **Internal**: アンダースコアプレフィックス
  - `_parse_yaml()`
  - `_validate_schema()`

### Dependencies Direction
```
__main__.py (CLI層)
  ├→ config.py で設定読み込み
  ├→ schema.py で入出力検証
  └→ judge.py でLLM判定

judge.py (判定ロジック層)
  ├→ Claude Agent SDK でLLM判定
  └→ schema.py で出力検証

config.py (設定層)
  ├→ builtin_configs/ (組み込み設定)
  └→ schema.py で設定検証

models.py, constants.py, exceptions.py ← 全ての層から参照可能
```

## Code Size Guidelines

- **File size**: 最大500行（ただしテストは除外）
- **Function/Method size**: 最大50行（理想は20行以下）
- **Class complexity**: 最大15メソッド
- **Nesting depth**: 最大3レベル（if/for/whileのネスト）
- **Function arguments**: 最大5引数（それ以上は構造体化）

### 超過時の対応
- ファイルが500行超過 → モジュール分割
- 関数が50行超過 → サブ関数に分割
- ネストが3レベル超過 → Early returnやガード節使用

## Documentation Standards

### Docstring（Google形式）
```python
def function_name(arg1: str, arg2: int) -> bool:
    """Brief description of what this function does.

    More detailed explanation if needed. Can span multiple
    lines and include implementation details.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When arg1 is empty
        ConfigError: When configuration is invalid

    Example:
        >>> function_name("test", 42)
        True
    """
```

### README Standards
- プロジェクトルート: プロジェクト全体の説明
- 各サブディレクトリ: 必要に応じてREADME追加

### Inline Comments
- **Why（なぜ）を説明**: コードを見れば分かる「何」ではなく「なぜ」を記述
- **悪い例**: `# iを1増やす`
- **良い例**: `# リトライカウントを増やして次の試行へ`

## Testing Structure

### Test Organization
- テストファイルは`tests/`ディレクトリに配置
- モジュール構造を反映: `src/config.py` → `tests/test_config.py`
- Fixturesは`tests/fixtures/`に配置

### Test Naming
```python
class TestJudge:
    def test_judge_safe_command_returns_allow(self) -> None:
        """安全なコマンドに対してallowを返すことを確認"""
        ...

    def test_judge_dangerous_command_returns_deny(self) -> None:
        """危険なコマンドに対してdenyを返すことを確認"""
        ...
```

### Test Coverage
- **目標**: 80%以上
- **必須**: Public API全てカバー
- **推奨**: エッジケース・エラーケースもカバー

## Builtin Configs Management

### パッケージデータの同梱

`builtin_configs/`をパッケージデータとして同梱するため、`pyproject.toml`に設定：

```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.hatch.build.targets.wheel.force-include]
"builtin_configs" = "builtin_configs"
```

### 実行時の読み込み

```python
from pathlib import Path
import importlib.resources

# builtin_configs/validate_bq_query.yaml を読み込む
with importlib.resources.files('builtin_configs').joinpath('validate_bq_query.yaml').open() as f:
    config_data = f.read()
```

### ユーザー設定 vs 組み込み設定

- **ユーザー設定**: `--config path/to/config.yaml`で指定
- **組み込み設定**: `--builtin validate_bq_query`で指定（デフォルトでは読み込まれない）
- **デフォルト動作**: 設定未指定時はdeny-by-default設計で拒否
