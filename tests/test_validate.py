import copy
import json
from pathlib import Path

from app.learning.generate import build_arguments, validate_result
from app.schemas import CommitIn

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_D1 = json.loads((ROOT / "app/static/sample_d1.json").read_text(encoding="utf-8"))
SAMPLE_D2 = json.loads((ROOT / "mcp_server/fake_result.json").read_text(encoding="utf-8"))


def test_build_arguments_uses_only_message_files_diff():
    args = build_arguments(CommitIn(**SAMPLE_D1)).model_dump()
    assert set(args) == {"message", "files", "diff", "question_count", "choice_count", "language"}
    assert args["diff"] == SAMPLE_D1["diff"]
    assert (args["question_count"], args["choice_count"], args["language"]) == (3, 4, "ja")


def test_sample_result_is_valid():
    assert validate_result(SAMPLE_D2) == []


def test_wrong_question_count():
    bad = {"questions": SAMPLE_D2["questions"][:2]}
    assert any("expected 3 questions" in e for e in validate_result(bad))


def test_duplicate_choices_and_bad_index():
    bad = copy.deepcopy(SAMPLE_D2)
    bad["questions"][0]["choices"][1] = bad["questions"][0]["choices"][0]
    bad["questions"][1]["correct_index"] = 4
    bad["questions"][2]["correct_index"] = True
    errors = validate_result(bad)
    assert any("q1: choices must not be duplicated" in e for e in errors)
    assert any(e.startswith("q2: 'correct_index'") for e in errors)
    assert any(e.startswith("q3: 'correct_index'") for e in errors)


def test_empty_text_and_not_object():
    bad = copy.deepcopy(SAMPLE_D2)
    bad["questions"][0]["hint"] = " "
    assert any("q1: 'hint'" in e for e in validate_result(bad))
    assert validate_result([]) == ["result must be an object with a 'questions' array"]
