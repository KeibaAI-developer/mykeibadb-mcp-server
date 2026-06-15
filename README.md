# mykeibadb-mcp-server

**Claudeに話しかけるだけで、JRA-VAN DataLabの競馬データを自然言語で分析できます。**

SQLを書く必要はありません。日本語で質問すれば、過去のレース結果・騎手成績・種牡馬傾向・枠番成績など、あらゆる競馬データを調べられます。

## こんな質問ができます

- 1番人気の勝率・複勝率を教えて
- 今年の東京芝1600mで成績が良い騎手は？
- ディープインパクト産駒の距離別成績は？
- 内枠と外枠、どちらが有利なコースは？
- アーモンドアイの戦績を一覧で見せて
- G1で1番人気が飛んだレースを調べて

---

## 前提条件

- **JRA-VAN DataLab** の契約とデータ取得済みのPostgreSQLが必要です
- **mykeibadb-python**（データアクセスライブラリ）がインストール済みであること
- Python 3.12 以上 / [uv](https://github.com/astral-sh/uv) がインストール済みであること

---

## セットアップ

### Step 1: リポジトリをクローン

```bash
git clone https://github.com/KeibaAI-developer/mykeibadb-mcp-server.git
cd mykeibadb-mcp-server
```

### Step 2: 依存パッケージをインストール

```bash
uv sync
```

### Step 3: 環境変数を設定

`.env.example` をコピーして `.env` を作成し、PostgreSQLの接続情報を記入します。

```bash
cp .env.example .env
```

```
MYKEIBADB_HOST=localhost
MYKEIBADB_PORT=5432
MYKEIBADB_DATABASE=mykeibadb
MYKEIBADB_USER=postgres
MYKEIBADB_PASSWORD=your_password
```

### Step 4: 動作確認

```bash
uv run python -m mykeibadb_mcp_server.server
```

DB接続に成功すると MCPサーバーが stdio モードで起動します。接続失敗時はエラーで終了します。

---

## MCPクライアント別セットアップ

### Claude Desktop

`claude_desktop_config.json` に追加します。

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mykeibadb": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/mykeibadb-mcp-server",
        "python", "-m", "mykeibadb_mcp_server.server"
      ],
      "env": {
        "MYKEIBADB_HOST": "localhost",
        "MYKEIBADB_PORT": "5432",
        "MYKEIBADB_DATABASE": "mykeibadb",
        "MYKEIBADB_USER": "postgres",
        "MYKEIBADB_PASSWORD": "your_password"
      }
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add mykeibadb \
  -e MYKEIBADB_HOST=localhost \
  -e MYKEIBADB_PORT=5432 \
  -e MYKEIBADB_DATABASE=mykeibadb \
  -e MYKEIBADB_USER=postgres \
  -e MYKEIBADB_PASSWORD=your_password \
  -- uv run --directory /path/to/mykeibadb-mcp-server python -m mykeibadb_mcp_server.server
