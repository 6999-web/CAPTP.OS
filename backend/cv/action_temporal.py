from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from cv.types import FramePoseResult, FrameWeaponResult


@dataclass
class TemporalStatus:
    mmaction_ready: bool
    stgcn_ready: bool
    agcn_ready: bool


@dataclass
class TemporalFeatureSnapshot:
    frame_index: int
    wrist_speed: float
    elbow_extension: float
    hip_rotation: float
    distance_delta: float
    guard_open: float
    leg_lift: float


@dataclass
class TemporalOutput:
    frame_actions: list[dict]
    dominant_action: str
    confidence: float
    features: list[TemporalFeatureSnapshot]


class ActionTemporalAnalyzer:
    def __init__(self) -> None:
        self._mmaction_model = None
        self._window_size = 12
        self._load_mmaction()

    @property
    def status(self) -> TemporalStatus:
        return TemporalStatus(
            mmaction_ready=self._mmaction_model is not None,
            stgcn_ready=False,
            agcn_ready=False,
        )

    def _load_mmaction(self) -> None:
        self._mmaction_model = None

    def analyze_frame(self, pose: FramePoseResult, weapon: FrameWeaponResult) -> TemporalOutput:
        action, conf = self._heuristic_action(pose, weapon)
        features = [self._feature_snapshot(0, pose, pose)]
        return TemporalOutput(frame_actions=[{"action": action, "confidence": conf}], dominant_action=action, confidence=conf, features=features)

    def analyze_sequence(self, poses: list[FramePoseResult], weapons: list[FrameWeaponResult]) -> TemporalOutput:
        cleaned_poses = self._clean_sequence(poses)
        if not cleaned_poses:
            return TemporalOutput(frame_actions=[], dominant_action="unknown", confidence=0.0, features=[])

        features = [
            self._feature_snapshot(idx, cleaned_poses[idx], cleaned_poses[max(0, idx - 1)])
            for idx in range(len(cleaned_poses))
        ]

        items: list[dict] = []
        for idx, (pose, weapon) in enumerate(zip(cleaned_poses, weapons)):
            start = max(0, idx - self._window_size + 1)
            window = features[start : idx + 1]
            action, conf = self._heuristic_action(pose, weapon, window)
            items.append({"action": action, "confidence": conf})

        smoothed_items = self._suppress_isolated_actions(items)
        dominant_counter = Counter(item["action"] for item in smoothed_items)
        dominant_action = dominant_counter.most_common(1)[0][0]
        dominant_confidence = float(np.mean([item["confidence"] for item in smoothed_items if item["action"] == dominant_action]))
        return TemporalOutput(frame_actions=smoothed_items, dominant_action=dominant_action, confidence=dominant_confidence, features=features)

    def _clean_sequence(self, poses: list[FramePoseResult]) -> list[FramePoseResult]:
        cleaned: list[FramePoseResult] = []
        previous_pose: FramePoseResult | None = None

        for pose in poses:
            if not pose.persons:
                cleaned.append(pose)
                continue

            for person in pose.persons:
                if person.keypoints_xy.size == 0:
                    continue
                low_conf_mask = person.keypoints_conf < 0.2
                if previous_pose is not None:
                    previous_person = self._resolve_person_by_id(previous_pose, person.person_id)
                    if previous_person is not None:
                        person.keypoints_xy[low_conf_mask] = previous_person.keypoints_xy[low_conf_mask]
                    else:
                        person.keypoints_xy[low_conf_mask] = self._fill_points(person.keypoints_xy)[low_conf_mask]
                else:
                    person.keypoints_xy[low_conf_mask] = self._fill_points(person.keypoints_xy)[low_conf_mask]

                if previous_pose is not None:
                    previous_person = self._resolve_person_by_id(previous_pose, person.person_id)
                    if previous_person is not None:
                        person.keypoints_xy = (person.keypoints_xy * 0.65) + (previous_person.keypoints_xy * 0.35)
            cleaned.append(pose)
            previous_pose = pose
        return cleaned

    def _heuristic_action(
        self,
        pose: FramePoseResult,
        weapon: FrameWeaponResult,
        window: list[TemporalFeatureSnapshot] | None = None,
    ) -> tuple[str, float]:
        if weapon.weapons:
            person = max(pose.persons, key=lambda item: item.score) if pose.persons else None
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
            feature_window = window or [self._feature_snapshot(0, pose, pose)]
            mean_wrist_speed = float(np.mean([item.wrist_speed for item in feature_window]))
            mean_extension = float(np.mean([item.elbow_extension for item in feature_window]))
            mean_guard_open = float(np.mean([item.guard_open for item in feature_window]))
            mean_leg_lift = float(np.mean([item.leg_lift for item in feature_window]))
            mean_distance_delta = float(np.mean([item.distance_delta for item in feature_window]))
            mean_hip_rotation = float(np.mean([item.hip_rotation for item in feature_window]))

            if mean_guard_open < 0.24 and mean_distance_delta < 0.1:
                return "block", 0.63
            if mean_leg_lift > 0.68 and mean_wrist_speed > 0.15:
                return "kick", 0.74
            if mean_extension > 1.05 and mean_wrist_speed > 0.18:
                return "straight_punch", 0.72
            if mean_hip_rotation > 0.22 and mean_extension > 0.88:
                return "hook_punch", 0.66
            return "dodge", 0.56

        if pose.persons:
            person = max(pose.persons, key=lambda item: item.score)
            leg_ratio = self._leg_lift_ratio(person)
            if leg_ratio > 0.7:
                return "kick", 0.68
        return "idle", 0.45

    def _feature_snapshot(self, frame_index: int, pose: FramePoseResult, previous_pose: FramePoseResult) -> TemporalFeatureSnapshot:
        person = max(pose.persons, key=lambda item: item.score) if pose.persons else None
        previous_person = max(previous_pose.persons, key=lambda item: item.score) if previous_pose.persons else person
        if person is None or previous_person is None:
            return TemporalFeatureSnapshot(frame_index=frame_index, wrist_speed=0.0, elbow_extension=0.0, hip_rotation=0.0, distance_delta=0.0, guard_open=0.0, leg_lift=0.0)

        current_wrist = self._mean_points(person.keypoints_xy[[9, 10]])
        previous_wrist = self._mean_points(previous_person.keypoints_xy[[9, 10]])
        torso = np.linalg.norm(person.keypoints_xy[5] - person.keypoints_xy[11]) + 1e-6
        wrist_speed = float(np.linalg.norm(current_wrist - previous_wrist) / torso)

        elbow_extension = self._wrist_extension_ratio(person)
        hip_rotation = float(abs(person.keypoints_xy[5][0] - person.keypoints_xy[6][0]) / torso)
        guard_open = self._guard_open_ratio(person)
        leg_lift = self._leg_lift_ratio(person)
        distance_delta = self._distance_delta(pose, previous_pose)

        return TemporalFeatureSnapshot(
            frame_index=frame_index,
            wrist_speed=wrist_speed,
            elbow_extension=elbow_extension,
            hip_rotation=hip_rotation,
            distance_delta=distance_delta,
            guard_open=guard_open,
            leg_lift=leg_lift,
        )

    def _suppress_isolated_actions(self, items: list[dict]) -> list[dict]:
        if len(items) < 3:
            return items

        smoothed = [dict(item) for item in items]
        for idx in range(1, len(items) - 1):
            prev_action = items[idx - 1]["action"]
            curr_action = items[idx]["action"]
            next_action = items[idx + 1]["action"]
            if curr_action != prev_action and curr_action != next_action and prev_action == next_action and items[idx]["confidence"] < 0.62:
                smoothed[idx]["action"] = prev_action
                smoothed[idx]["confidence"] = float(max(items[idx - 1]["confidence"], items[idx + 1]["confidence"]) * 0.92)
        return smoothed

    def _distance_delta(self, pose: FramePoseResult, previous_pose: FramePoseResult) -> float:
        if len(pose.persons) < 2 or len(previous_pose.persons) < 2:
            return 0.0
        current_pair = sorted(pose.persons, key=lambda item: item.score, reverse=True)[:2]
        previous_pair = sorted(previous_pose.persons, key=lambda item: item.score, reverse=True)[:2]
        current_distance = np.linalg.norm(self._center(current_pair[0]) - self._center(current_pair[1]))
        previous_distance = np.linalg.norm(self._center(previous_pair[0]) - self._center(previous_pair[1]))
        body_scale = max(1.0, np.linalg.norm(np.array(current_pair[0].bbox[:2]) - np.array(current_pair[0].bbox[2:])))
        return float(abs(current_distance - previous_distance) / body_scale)

    def _resolve_person_by_id(self, pose: FramePoseResult, person_id: int):
        for person in pose.persons:
            if person.person_id == person_id:
                return person
        return None

    def _fill_points(self, points: np.ndarray) -> np.ndarray:
        if points.size == 0:
            return points
        replacement = points.copy()
        mean_xy = np.mean(points, axis=0)
        zero_mask = np.isclose(np.sum(np.abs(replacement), axis=1), 0.0)
        replacement[zero_mask] = mean_xy
        return replacement

    def _center(self, person) -> np.ndarray:
        x1, y1, x2, y2 = person.bbox
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2], dtype=float)

    def _mean_points(self, points: np.ndarray) -> np.ndarray:
        return np.mean(points, axis=0)

    def _guard_open_ratio(self, person) -> float:
        head = person.keypoints_xy[0]
        torso = np.linalg.norm(person.keypoints_xy[5] - person.keypoints_xy[11]) + 1e-6
        wrists = self._mean_points(person.keypoints_xy[[9, 10]])
        return float(np.linalg.norm(wrists - head) / (torso * 1.2))

    def _wrist_extension_ratio(self, person) -> float:
        k = person.keypoints_xy
        reach = (np.linalg.norm(k[9] - k[5]) + np.linalg.norm(k[10] - k[6])) / 2
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        return float(reach / torso)

    def _leg_lift_ratio(self, person) -> float:
        k = person.keypoints_xy
        hip_line = (k[11][1] + k[12][1]) / 2
        ankle_high = min(k[15][1], k[16][1])
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        return float((hip_line - ankle_high) / torso)
