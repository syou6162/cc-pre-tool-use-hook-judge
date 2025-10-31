# Claude Code開発ガイド - cc-pre-tool-use-hook-judge

このファイルは、Claude Codeがこのプロジェクトを開発・保守する際に参照する情報をまとめています。

## プロジェクト概要

### 目的

Claude CodeのPreToolUseフック用のバリデーター・判定システム。ツール実行前に、Claude Agent SDKを使って安全性を判断し、適切な許可決定（allow/deny/ask）を返します。

### 設計思想

1. **セキュリティ優先**: デフォルトでdeny、明示的な許可のみ通す
2. **型安全**: mypy strict modeで完全な型チェック
3. **関心の分離**: 入力処理、検証、判定ロジックを明確に分離
4. **DRY原則**: partial関数やカスタム例外で重複を排除
5. **テスト可能性**: 純粋関数とSDK依存部分を分離

## 使用例

### Claude Codeのデフォルトフックとして使う

GitHubリポジトリから直接実行する最もシンプルな方法です：

#### BigQueryバリデータ

```json
# .claude/hooks.json
{
  "hooks": [
    {
      "eventName": "PreToolUse",
      "command": "uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_bq_query"
    }
  ]
}
```

この設定では、全てのツール実行前にBigQueryバリデータが動作します。

#### Codex MCPバリデータ

```json
# .claude/hooks.json
{
  "hooks": [
    {
      "eventName": "PreToolUse",
      "command": "uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_codex_mcp"
    }
  ]
}
```

この設定では、MCP経由でCodexツールを実行する際の安全性をチェックします。

#### Git Pushバリデータ

```json
# .claude/hooks.json
{
  "hooks": [
    {
      "eventName": "PreToolUse",
      "command": "uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_git_push"
    }
  ]
}
```

この設定では、全てのツール実行前にGit pushバリデータが動作します。

### cchookと組み合わせて使う（推奨）

