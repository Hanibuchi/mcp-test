"""FastAPI：画面配信と POST /api/v1/commits（MCP Clientとして問題生成を呼ぶ）。

FastAPIはGemini APIを直接呼ばない。問題生成はMCP Server経由のみ。
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.learning.generate import build_arguments, validate_result
from app.learning.mcp_client import GenerationError, call_generate_quiz
from app.schemas import CommitIn, GenerateResponse

load_dotenv()

STATIC_DIR = Path(__file__).with_name("static")
MCP_TIMEOUT_SEC = float(os.environ.get("MCP_TIMEOUT_SEC", "20"))

app = FastAPI(title="nanicommit MCP PoC")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/commits", response_model=GenerateResponse)
async def create_commit(commit: CommitIn):
    arguments = build_arguments(commit)
    started = time.perf_counter()
    try:
        result = await call_generate_quiz(arguments, MCP_TIMEOUT_SEC)
    except GenerationError as e:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail, "elapsed_ms": elapsed_ms})
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    errors = validate_result(result)
    body = GenerateResponse(
        status="ok" if not errors else "invalid",
        elapsed_ms=elapsed_ms,
        mcp_arguments=arguments,
        result=result if isinstance(result, dict) else {"raw": result},
        validation_errors=errors,
    )
    # 返却データが形式不正なら設計書どおり502。確認用に中身も返す。
    return JSONResponse(status_code=200 if not errors else 502, content=body.model_dump())
