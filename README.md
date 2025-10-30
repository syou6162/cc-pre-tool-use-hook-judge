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

## インストール

### 前提条件

- Python 3.11以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/cc-pre-tool-use-hook-judge.git
cd cc-pre-tool-use-hook-judge

# 依存関係のインストール
uv sync

# 開発用依存関係も含めてインストール
uv sync --all-groups
```

## 使い方

### Claude Codeフックとして使用

Claude Codeの設定ファイル（`.claude/hooks.json`）に以下を追加：

```json
{
  "hooks": [
    {
      "eventName": "PreToolUse",
      "command": "uv run cc-pre-tool-use-hook-judge"
    }
  ]
}
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

## 開発

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

## プロジェクト構造

```
cc-pre-tool-use-hook-judge/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # エントリーポイント（stdin/stdout処理）
│   ├── constants.py         # 定数定義
│   ├── exceptions.py        # カスタム例外クラス
│   ├── judge.py             # 判定ロジック（Claude Agent SDK）
│   └── schema.py            # JSON Schema定義と検証関数
├── tests/
│   ├── __init__.py
│   └── test_schema.py       # スキーマ検証のテスト
├── pyproject.toml           # プロジェクト設定
└── README.md
```

## 技術スタック

- **Python 3.11+**: 最新の型ヒント機能を活用
- **Claude Agent SDK**: 双方向会話による高度な判断
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
