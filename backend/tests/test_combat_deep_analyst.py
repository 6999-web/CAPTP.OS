from __future__ import annotations

from services.combat_deep_analyst import CombatDeepAnalyst


def test_simulated_180_seconds_returns_loss_and_stamina_reason():
    engine = CombatDeepAnalyst()
    report = engine.simulate_180_seconds()

    assert report["result"] == "Loss"
    assert "体力不支" in report["primary_reason"]
    assert report["evidence"]["timestamp"] == "02:15"
    assert report["diagnoses"]["fatigue"]["drop_count"] == 3


def test_simulated_180_seconds_contains_key_event_spots_and_feedback():
    engine = CombatDeepAnalyst()
    report = engine.simulate_180_seconds()

    event_types = {item["event_type"] for item in report["event_spots"]}
    assert "防守位塌陷" in event_types
    assert "重击受挫" in event_types
    assert "核心耐力" in report["technical_feedback"]
