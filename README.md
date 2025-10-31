# cc-pre-tool-use-hook-judge

Claude CodeのPreToolUseフック用のバリデーター・判定システム。Claude Agent SDKを使用して、ツール実行前に安全性を判断し、適切な許可決定を返します。

## 概要

このツールは、Claude Codeの[PreToolUseフック](https://docs.claude.com/en/docs/claude-code/hooks)として動作し、以下の機能を提供します：

- ツール実行前の安全性チェック
- Claude Agent SDKを使った高度な判断ロジック
- JSON Schemaによる入出力の厳密な検証
- リトライ機能付きのエラーハンドリング
- デフォルトでdenyの安全優先設計

## 特徴

- **型安全**: mypy strict モードでの完全な型チェック
- **スキーマ検証**: JSON Schemaによる入出力の厳密な検証
- **カスタム例外**: 型ベースのエラー分類で保守性向上
- **セキュリティ優先**: デフォルトで拒否、明示的な許可のみ通す設計
- **リトライロジック**: JSON解析やスキーマ検証失敗時の自動リトライ（最大3回）

## 使い方

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

**動作例:**

安全なクエリ（ALLOW）:
```bash
bq query "SELECT * FROM dataset.table LIMIT 100"
# → permissionDecision: "allow"
# → 理由: 純粋なSELECT、読み取り専用操作
```

危険なクエリ（DENY）:
```bash
bq query "DROP TABLE dataset.old_table"
# → permissionDecision: "deny"
# → 理由: DDL操作でデータを削除

bq query "INSERT INTO dataset.table VALUES (1, 'test')"
# → permissionDecision: "deny"
# → 理由: DML操作でデータを変更
```

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

**動作例:**

安全な設定（ALLOW）:
```python
# sandbox=read-only（または未指定）、cwdが未指定
mcp__codex__codex(prompt="テストを実行して")
# → permissionDecision: "allow"
# → 理由: 読み取り専用モードで安全

# approval-policy=untrusted
mcp__codex__codex(prompt="ファイルを作成して", sandbox="read-only", approval_policy="untrusted")
# → permissionDecision: "allow"
# → 理由: 承認ポリシーが適切
```

危険な設定（DENY）:
```python
# sandbox=danger-full-access
mcp__codex__codex(prompt="ファイルを削除して", sandbox="danger-full-access")
# → permissionDecision: "deny"
# → 理由: システム全体への書き込みが可能

# approval-policy=never
mcp__codex__codex(prompt="スクリプトを実行して", approval_policy="never")
# → permissionDecision: "deny"
# → 理由: 承認なしでコマンド実行

# cwd=別のディレクトリ
mcp__codex__codex(prompt="設定を変更して", cwd="/etc")
# → permissionDecision: "deny"
# → 理由: 意図しないディレクトリでの操作
```

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

**動作例:**

安全なpush（ALLOW）:
```bash
# 現在のブランチ（例: feature/new-feature）をpush
git push
# → permissionDecision: "allow"
# → 理由: 現在のブランチをpush

git push origin feature/new-feature
# → permissionDecision: "allow"
# → 理由: 現在のブランチと同じ名前のリモートブランチへのpush
```

危険なpush（DENY）:
```bash
git push origin main
# → permissionDecision: "deny"
# → 理由: mainブランチへのpushは禁止

git push origin master
# → permissionDecision: "deny"
# → 理由: masterブランチへのpushは禁止

git push --force origin feature/new-feature
# → permissionDecision: "deny"
# → 理由: force pushは禁止

git push -f origin feature/new-feature
# → permissionDecision: "deny"
# → 理由: force pushは禁止

git push origin HEAD
# → permissionDecision: "deny"
# → 理由: HEADの使用は禁止、明示的なブランチ名を指定してください
```

### cchookと組み合わせて使う（推奨）

[cchook](https://github.com/syou6162/cchook)を使うと、特定のコマンドのみをバリデートできます：

#### ビルトインBigQueryバリデータ

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

#### ビルトインCodex MCPバリデータ

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

#### カスタム設定ファイルの使用

外部YAML設定ファイルでカスタムプロンプトを指定できます：

```yaml
# custom_validator.yaml
prompt: |
  あなたはカスタムバリデーターです。
  独自のルールでツール使用を判定してください。
model: claude-sonnet-4-5
allowed_tools:
  - Bash
  - Read
```

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
        command: echo '{.}' | uvx --from git+https://github.com/syou6162/cc-pre-tool-use-hook-judge cc-pre-tool-use-hook-judge --config custom_validator.yaml
```

### 標準入出力での動作

```bash
# 標準入力からJSON入力を受け取り、標準出力にJSON結果を返す
echo '{"session_id":"test","hook_event_name":"PreToolUse","tool_name":"Write",...}' | uv run cc-pre-tool-use-hook-judge
```

### 入力スキーマ

```json
{
  "session_id": "string",
  "hook_event_name": "PreToolUse",
  "tool_name": "string",
  "tool_parameters": {},
  "message_history": []
}
```

### 出力スキーマ

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "string"
  },
  "updatedInput": {}
}
```

## 開発者向け情報

### インストール（ローカル開発用）

#### 前提条件

- Python 3.11以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー

#### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/cc-pre-tool-use-hook-judge.git
cd cc-pre-tool-use-hook-judge

# 依存関係のインストール
uv sync

# 開発用依存関係も含めてインストール
uv sync --all-groups
```

### テストの実行

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=src --cov-report=html

# 詳細モードで実行
uv run pytest -xvs
```

### 型チェック

```bash
uv run mypy src tests
```

### Linting

```bash
# チェックのみ
uv run ruff check src tests

# 自動修正
uv run ruff check --fix src tests

# フォーマット
uv run ruff format src tests
```

### Pre-commit hooks

```bash
# pre-commit hooksのインストール
uv run pre-commit install

# 全ファイルに対して実行
uv run pre-commit run --all-files
```

### プロジェクト構造

```
cc-pre-tool-use-hook-judge/
├── builtin_configs/
│   ├── validate_bq_query.yaml   # ビルトインBigQueryバリデータ設定
│   └── validate_codex_mcp.yaml  # ビルトインCodex MCPバリデータ設定
├── src/
│   ├── __init__.py
│   ├── __main__.py              # エントリーポイント（stdin/stdout、argparse）
│   ├── config.py                # YAML設定ローダー
│   ├── constants.py             # 定数定義
│   ├── exceptions.py            # カスタム例外クラス
│   ├── judge.py                 # 判定ロジック（Claude Agent SDK）
│   ├── models.py                # TypedDict型定義
│   └── schema.py                # JSON Schema定義と検証関数
├── tests/
│   ├── __init__.py
│   ├── test_config.py           # 設定ローダーのテスト
│   ├── test_models.py           # 型定義のテスト
│   └── test_schema.py           # スキーマ検証のテスト
├── pyproject.toml               # プロジェクト設定
└── README.md
```

### 技術スタック

- **Python 3.11+**: 最新の型ヒント機能を活用
- **Claude Agent SDK**: 双方向会話による高度な判断
- **PyYAML**: YAML設定ファイルの読み込み
- **jsonschema**: JSON Schemaベースの厳密な検証
- **pytest**: テストフレームワーク
- **mypy**: 静的型チェック（strict mode）
- **ruff**: 高速リンター・フォーマッター
- **uv**: 高速パッケージマネージャー

## ライセンス

MIT License

## 関連リンク

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [PreToolUse Hook Specification](https://docs.claude.com/en/docs/claude-code/hooks)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
