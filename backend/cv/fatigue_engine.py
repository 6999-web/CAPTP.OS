from __future__ import annotations

from collections import deque

import numpy as np


class FatigueEngine:
    def __init__(self, history_size: int = 24) -> None:
        self.motion_history: deque[float] = deque(maxlen=history_size)

    def update(self, pose_sequence: list) -> dict:
        motion = self._estimate_motion(pose_sequence)
        self.motion_history.append(motion)

        if len(self.motion_history) < 4:
            return {"level": "low", "score": 0.2, "reason": "insufficient_motion_history"}

        recent = np.array(list(self.motion_history), dtype=float)
        mean_motion = float(np.mean(recent))
        std_motion = float(np.std(recent))

        fatigue_score = float(np.clip((0.7 - mean_motion) + std_motion * 0.5, 0.0, 1.0))
        if fatigue_score > 0.66:
            level = "high"
            reason = "movement amplitude decays and stability variance increases"
        elif fatigue_score > 0.33:
            level = "medium"
            reason = "movement quality starts dropping"
        else:
            level = "low"
            reason = "movement remains stable"

        return {"level": level, "score": fatigue_score, "reason": reason}

    def _estimate_motion(self, pose_sequence: list) -> float:
        if len(pose_sequence) < 2:
            return 0.5

        deltas = []
        for prev, cur in zip(pose_sequence[:-1], pose_sequence[1:]):
            if not prev.persons or not cur.persons:
                continue
            p0 = max(prev.persons, key=lambda p: p.score)
            p1 = max(cur.persons, key=lambda p: p.score)
            k0 = p0.keypoints_xy
            k1 = p1.keypoints_xy
            delta = float(np.linalg.norm(k1 - k0, axis=1).mean())
            torso = np.linalg.norm(k1[5] - k1[11]) + 1e-6
            deltas.append(delta / torso)

        if not deltas:
            return 0.5
        return float(np.mean(deltas))

