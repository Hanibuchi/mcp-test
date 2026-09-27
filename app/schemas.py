"""設計書6章のD1・D2に対応するモデル。"""

from pydantic import BaseModel, Field


class CommitIn(BaseModel):
    """D1：commit送信（6項目）。"""

    repository_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")
    commit_sha: str = Field(pattern=r"^([0-9a-f]{40}|[0-9a-f]{64})$")
    branch: str | None
    message: str
    files: list[str]
    diff: str


class QuizArguments(BaseModel):
    """D2：generate_quiz toolへ渡すarguments。"""

    message: str
    files: list[str]
    diff: str
    question_count: int = 3
    choice_count: int = 4
    language: str = "ja"


class GenerateResponse(BaseModel):
    """本PoCの返答（実現性確認用。設計書のquiz_id/quiz_urlの代わり）。"""

    status: str
    elapsed_ms: int
    mcp_arguments: QuizArguments
    result: dict
    validation_errors: list[str]
