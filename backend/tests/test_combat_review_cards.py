from __future__ import annotations

import numpy as np

from cv.combat_analysis import CombatAnalyzer
from cv.types import FramePoseResult, PosePerson
from schemas import CombatActionItem


def _person(person_id: int, offset_x: float, score: float = 0.95) -> PosePerson:
    keypoints = np.array(
        [
            [offset_x + 22, 24],
            [offset_x + 20, 28],
            [offset_x + 24, 28],
            [offset_x + 18, 34],
            [offset_x + 26, 34],
            [offset_x + 16, 50],
            [offset_x + 28, 50],
            [offset_x + 12, 68],
            [offset_x + 32, 68],
            [offset_x + 12, 42],
            [offset_x + 34, 42],
            [offset_x + 18, 84],
            [offset_x + 28, 84],
            [offset_x + 18, 112],
            [offset_x + 28, 112],
            [offset_x + 16, 146],
            [offset_x + 30, 146],
        ],
        dtype=float,
    )
    conf = np.ones((17,), dtype=float) * score
    return PosePerson(
        person_id=person_id,
        bbox=(int(offset_x), 10, int(offset_x + 48), 164),
        score=score,
        keypoints_xy=keypoints,
        keypoints_conf=conf,
    )


def test_review_cards_include_chinese_fields_and_images():
    analyzer = CombatAnalyzer()
    frame = np.full((180, 220, 3), 120, dtype=np.uint8)
    attacker = _person(0, 20)
    defender = _person(1, 84)
    defender.keypoints_xy[0] = np.array([54.0, 42.0])
    defender.keypoints_xy[9] = np.array([90.0, 78.0])
    defender.keypoints_xy[10] = np.array([96.0, 78.0])
    pose = FramePoseResult(persons=[attacker, defender], fallback_used=False)

    actions = [CombatActionItem(action="straight_punch", confidence=0.82, actor_id=0, frame_index=0)]
    hits = analyzer.estimate_hits(pose, 0)
    cards = analyzer.build_review_cards([frame], [pose], actions, hits, {"level": "medium", "score": 0.55, "reason": "test"}, 12.0)

    assert cards
    card = cards[0]
    assert card.action_zh == "直拳"
    assert card.damage_zh
    assert card.evade_failure_reason_zh
    assert card.summary_zh
    assert card.image_b64
    assert card.metrics.distance_score >= 0.0


def test_supported_actions_are_always_available():
    analyzer = CombatAnalyzer()
    actions = analyzer.supported_actions()

    assert actions
    assert all(item.action_zh for item in actions)
    assert all(item.common_evade_failure_reasons_zh for item in actions)


def test_review_cards_fallback_reason_when_evidence_is_weak():
    analyzer = CombatAnalyzer()
    frame = np.zeros((140, 180, 3), dtype=np.uint8)
    single_pose = FramePoseResult(persons=[_person(0, 24, score=0.2)], fallback_used=True)
    actions = [CombatActionItem(action="dodge", confidence=0.4, actor_id=0, frame_index=0)]

    cards = analyzer.build_review_cards([frame], [single_pose], actions, [], {"level": "low", "score": 0.1, "reason": "weak"}, 10.0)

    assert cards
    assert cards[0].evade_failure_reason_zh == "画面证据不足，无法稳定判断"
