"""問題生成MCP Serverへの接続（stdio）。

リクエストごとにMCP Serverを子プロセスとして起動し、generate_quizを呼ぶ。
"""

import json
import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.schemas import QuizArguments

ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = ROOT / "mcp_server" / "server.py"
INSUFFICIENT_PREFIX = "INSUFFICIENT_EVIDENCE:"
# MCP Serverへ引き継ぐ環境変数。FastAPI側の他の秘密情報は渡さない。
FORWARDED_ENV = (
    "GEMINI_API_KEY", "GEMINI_MODEL", "QUIZ_GENERATOR",
    "PATH", "HOME", "SYSTEMROOT",
    "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR",
)


class GenerationError(Exception):
    """問題生成の失敗。status_codeは設計書の共通エラーに対応する。"""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _server_params() -> StdioServerParameters:
    env = {k: os.environ[k] for k in FORWARDED_ENV if k in os.environ}
    return StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)], env=env, cwd=str(ROOT))


async def call_generate_quiz(arguments: QuizArguments, timeout_sec: float) -> object:
    """generate_quizを呼び、toolの結果（未検証のJSON）を返す。"""
    try:
        with anyio.fail_after(timeout_sec):
            async with stdio_client(_server_params()) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("generate_quiz", arguments.model_dump())
    except TimeoutError as e:
        raise GenerationError(504, f"MCP generate_quiz timed out after {timeout_sec}s") from e
    except GenerationError:
        raise
    except Exception as e:  # 起動失敗・接続断など
        raise GenerationError(503, f"MCP server unavailable: {type(e).__name__}: {e}") from e

    text = "".join(getattr(c, "text", "") for c in result.content)
    if result.is_error:
        if INSUFFICIENT_PREFIX in text:
            raise GenerationError(422, text)
        raise GenerationError(502, f"generate_quiz failed: {text}")

    if result.structured_content is not None:
        return result.structured_content
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise GenerationError(502, "generate_quiz returned non-JSON content") from e
