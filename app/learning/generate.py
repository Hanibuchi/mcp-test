"""D1→D2変換と、MCP Serverから返った結果の検証（設計書6章 D2）。"""

from app.schemas import CommitIn, QuizArguments

QUESTION_COUNT = 3
CHOICE_COUNT = 4
TEXT_FIELDS = ("question", "hint", "explanation")


def build_arguments(commit: CommitIn) -> QuizArguments:
    """D1からmessage・files・diffだけを取り出し、出題条件を加える。"""
    return QuizArguments(
        message=commit.message,
        files=commit.files,
        diff=commit.diff,
        question_count=QUESTION_COUNT,
        choice_count=CHOICE_COUNT,
        language="ja",
    )


def validate_result(result: object) -> list[str]:
    """形式だけを検証し、問題点の一覧を返す（空なら合格）。内容の正しさは保証しない。"""
    if not isinstance(result, dict) or not isinstance(result.get("questions"), list):
        return ["result must be an object with a 'questions' array"]

    questions = result["questions"]
    errors: list[str] = []
    if len(questions) != QUESTION_COUNT:
        errors.append(f"expected {QUESTION_COUNT} questions, got {len(questions)}")

    for i, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            errors.append(f"q{i}: must be an object")
            continue
        for field in TEXT_FIELDS:
            value = q.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"q{i}: '{field}' must be a non-empty string")

        choices = q.get("choices")
        if not isinstance(choices, list) or not all(isinstance(c, str) for c in choices):
            errors.append(f"q{i}: 'choices' must be an array of strings")
        else:
            if len(choices) != CHOICE_COUNT:
                errors.append(f"q{i}: expected {CHOICE_COUNT} choices, got {len(choices)}")
            if any(not c.strip() for c in choices):
                errors.append(f"q{i}: choices must not be empty")
            if len({c.strip() for c in choices}) != len(choices):
                errors.append(f"q{i}: choices must not be duplicated")

        index = q.get("correct_index")
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < CHOICE_COUNT:
            errors.append(f"q{i}: 'correct_index' must be an integer 0-{CHOICE_COUNT - 1}")
    return errors
