from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeMode(str, Enum):
    shooting_posture = "shooting_posture"
    shooting_flow = "shooting_flow"
    combat_action = "combat_action"
    combat_full = "combat_full"


class AnalyzeSource(str, Enum):
    image = "image"
    video = "video"
    stream = "stream"


class ShootingFlowStage(str, Enum):
    pass_gun_method_1 = "pass_gun_method_1"
    pass_gun_method_2 = "pass_gun_method_2"
    check_weapon = "check_weapon"
    insert_magazine = "insert_magazine"
    prepare_and_fire = "prepare_and_fire"
    post_fire_check = "post_fire_check"


class Violation(BaseModel):
    code: str
    severity: Literal["low", "medium", "high", "high_critical"]
    description: str
    rule_ref: str
    evidence_frame_idx: int = 0


class ShootingEvidence(BaseModel):
    frame_index: int
    label: str
    confidence: float = 0.0


class ShootingResult(BaseModel):
    posture_compliance: bool = False
    posture_score: float = 0.0
    flow_stage: ShootingFlowStage = ShootingFlowStage.check_weapon
    flow_order_ok: bool = True
    violations: list[Violation] = Field(default_factory=list)
    evidence: list[ShootingEvidence] = Field(default_factory=list)


class CombatActionItem(BaseModel):
    action: str
    confidence: float
    actor_id: int | None = None
    frame_index: int = 0


class CombatQuartet(BaseModel):
    action: str
    effect: str
    reason: str
    suggestion: str
    confidence: float
    timestamp_range: tuple[float, float]


class HitEvent(BaseModel):
    attacker_id: int
    defender_id: int
    target: str
    confidence: float
    frame_index: int


class FatigueResult(BaseModel):
    level: Literal["low", "medium", "high"]
    score: float
    reason: str


class CombatResult(BaseModel):
    actions: list[CombatActionItem] = Field(default_factory=list)
    quartets: list[CombatQuartet] = Field(default_factory=list)
    fatigue: FatigueResult = Field(default_factory=lambda: FatigueResult(level="low", score=0.0, reason="insufficient_motion_history"))
    hit_events: list[HitEvent] = Field(default_factory=list)
    stability: float = 0.0


class MetaResult(BaseModel):
    fps: float = 0.0
    latency_ms: float = 0.0
    persons: int = 0
    device: str = "cpu"
    fallback_used: bool = False


class AnalyzeResult(BaseModel):
    shooting: ShootingResult
    combat: CombatResult
    meta: MetaResult
    reasoning: str | None = None


class AnalyzeRequest(BaseModel):
    mode: AnalyzeMode = AnalyzeMode.combat_full
    source: AnalyzeSource = AnalyzeSource.image
    scene_cardinality: str = "multi_person"


class TacticalMessage(BaseModel):
    role: str
    content: str


class TacticalChatRequest(BaseModel):
    messages: list[TacticalMessage]
    scenario: str | None = None
    scenarioContext: str | None = None


class ModelHealth(BaseModel):
    ready: bool
    runtime_profile: str
    device: str
    loaded_models: dict[str, bool]
    versions: dict[str, Any]