```

プロジェクトスコープに追加する場合は `-s project` を付けてください。

### Cursor

プロジェクトルートに `.cursor/mcp.json` を作成します。

```json
{
  "mcpServers": {
    "mykeibadb": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/mykeibadb-mcp-server",
        "python", "-m", "mykeibadb_mcp_server.server"
      ],
      "env": {
        "MYKEIBADB_HOST": "localhost",
        "MYKEIBADB_PORT": "5432",
        "MYKEIBADB_DATABASE": "mykeibadb",
        "MYKEIBADB_USER": "postgres",
        "MYKEIBADB_PASSWORD": "your_password"
      }
    }
  }
}
```

### VS Code + GitHub Copilot

`.vscode/mcp.json` を作成します。

```json
{
  "servers": {
    "mykeibadb": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/mykeibadb-mcp-server",
        "python", "-m", "mykeibadb_mcp_server.server"
      ],
      "env": {
        "MYKEIBADB_HOST": "localhost",
        "MYKEIBADB_PORT": "5432",
        "MYKEIBADB_DATABASE": "mykeibadb",
        "MYKEIBADB_USER": "postgres",
        "MYKEIBADB_PASSWORD": "your_password"
      }
    }
  }
}
```

VS Code の設定で `"chat.mcp.enabled": true` を有効にしてください。

---

## SSEモードで起動する場合

HTTP/SSE トランスポートで起動したい場合は `--sse` フラグを使います。

```bash
uv run python -m mykeibadb_mcp_server.server --sse
```

| 環境変数 | デフォルト | 説明 |
|---------|-----------|------|
| `MCP_HOST` | `127.0.0.1` | バインドするホスト |
| `MCP_PORT` | `8000` | バインドするポート |

---

## 利用可能なツール

### 集計API（よく使う質問向け）

| ツール名 | 説明 | 主なパラメータ |
|---------|------|--------------|
| `tool_analyze_chakudo` | 馬×レースを条件で絞り込み、指定軸でグループ別の着度数・勝率・複勝率・回収率を集計 | `filters`, `condition`, `group_by` |
| `tool_get_uma_rekisen` | 馬名で過去の戦績一覧を取得 | `uma_name`, `year_from` |

### 汎用クエリ

| ツール名 | 説明 |
|---------|------|
| `execute_query` | 任意のSELECT文を実行（最大200行） |
| `get_table_data` | テーブルをフィルタ・期間指定で取得 |

### スキーマ探索

| ツール名 | 説明 |
|---------|------|
| `list_tables` | 利用可能な全63テーブルの一覧を取得 |
| `get_table_info` | テーブルのカラム定義・説明・エンコーディング情報を取得 |
| `get_sql_generation_prompt` | SQL生成用のスキーマ情報・コード表を取得 |
| `get_table_sample_data` | テーブルのサンプルデータを取得（デフォルト5行） |
| `get_column_examples` | カラムの実際の値例（DISTINCT）を取得 |

---

## 主要なコード値

競馬場コードやグレードコードを質問に含めると、より精度の高い絞り込みができます。

### 競馬場コード

| コード | 競馬場 | コード | 競馬場 |
|--------|--------|--------|--------|
| `01` | 札幌 | `06` | 中山 |
| `02` | 函館 | `07` | 中京 |
| `03` | 福島 | `08` | 京都 |
| `04` | 新潟 | `09` | 阪神 |
| `05` | 東京 | `10` | 小倉 |

### グレードコード

| コード | グレード |
|--------|--------|
| `A` | GI |
| `B` | GII |
| `C` | GIII |
| `L` | Listed |
| `_` または空白 | 一般競走 |

---

## 使い方のコツ

| コツ | 説明 |
|-----|------|
| **気軽に質問** | 思いついたことをそのまま聞いてみてください |
| **条件を追加** | 「東京の」「芝の」「1600mの」「2020年以降の」など条件を絞ると精度が上がります |
| **比較を依頼** | 「AとBを比較して」「年度別の推移を見せて」も対応できます |
| **深掘りする** | 回答を見て気になったら続けて質問できます |

---

## トラブルシューティング

### サーバーが起動しない

1. `uv` がインストールされているか確認: `uv --version`
2. `.env` の接続情報が正しいか確認
3. mykeibadb-python がインストールされているか確認: `uv run python -c "import mykeibadb"`
4. 依存関係を再インストール: `uv sync`

### DB接続エラーが出る

1. PostgreSQL が起動しているか確認
2. `.env` のホスト・ポート・ユーザー・パスワードが正しいか確認
3. 手動接続で確認: `psql -h localhost -U postgres -d mykeibadb`

### データが取得できない

1. `list_tables` ツールで対象テーブルが存在するか確認
2. `get_table_sample_data` でデータが入っているか確認
3. MCPクライアントのログでエラーメッセージを確認

---

## JRA-VANデータの利用について

本サーバーで分析するデータは [JRA-VAN](https://jra-van.jp/) から提供されるものです。

- データの再配布・第三者への提供・データベースファイルの共有は禁止されています
- 個人的な競馬分析・研究、自社内での利用は許可されています

詳細は [JRA-VAN利用規約](https://jra-van.jp/info/rule.html) をご確認ください。

---

## ライセンス

MIT License
