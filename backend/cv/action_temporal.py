from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

import numpy as np

from cv.types import FramePoseResult, FrameWeaponResult


@dataclass
class TemporalStatus:
    mmaction_ready: bool
    stgcn_ready: bool
    agcn_ready: bool


@dataclass
class TemporalOutput:
    frame_actions: list[dict]
    dominant_action: str
    confidence: float


class ActionTemporalAnalyzer:
    def __init__(self) -> None:
        self._mmaction_model = None
        self._load_mmaction()

    @property
    def status(self) -> TemporalStatus:
        return TemporalStatus(
            mmaction_ready=self._mmaction_model is not None,
            stgcn_ready=False,
            agcn_ready=False,
        )

    def _load_mmaction(self) -> None:
        # Placeholder for future plug-in loading. Keep runtime-safe by default.
        self._mmaction_model = None

    def analyze_frame(self, pose: FramePoseResult, weapon: FrameWeaponResult) -> TemporalOutput:
        action, conf = self._heuristic_action(pose, weapon)
        return TemporalOutput(frame_actions=[{"action": action, "confidence": conf}], dominant_action=action, confidence=conf)

    def analyze_sequence(self, poses: list[FramePoseResult], weapons: list[FrameWeaponResult]) -> TemporalOutput:
        items: list[dict] = []
        for p, w in zip(poses, weapons):
            action, conf = self._heuristic_action(p, w)
            items.append({"action": action, "confidence": conf})

        if not items:
            return TemporalOutput(frame_actions=[], dominant_action="unknown", confidence=0.0)

        c = Counter([x["action"] for x in items])
        dominant = c.most_common(1)[0][0]
        conf = float(np.mean([x["confidence"] for x in items if x["action"] == dominant]))
        return TemporalOutput(frame_actions=items, dominant_action=dominant, confidence=conf)

    def _heuristic_action(self, pose: FramePoseResult, weapon: FrameWeaponResult) -> tuple[str, float]:
        if weapon.weapons:
            person = max(pose.persons, key=lambda p: p.score) if pose.persons else None
            if person is None:
                return "weapon_present", 0.55

            k = person.keypoints_xy
            left_reach = np.linalg.norm(k[9] - k[5])
            right_reach = np.linalg.norm(k[10] - k[6])
            torso = np.linalg.norm(k[5] - k[11]) + 1e-6
            reach = (left_reach + right_reach) / (2 * torso)
            if reach > 1.0:
                return "prepare_and_fire", 0.78
            return "check_weapon", 0.65

        if len(pose.persons) >= 2:
            p1, p2 = sorted(pose.persons, key=lambda p: p.score, reverse=True)[:2]
            dist = np.linalg.norm(self._center(p1) - self._center(p2))
            scale = max(50.0, np.linalg.norm(np.array(p1.bbox[:2]) - np.array(p1.bbox[2:])))
            if dist < scale * 0.8:
                return "block", 0.62
            wrist_speed_proxy = self._wrist_extension_ratio(p1)
            if wrist_speed_proxy > 1.1:
                return "straight_punch", 0.7
            if wrist_speed_proxy > 0.95:
                return "hook_punch", 0.62
            return "dodge", 0.55

        if pose.persons:
            person = max(pose.persons, key=lambda p: p.score)
            leg_ratio = self._leg_lift_ratio(person)
            if leg_ratio > 0.7:
                return "kick", 0.68
        return "idle", 0.45

    def _center(self, p):
        x1, y1, x2, y2 = p.bbox
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2], dtype=float)

    def _wrist_extension_ratio(self, p) -> float:
        k = p.keypoints_xy
        reach = (np.linalg.norm(k[9] - k[5]) + np.linalg.norm(k[10] - k[6])) / 2
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        return float(reach / torso)

    def _leg_lift_ratio(self, p) -> float:
        k = p.keypoints_xy
        hip_line = (k[11][1] + k[12][1]) / 2
        ankle_high = min(k[15][1], k[16][1])
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        return float((hip_line - ankle_high) / torso)

