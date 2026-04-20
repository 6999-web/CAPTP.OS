from __future__ import annotations

from cv.combat_analysis import CombatAnalyzer
from schemas import CombatActionItem


def test_combat_quartet_has_four_fields_semantics():
    analyzer = CombatAnalyzer()
    actions = [CombatActionItem(action='straight_punch', confidence=0.8, actor_id=0, frame_index=12)]
    quartets = analyzer.build_quartets(actions=actions, hits=[], fatigue={"level": "low", "score": 0.2, "reason": "ok"}, fps=24)

    assert len(quartets) == 1
    q = quartets[0]
    assert q.action
    assert q.effect
    assert q.reason
    assert q.suggestion

