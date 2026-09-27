# nanicommit MCP連携 PoC

MCPを使ったアプリを作ることができるか確かめるためのリポジトリ

nanicommit設計書のうち **FastAPI（MCP Client）→ 問題生成MCP Server（`generate_quiz`）→ Google AI Studio（Gemini）** の部分だけを確認するアプリです。計画は [PLAN.md](PLAN.md) を参照してください。

```
ブラウザ ──D1 JSON──▶ FastAPI ──MCP(stdio)──▶ mcp_server/server.py ──▶ Gemini API
```

FastAPIはGeminiを直接呼びません。APIキーはMCP Serverプロセスにだけ渡します。

## 起動

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # GEMINI_API_KEY を記入
uvicorn app.main:app --reload
```

http://localhost:8000 を開き、入力欄のD1 JSON（設計書のサンプル入り）をそのまま「送信」します。

APIキーなしでMCPの疎通だけを見る場合は、`.env` を `QUIZ_GENERATOR=fake` にします（MCP Serverが固定の3問を返します）。

## 返答

| HTTP | 内容 |
| --- | --- |
| 200 | `status: "ok"`。`result.questions` にD2形式の3問、`elapsed_ms` に所要時間、`mcp_arguments` にMCPへ渡したarguments |
| 422 | D1の形式不正、または根拠不足で問題を作れない |
| 502 | MCP Serverの返却データが形式不正（`validation_errors` に理由）、またはGemini APIのエラー（APIキー不正など） |
| 503 | MCP Serverを起動・接続できない |
| 504 | `MCP_TIMEOUT_SEC` を超えた |

形式チェックの内容：3問であること、選択肢が4つで重複・空文字がないこと、`correct_index` が0〜3であること、question・hint・explanationが空でないこと。

## MCP Server単体での確認

```bash
npx @modelcontextprotocol/inspector .venv/bin/python mcp_server/server.py
```

## テスト

```bash
pytest
```

Geminiを呼ばずに（fakeモード）、FastAPI → MCP Client → MCP Server（stdio）の経路と形式チェックを確認します。
