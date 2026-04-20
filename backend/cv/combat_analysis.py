from __future__ import annotations

import numpy as np

from schemas import CombatActionItem, CombatQuartet, HitEvent
from cv.types import FramePoseResult


ACTION_REASON_MAP = {
    "straight_punch": ("direct upper-body strike with linear extension", "keep chin tucked, retract fist faster after impact"),
    "hook_punch": ("rotational punch with partial shoulder opening", "improve hip-shoulder torque sequencing"),
    "kick": ("lower-limb strike with balance transition", "increase support-leg stability and guard-hand discipline"),
    "block": ("defensive frame absorbs incoming force", "maintain compact guard and shorten defensive arc"),
    "dodge": ("evasion reduced contact probability", "increase head movement amplitude and timing"),
}


class CombatAnalyzer:
    def build_actions(self, action_label: str, confidence: float, frame_index: int) -> list[CombatActionItem]:
        if action_label in {"idle", "unknown", "weapon_present", "prepare_and_fire", "check_weapon"}:
            return []
        return [CombatActionItem(action=action_label, confidence=confidence, actor_id=0, frame_index=frame_index)]

    def estimate_hits(self, pose: FramePoseResult, frame_index: int) -> list[HitEvent]:
        if len(pose.persons) < 2:
            return []

        a, b = sorted(pose.persons, key=lambda p: p.score, reverse=True)[:2]
        a_wrist = (a.keypoints_xy[9] + a.keypoints_xy[10]) / 2
        b_head = b.keypoints_xy[0]
        b_torso = (b.keypoints_xy[5] + b.keypoints_xy[6] + b.keypoints_xy[11] + b.keypoints_xy[12]) / 4

        head_dist = np.linalg.norm(a_wrist - b_head)
        torso_dist = np.linalg.norm(a_wrist - b_torso)
        torso_scale = np.linalg.norm(b.keypoints_xy[5] - b.keypoints_xy[11]) + 1e-6

        events: list[HitEvent] = []
        if head_dist < torso_scale * 0.6:
            events.append(HitEvent(attacker_id=a.person_id, defender_id=b.person_id, target="head", confidence=float(np.clip(1.0 - head_dist / (torso_scale * 0.6), 0.0, 1.0)), frame_index=frame_index))
        elif torso_dist < torso_scale * 0.7:
            events.append(HitEvent(attacker_id=a.person_id, defender_id=b.person_id, target="body", confidence=float(np.clip(1.0 - torso_dist / (torso_scale * 0.7), 0.0, 1.0)), frame_index=frame_index))
        return events

    def build_quartets(self, actions: list[CombatActionItem], hits: list[HitEvent], fatigue: dict, fps: float) -> list[CombatQuartet]:
        quartets: list[CombatQuartet] = []
        for action in actions:
            hit = next((h for h in hits if h.frame_index == action.frame_index), None)
            effect = "未击中"
            if hit is not None:
                effect = f"击中{hit.target}"
            if fatigue["level"] == "high":
                effect = effect + "，自身失衡风险上升"

            reason_base, suggestion = ACTION_REASON_MAP.get(action.action, ("technique execution uncertain", "stabilize base and improve timing"))
            if fatigue["level"] == "high":
                reason = f"{reason_base}; fatigue accumulation affects reaction speed"
                suggestion = suggestion + "; add interval conditioning and recovery pacing"
            else:
                reason = reason_base

            ts = action.frame_index / max(1.0, fps)
            quartets.append(
                CombatQuartet(
                    action=action.action,
                    effect=effect,
                    reason=reason,
                    suggestion=suggestion,
                    confidence=action.confidence,
                    timestamp_range=(max(0.0, ts - 0.2), ts + 0.2),
                )
            )
        return quartets

    def estimate_stability(self, pose: FramePoseResult) -> float:
        if not pose.persons:
            return 0.0
        person = max(pose.persons, key=lambda p: p.score)
        k = person.keypoints_xy
        shoulder_center = (k[5] + k[6]) / 2
        foot_center = (k[15] + k[16]) / 2
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        x_dev = abs(shoulder_center[0] - foot_center[0]) / torso
        return float(np.clip(1.0 - x_dev, 0.0, 1.0))