[cchook](https://github.com/syou6162/cchook)と組み合わせることで、特定のコマンドのみをバリデートできます：

#### BigQueryバリデータ

```yaml
# .cchook/config.yaml
preToolUse:
  - matcher: "Bash"
    conditions:
      - type: command_starts_with
        value: "bq query"
    actions:
      - type: command
        exit_status: 0 # JSON Outputで制御するので、exit_statusはこれでよい
        command: echo '{.}' | uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_bq_query
```

この設定により、`bq query`コマンドのみがバリデーションの対象になります。

#### Codex MCPバリデータ

```yaml
# .cchook/config.yaml
preToolUse:
  - matcher: "mcp__codex__codex"
    actions:
      - type: command
        exit_status: 0 # JSON Outputで制御するので、exit_statusはこれでよい
        command: echo '{.}' | uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_codex_mcp
```

この設定により、MCP Codexツールの実行時のみがバリデーションの対象になります。

#### Git Pushバリデータ

```yaml
# .cchook/config.yaml
preToolUse:
  - matcher: "Bash"
    conditions:
      - type: command_starts_with
        value: "git push"
    actions:
      - type: command
        exit_status: 0 # JSON Outputで制御するので、exit_statusはこれでよい
        command: echo '{.}' | uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --builtin validate_git_push
```

この設定により、`git push`コマンドのみがバリデーションの対象になります。

## アーキテクチャ

### データフロー

```
stdin (JSON)
  ↓
__main__.py (入力処理・例外ハンドリング)
  ↓
schema.py (入力検証)
  ↓
judge.py (Claude Agent SDK による判定)
  ↓
schema.py (出力検証)
  ↓
__main__.py (出力処理)
  ↓
stdout (JSON)
```

### 主要コンポーネント

#### 1. `src/__main__.py`
- **役割**: エントリーポイント、CLI引数解析、stdin/stdout処理、例外ハンドリング
- **責務**:
  - コマンドライン引数の解析（`--config`、`--builtin`）
  - 設定ファイルの読み込み
  - 標準入力からJSON読み取り
  - JSON parsingと入力検証の呼び出し
  - カスタムプロンプトを指定して判定ロジックを実行
  - エラー時の適切なJSON出力（deny決定）
  - 標準出力へのJSON書き込み
- **注意点**:
  - 全ての出力は**stdout**に出力する（Claude Code hook仕様）
  - stderrは使わない
  - `sys.exit(1)`は使わない（exit code 0で正常終了）
  - `--config`と`--builtin`は相互排他（両方指定不可）

#### 2. `src/schema.py`
- **役割**: JSON Schema定義と検証ロジック
- **責務**:
  - PreToolUse入力スキーマの定義
  - PreToolUse出力スキーマの定義
  - スキーマ検証関数の提供
- **設計**:
  - `_validate_with_schema()`: 内部ヘルパー関数
  - `validate_pretooluse_input`/`validate_pretooluse_output`: partial関数でスキーマを固定
  - 入力は`dict[str, Any]`（JSON stringではない）
  - 検証失敗時は`ValueError`を送出

#### 3. `src/judge.py`
- **役割**: Claude Agent SDKを使った判定ロジック
- **責務**:
  - カスタムプロンプトの処理（SystemPromptPreset切り替え）
  - Claude Agent SDKとの双方向会話
  - リトライロジック（最大3回）
  - JSON解析エラー・スキーマ検証エラーのハンドリング
  - 出力データのラッピング（hookSpecificOutput形式）
- **主要関数**:
  - `judge_pretooluse(input_data, prompt)`: 同期版エントリーポイント（anyio.run()のラッパー）
  - `judge_pretooluse_async(input_data, prompt)`: 非同期版メインロジック（リトライループ）
  - `_receive_text_response()`: Claude Agent SDKからのテキスト受信
  - `_wrap_output_if_needed()`: 出力データのラッピング
- **SystemPromptPreset**:
  - カスタムプロンプト（YAML設定ファイルから読み込み）をClaude Codeシステムプロンプトに追加: `{"type": "preset", "preset": "claude_code", "append": prompt}`
  - promptパラメータは必須（YAML設定のpromptフィールドも必須）
- **注意点**:
  - テストが難しい（SDK依存が強い、モックが複雑）
  - リトライ時はSDKの会話機能を使ってエラー内容を伝える

#### 4. `src/exceptions.py`
- **役割**: カスタム例外クラスの定義
- **設計**:
  - `JudgeError`: 基底例外クラス
  - `InvalidJSONError`: JSON parsing失敗
  - `NoResponseError`: SDKから応答なし
  - `SchemaValidationError`: スキーマ検証失敗
- **メリット**: 文字列パターンマッチングではなく型ベースのエラー分類が可能

#### 4. `src/config.py`
- **役割**: YAML設定ファイルの読み込みと検証
- **責務**:
  - ビルトイン設定の読み込み（`builtin_configs/`ディレクトリから）
  - 外部設定ファイルの読み込み（`--config`オプションで指定）
  - YAML構文エラーのハンドリング
  - スキーマ検証（`schema.py`を使用）
- **主要関数**:
  - `load_builtin_config(name: str) -> ConfigDict`: ビルトイン設定読み込み
  - `load_config(path: Path) -> ConfigDict`: 外部設定読み込み
- **例外**:
  - `ConfigError`: 設定ファイル読み込み・検証失敗時
- **注意点**:
  - `importlib.resources`を使ってパッケージ内のビルトイン設定にアクセス

#### 5. `src/models.py`
- **役割**: TypedDict型定義
- **型定義**:
  - `ConfigDict`: YAML設定構造
    - `prompt`: str（必須）
    - `model`: NotRequired[str]（オプション）
    - `allowed_tools`: NotRequired[list[str]]（オプション）

#### 6. `src/exceptions.py`
- **役割**: カスタム例外クラスの定義
- **設計**:
  - `JudgeError`: 基底例外クラス
  - `InvalidJSONError`: JSON parsing失敗
  - `NoResponseError`: SDKから応答なし
  - `SchemaValidationError`: スキーマ検証失敗
  - `ConfigError`: 設定ファイル読み込み失敗
- **メリット**: 文字列パターンマッチングではなく型ベースのエラー分類が可能

#### 7. `src/constants.py`
- **役割**: アプリケーション全体で使用する定数の一元管理
- **定数**:
  - `HOOK_EVENT_NAME`: "PreToolUse"
  - `PERMISSION_ALLOW/DENY/ASK`: 許可決定の値
  - `DEFAULT_PERMISSION_DECISION`: "deny"（セキュリティ優先）
  - `DEFAULT_PERMISSION_REASON`: デフォルトエラーメッセージ
  - `MAX_RETRY_ATTEMPTS`: 3

#### 8. `builtin_configs/validate_bq_query.yaml`
- **役割**: BigQueryクエリバリデータのビルトイン設定
- **内容**:
  - BigQueryクエリの安全性判定ルール
  - 安全な操作（SELECT、INFORMATION_SCHEMA、WITH）
  - 危険な操作（DDL、DML、DCL、BigQuery ML、危険なオプション）
- **使用方法**: `--builtin validate_bq_query`で指定

#### 9. `builtin_configs/validate_codex_mcp.yaml`
- **役割**: Codex MCPバリデータのビルトイン設定
- **内容**:
  - MCP経由でCodexツールを実行する際の安全性判定ルール
  - 安全な設定（read-only sandbox、適切なapproval-policy）
  - 危険な設定（danger-full-access、approval-policy=never、別ディレクトリでの実行）
- **使用方法**: `--builtin validate_codex_mcp`で指定

#### 10. `builtin_configs/validate_git_push.yaml`
- **役割**: Git Pushバリデータのビルトイン設定
- **内容**:
  - git pushコマンドの安全性判定ルール
  - 安全な操作（現在のブランチと同じ名前のリモートブランチへのpush）
  - 危険な操作（main/masterブランチへのpush、force push、HEADの使用）
  - Bashツールを使用して現在のブランチ名を確認
- **使用方法**: `--builtin validate_git_push`で指定

## コーディング規約

### 型アノテーション
- **全ての関数に型ヒントを付ける**
- mypy strict modeで型チェックをパスすること
- `dict[str, Any]`など、Python 3.11+の新しい型ヒント構文を使用

### 関数設計
- **単一責任の原則**: 1つの関数は1つの責務のみ
- **純粋関数を優先**: 外部依存が少ない関数は単体テスト可能
- **長い関数は分割**: 目安として30-40行以上なら分割を検討

### 例外処理
- **カスタム例外を使用**: ValueError等の汎用例外より、具体的な例外クラスを使う
- **例外チェーン**: `raise NewError(...) from e`で元の例外を保持
- **型ベースの分類**: 文字列パターンマッチングではなく例外型で分岐

### 定数
- **マジック文字列/数値禁止**: 全て`constants.py`で定義
- **命名規約**: `UPPER_SNAKE_CASE`

### テスト
- **純粋関数は必ずテスト**: `schema.py`の検証関数など
- **SDK依存部分はテスト不要**: `judge.py`の大部分（モックが複雑すぎる）
- **簡単な辞書操作のみの関数はテスト不要**: `_wrap_output_if_needed`など

## YAML設定形式

### 設定ファイル構造

```yaml
prompt: |
  あなたのカスタムプロンプトをここに書く。
  複数行可能。
model: claude-sonnet-4-5  # オプション
allowed_tools:            # オプション
  - Bash
  - Read
  - Write
```

### フィールド説明

- **prompt** (必須): カスタムプロンプト文字列
  - Claude Agent SDKに渡される追加プロンプト
  - SystemPromptPresetの`append`フィールドに設定される
- **model** (オプション): 使用するClaudeモデル
  - 指定可能な値: `claude-sonnet-4-5`, `claude-opus-4-1`, `sonnet`, `opus`, `haiku`, など
- **allowed_tools** (オプション): 許可するツールのリスト
  - 現在未使用（将来の拡張用）

### カスタム設定の作成例

```yaml
# custom_validator.yaml
prompt: |
  あなたはセキュリティ専門家です。
  危険な操作を見抜いて拒否してください。
model: sonnet
```

使用方法:
```bash
uv run cc-pre-tool-use-hook-judge --config custom_validator.yaml
```

## ファイル構造詳細

```
cc-pre-tool-use-hook-judge/
├── builtin_configs/
│   ├── validate_bq_query.yaml   # BigQueryバリデータ設定
│   ├── validate_codex_mcp.yaml  # Codex MCPバリデータ設定
│   └── validate_git_push.yaml   # Git Pushバリデータ設定
├── src/
│   ├── __init__.py              # 空
│   ├── __main__.py              # main()関数、CLIエントリーポイント
│   ├── config.py                # YAML設定ローダー
│   ├── constants.py             # 定数定義
│   ├── exceptions.py            # カスタム例外クラス
│   ├── judge.py                 # Claude Agent SDK判定ロジック
│   ├── models.py                # TypedDict型定義
│   └── schema.py                # JSON Schema定義と検証
├── tests/
│   ├── __init__.py              # 空
│   ├── test_config.py           # config.pyの単体テスト
│   ├── test_models.py           # models.pyの型テスト
│   └── test_schema.py           # schema.pyの単体テスト
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI設定
├── .pre-commit-config.yaml      # pre-commit hooks設定
├── pyproject.toml               # プロジェクト設定、依存関係
├── uv.lock                      # uvロックファイル
├── renovate.json                # Renovate Bot設定
├── LICENSE                      # MITライセンス
├── README.md                    # ユーザー向けドキュメント
└── CLAUDE.md                    # このファイル（開発ガイド）
```

## 開発ワークフロー

### 新機能の追加
1. 必要に応じて`constants.py`に定数を追加
2. 必要に応じて`exceptions.py`にカスタム例外を追加
3. 純粋関数の実装 → テストを先に書く（TDD）
4. SDK依存の実装 → テストは不要
5. mypy/ruff/pytestが全て通ることを確認
6. pre-commit hooksが通ることを確認

### リファクタリング時の注意点
- **段階的に進める**: 1つの変更ごとにテストを実行
- **テストを先に修正**: 関数シグネチャを変える場合はテストも同時に修正
- **コミットを細かく**: 意味のある単位でコミット

### CI/CD
- GitHub Actionsで自動実行:
  - pytest（全テスト）
  - mypy（型チェック）
  - ruff（linting）
- pre-commit hooksでローカルでも同じチェック

## 技術的な判断・履歴

### なぜpartial関数を使うのか？
- `validate_pretooluse_input`と`validate_pretooluse_output`はほぼ同じコード
- スキーマだけが異なる
- partial関数でスキーマを固定することでDRY化

### なぜ入力を`str`から`dict`に変えたのか？
- JSON parsingと検証は別の責務
- `__main__.py`でparsing、`schema.py`で検証と分離
- テストが書きやすい（`json.dumps()`不要）

### なぜデフォルトを"deny"にしたのか？
- セキュリティ優先の設計
- エラー時・不明時は拒否が安全
- 明示的な許可のみ通す

### なぜカスタム例外クラスを導入したのか？
- 文字列パターンマッチング（`"Failed to parse" in str(e)`）はメンテナンスしづらい
- 型ベースのエラー分類の方が保守性が高い
- エラーメッセージが変わってもコードが壊れない

### なぜjudge.pyのテストを書かないのか？
- Claude Agent SDK依存が強い
- モックが複雑すぎてテストの価値が低い
- 純粋関数（`_wrap_output_if_needed`）は単純すぎてテスト不要

## よくある操作

### 依存関係の追加
```bash
# 本番依存関係
uv add パッケージ名

# 開発依存関係
uv add --dev パッケージ名
```

### テストの実行
```bash
# 全テスト
uv run pytest

# 特定のテストファイル
uv run pytest tests/test_schema.py

# 特定のテストケース
uv run pytest tests/test_schema.py::TestPreToolUseInputValidation::test_valid_pretooluse_input

# カバレッジ確認
uv run pytest --cov=src --cov-report=term-missing
```

### 型チェック・Linting
```bash
# 型チェック
uv run mypy src tests

# Linting
uv run ruff check src tests

# 自動修正
uv run ruff check --fix src tests

# フォーマット
uv run ruff format src tests
```

## トラブルシューティング

### 設定ファイルエラー

**症状**: `ConfigError: Builtin config '...' not found`
- **原因**: 指定したビルトイン設定名が存在しない
- **解決**: `builtin_configs/`ディレクトリ内のYAMLファイル名を確認

**症状**: `ConfigError: Validation failed for config file`
- **原因**: YAML設定がスキーマに従っていない
- **解決**: 必須フィールド（`prompt`）があるか確認、モデル名が正しいか確認

**症状**: `ConfigError: Failed to parse config file`
- **原因**: YAML構文エラー
- **解決**: YAMLのインデントや引用符を確認

### Claude Codeフックが動かない
- 出力が**stdout**に出ているか確認（stderrではない）
- JSON形式が正しいか確認
- exit codeが0か確認（`sys.exit(1)`は使わない）
- `--config`と`--builtin`を同時指定していないか確認

### テストが失敗する
- `uv sync --all-groups`で依存関係を再インストール
- `.venv`を削除して再作成

### mypy/ruffエラー
- `uv run mypy src tests --show-error-codes`でエラーコード確認
- `uv run ruff check src tests --fix`で自動修正

## 参考リンク

- [Claude Code Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [JSON Schema](https://json-schema.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
