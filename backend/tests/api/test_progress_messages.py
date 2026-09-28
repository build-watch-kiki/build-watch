from types import SimpleNamespace

import pytest

from buildwatch.progress.messages import count_text, progress_message, stage_message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0 дней"),
        (1, "1 день"),
        (2, "2 дня"),
        (4, "4 дня"),
        (5, "5 дней"),
        (11, "11 дней"),
        (21, "21 день"),
        (-22, "22 дня"),
    ],
)
def test_russian_plural_forms(value, expected):
    assert count_text(value, "день", "дня", "дней") == expected


def test_stage_messages_are_structured_and_plain_text():
    message = stage_message("behind", "Котлован", 2)
    assert message.code == "stage_behind"
    assert message.severity == "warning"
    assert message.text == "Этап «Котлован» отстаёт от плана на 2 дня"
    assert "<" not in message.text


def test_gantt_message_includes_technique_deviation_count():
    message = stage_message("behind", "Котлован", 5, 2, compact=True)
    assert message.code == "stage_behind_with_technique_deviations"
    assert message.text == "Отставание на 5 дней, отклонения по 2 видам техники"


def test_daily_message_keeps_stable_status_code_with_technique_deviations():
    message = stage_message("behind", "Котлован", 5, 2)
    assert message.code == "stage_behind"


def test_low_stage_score_message_explains_candidates_and_threshold():
    progress = SimpleNamespace(
        reason="low_stage_score",
        previous_stage_name="Обустройство площадки",
        previous_score=0.07,
        next_stage_name="Выемка грунта",
        next_score=0.45,
        actual_stage_name=None,
        time_deviation_days=None,
    )

    message = progress_message(progress, "unknown", 0.60)

    assert message.code == "stage_score_below_threshold"
    assert message.text == (
        "Техника на снимках недостаточно соответствует плану этапа: "
        "предыдущий «Обустройство площадки» — 7%, следующий «Выемка грунта» — "
        "45%. Необходимый порог — 60%"
    )
