# Technology Stack

## Project Type

CLIツール - Claude CodeのPreToolUseフックから呼び出され、ツール実行の安全性を判定してJSON形式で結果を返すコマンドラインツール。

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.11以上
- **パッケージ管理**: uv（高速なPythonパッケージマネージャー）
- **理由**:
  - Claude Agent SDKがPythonをサポート
  - uvによる高速な依存関係解決とプロジェクト管理
  - YAMLやJSON処理が標準的

### Key Dependencies/Libraries
- **Claude Agent SDK**: LLMベースの判定ロジック実装のためのSDK
- **PyYAML**: YAML設定ファイルの読み込み
- **jsonschema**: JSON schema検証（標準的なライブラリで依存を最小化）

### Application Architecture

**シンプルなパイプラインアーキテクチャ**:
```
入力（Claude Code PreToolUseフックからの環境変数/args）
  → YAML設定読み込み
  → ツール/コマンドマッチング
  → LLM判定（Claude Agent SDK）
  → JSON出力（stdout、PreToolUse標準形式）
```

- **単発実行**: 長時間稼働するデーモンではなく、呼び出しごとに起動・終了
- **ステートレス**: 実行間で状態を保持しない
- **設定駆動**: ロジックはYAML設定ファイルで定義

### Data Storage (if applicable)
- **Primary storage**: なし（ステートレス）
- **Caching**: なし（毎回新規判定）
- **Data formats**:
  - 入力: YAML（設定）、JSON（ツールパラメータ）
  - 出力: JSON（PreToolUse標準形式）

### External Integrations (if applicable)
- **APIs**: Claude API（Agent SDK経由）
- **Protocols**: HTTPS
- **Authentication**: Anthropic APIキー（環境変数 `ANTHROPIC_API_KEY`）

### Monitoring & Dashboard Technologies (if applicable)
ダッシュボードは不要。ログは標準エラー出力に記録。

## Development Environment

### Build & Development Tools
- **Build System**: uv（依存関係管理とビルド）
- **Package Management**: uv
- **Development workflow**:
  - `uv run` で開発時実行
  - `uv sync` で依存関係同期
- **Production usage**:
  - `uv tool run --from git+https://github.com/[user]/[repo] <コマンド>` でユーザーが実行
  - または短縮形: `uvx --from git+https://github.com/[user]/[repo] <コマンド>`
  - 例: `uvx --from git+https://github.com/syou6162/hook-validator validate`

### Code Quality Tools
- **Static Analysis**: ruff（lintとフォーマット統合ツール）
- **Formatting**: ruff format
- **Testing Framework**: pytest
- **Type Checking**: mypy（タイプアノテーション必須、`Any`型は禁止）
- **Documentation**: docstring（Google形式）
- **Type Safety Policy**:
  - 全ての関数・メソッドに型アノテーション必須
  - `Any`型の使用を禁止（mypyの`--disallow-any-expr`相当）
  - 型チェックエラーは全て解消が必須

### Version Control & Collaboration
- **VCS**: Git
- **Branching Strategy**: GitHub Flow
- **Code Review Process**: Pull Requestベース

### Dashboard Development (if applicable)
該当なし（CLIツールのため）

## Deployment & Distribution (if applicable)
- **Target Platform(s)**: macOS、Linux（uvがサポートする環境）
- **Distribution Method**:
  - GitHubリポジトリから直接実行（PyPI公開予定なし）
  - `uv tool run --from git+https://github.com/[user]/[repo] <コマンド>` で実行
  - または短縮形: `uvx --from git+https://github.com/[user]/[repo] <コマンド>`
  - ローカル開発: `uv run` で実行
- **Installation Requirements**:
  - Python 3.11以上
  - uv
  - Anthropic APIキー
- **Update Mechanism**: Gitリポジトリのpullまたは再実行で最新版を取得

## Technical Requirements & Constraints

### Performance Requirements
- **応答速度**: フック判定の応答時間 2秒以内（目標）
- **起動時間**: コールドスタート 500ms以内
- **メモリ使用量**: 50MB以下（通常実行時）
- **理由**: フック実行はユーザー体験に直結するため、レスポンスが重要

### Compatibility Requirements
- **Platform Support**: macOS、Linux（uvサポート範囲）
- **Python Version**: 3.11以上
- **Standards Compliance**:
  - Claude Code PreToolUse JSONフォーマット仕様
  - [PreToolUseフック公式ドキュメント](https://docs.claude.com/en/docs/claude-code/hooks#pretooluse-decision-control)準拠

### Security & Compliance
- **Security Requirements**:
  - APIキーは環境変数で管理（コード内にハードコードしない）
  - YAML設定ファイルの検証（悪意ある設定を防ぐ）
  - 実行されるコマンドはLLMに送信（ログに注意）
- **Threat Model**:
  - YAML injection攻撃への対策（jsonschemaでスキーマ検証）
  - 過度なAPI呼び出しによるコスト増加（レート制限考慮）

### Scalability & Reliability
- **Expected Load**: 単一ユーザー環境、1日数十〜数百回の実行
- **Availability Requirements**: APIダウン時のフォールバック動作（deny判定）
- **Growth Projections**: チーム利用時は各ユーザーが個別に実行

## Technical Decisions & Rationale

### Decision Log

1. **Python + uv**:
   - **理由**: Claude Agent SDKがPython対応、uvの高速性と開発体験
   - **代替案**: Node.js（検討したがAgent SDKの成熟度でPython選択）
   - **トレードオフ**: Pythonランタイムが必要だが、uvで環境構築は簡素化

2. **ステートレス設計**:
   - **理由**: フック実行は独立した判定であり、状態管理不要
   - **メリット**: シンプルさ、並行実行の安全性
   - **デメリット**: 統計情報の蓄積には別機構が必要（将来課題）

3. **YAML設定**:
   - **理由**: 可読性が高く、プロンプトなど複数行テキストの記述が容易
   - **代替案**: TOML（検討したがYAMLの柔軟性を優先）
   - **トレードオフ**: パース速度はTOMLより遅いが、利便性を重視

4. **LLMベース判定**:
   - **理由**: 正規表現では検出困難な複雑パターン（オプション組み合わせなど）に対応
   - **コスト**: API呼び出しコストが発生
   - **対策**: キャッシュ機構は将来検討（現時点は単純性を優先）

5. **jsonschema for validation**:
   - **理由**: 標準的なJSON schema検証ライブラリで依存を最小化
   - **代替案**: pydantic（検討したが依存を減らすため標準的なライブラリを選択）
   - **メリット**: YAML設定の誤りを早期検出、軽量

6. **argparseで引数パース**:
   - **理由**: Python標準ライブラリで外部依存なし
   - **代替案**: click（検討したがシンプルなCLIには不要）
   - **メリット**: 依存ゼロ、学習コスト低い

## Known Limitations

- **API依存**: Claude APIがダウンすると判定不可（フォールバック動作でdeny返却）
- **レスポンス時間**: LLM呼び出しのため、完全なリアルタイム性は保証できない
- **コスト**: 頻繁な実行でAPI利用料が増加する可能性（利用者が管理）
- **オフライン実行不可**: インターネット接続必須
- **統計情報なし**: 現バージョンでは判定履歴を保存しない（将来機能として検討）
