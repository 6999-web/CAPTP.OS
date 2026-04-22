from __future__ import annotations

import base64

import cv2
import numpy as np

from schemas import CombatActionItem, CombatQuartet, CombatReviewCard, CombatReviewMetrics, HitEvent, SupportedCombatAction
from cv.types import FramePoseResult, PosePerson


ACTION_CATALOG = {
    "straight_punch": {
        "action_zh": "直拳",
        "description_zh": "直线出拳，强调手臂伸展与中轴压迫。",
        "typical_damage_zh": "击中头部或躯干，形成直接打击。",
        "common_evade_failure_reasons_zh": ["距离来不及拉开", "护架打开，头部/躯干暴露", "被假动作或上一步动作牵制"],
        "suggestion_zh": "保持下巴内收，命中后快速回收拳路。",
    },
    "hook_punch": {
        "action_zh": "勾拳",
        "description_zh": "借助髋肩旋转完成弧线打击，适合侧向切入。",
        "typical_damage_zh": "容易形成头部侧向命中或压迫护架。",
        "common_evade_failure_reasons_zh": ["护架打开，头部/躯干暴露", "重心滞后，无法及时撤步", "被假动作或上一步动作牵制"],
        "suggestion_zh": "先稳住支撑脚，再做髋肩联动。",
    },
    "kick": {
        "action_zh": "踢击",
        "description_zh": "下肢提膝转髋完成中远距离打击。",
        "typical_damage_zh": "击中躯干或形成明显压制。",
        "common_evade_failure_reasons_zh": ["距离来不及拉开", "重心滞后，无法及时撤步", "连续对抗后反应下降"],
        "suggestion_zh": "抬膝后保持上肢护架，不让支撑腿失稳。",
    },
    "block": {
        "action_zh": "格挡",
        "description_zh": "使用前臂或护架吸收来袭力量。",
        "typical_damage_zh": "通常不形成有效击中，但可造成压制节奏。",
        "common_evade_failure_reasons_zh": ["被假动作或上一步动作牵制", "连续对抗后反应下降", "画面证据不足，无法稳定判断"],
        "suggestion_zh": "缩短防守弧线，避免护架打开。",
    },
    "dodge": {
        "action_zh": "闪躲",
        "description_zh": "通过头部或躯干位移降低被命中概率。",
        "typical_damage_zh": "通常不形成有效击中，更多体现为化解威胁。",
        "common_evade_failure_reasons_zh": ["重心滞后，无法及时撤步", "连续对抗后反应下降", "画面证据不足，无法稳定判断"],
        "suggestion_zh": "加大头部位移幅度并配合步法撤离。",
    },
}
DEFAULT_EVADE_REASON = "画面证据不足，无法稳定判断"
TARGET_ZH_MAP = {"head": "头部", "body": "躯干"}


class CombatAnalyzer:
    def supported_actions(self) -> list[SupportedCombatAction]:
        return [
            SupportedCombatAction(
                action_code=code,
                action_zh=meta["action_zh"],
                description_zh=meta["description_zh"],
                typical_damage_zh=meta["typical_damage_zh"],
                common_evade_failure_reasons_zh=list(meta["common_evade_failure_reasons_zh"]),
            )
            for code, meta in ACTION_CATALOG.items()
        ]

    def build_actions(self, action_label: str, confidence: float, frame_index: int) -> list[CombatActionItem]:
        if action_label in {"idle", "unknown", "weapon_present", "prepare_and_fire", "check_weapon"}:
            return []
        return [CombatActionItem(action=action_label, confidence=confidence, actor_id=0, frame_index=frame_index)]

    def estimate_hits(self, pose: FramePoseResult, frame_index: int) -> list[HitEvent]:
        if len(pose.persons) < 2:
            return []

        attacker, defender = sorted(pose.persons, key=lambda item: item.score, reverse=True)[:2]
        attacker_wrist = (attacker.keypoints_xy[9] + attacker.keypoints_xy[10]) / 2
        defender_head = defender.keypoints_xy[0]
        defender_torso = (defender.keypoints_xy[5] + defender.keypoints_xy[6] + defender.keypoints_xy[11] + defender.keypoints_xy[12]) / 4

        head_dist = np.linalg.norm(attacker_wrist - defender_head)
        torso_dist = np.linalg.norm(attacker_wrist - defender_torso)
        torso_scale = np.linalg.norm(defender.keypoints_xy[5] - defender.keypoints_xy[11]) + 1e-6

        events: list[HitEvent] = []
        if head_dist < torso_scale * 0.6:
            events.append(
                HitEvent(
                    attacker_id=attacker.person_id,
                    defender_id=defender.person_id,
                    target="head",
                    confidence=float(np.clip(1.0 - head_dist / (torso_scale * 0.6), 0.0, 1.0)),
                    frame_index=frame_index,
                )
            )
        elif torso_dist < torso_scale * 0.7:
            events.append(
                HitEvent(
                    attacker_id=attacker.person_id,
                    defender_id=defender.person_id,
                    target="body",
                    confidence=float(np.clip(1.0 - torso_dist / (torso_scale * 0.7), 0.0, 1.0)),
                    frame_index=frame_index,
                )
            )
        return events

    def build_quartets(self, actions: list[CombatActionItem], hits: list[HitEvent], fatigue: dict, fps: float) -> list[CombatQuartet]:
        quartets: list[CombatQuartet] = []
        for action in actions:
            hit = next((item for item in hits if item.frame_index == action.frame_index), None)
            ts = action.frame_index / max(1.0, fps)
            quartets.append(
                CombatQuartet(
                    action=self._action_zh(action.action),
                    effect=self._damage_zh(hit, fatigue["level"] == "high", action.confidence),
                    reason=self._quartet_reason_zh(action.action, hit, fatigue),
                    suggestion=self._suggestion_zh(action.action),
                    confidence=action.confidence,
                    timestamp_range=(max(0.0, ts - 0.2), ts + 0.2),
                )
            )
        return quartets

    def build_review_cards(
        self,
        frames: list[np.ndarray],
        poses: list[FramePoseResult],
        actions: list[CombatActionItem],
        hits: list[HitEvent],
        fatigue: dict,
        fps: float,
    ) -> list[CombatReviewCard]:
        if not frames or not poses:
            return []

        cards: list[CombatReviewCard] = []
        pose_by_frame = {idx: pose for idx, pose in enumerate(poses)}
        frame_by_index = {idx: frame for idx, frame in enumerate(frames)}
        hit_by_frame = {hit.frame_index: hit for hit in hits}

        for seq_idx, action in enumerate(actions):
            pose = pose_by_frame.get(action.frame_index)
            frame = frame_by_index.get(action.frame_index)
            if pose is None or frame is None:
                continue

            previous_pose = pose_by_frame.get(max(0, action.frame_index - 1), pose)
            hit = hit_by_frame.get(action.frame_index)
            attacker, defender = self._resolve_pair(pose, hit)
            metrics = self._review_metrics(pose, previous_pose, attacker, defender, action, hit, fatigue)
            action_zh = self._action_zh(action.action)
            damage_zh = self._damage_zh(hit, metrics.balance_break_score > 0.7, action.confidence)
            evade_failure_reason_zh = self._evade_failure_reason(metrics, action.action, hit, fatigue)
            timestamp = self._format_timestamp(action.frame_index, fps)

            cards.append(
                CombatReviewCard(
                    card_id=f"combat-card-{action.frame_index}-{seq_idx}",
                    frame_index=action.frame_index,
                    timestamp=timestamp,
                    image_b64=self._encode_crop(frame, attacker, defender),
                    action_code=action.action,
                    action_zh=action_zh,
                    damage_zh=damage_zh,
                    evade_failure_reason_zh=evade_failure_reason_zh,
                    summary_zh=f"{timestamp}，{action_zh}：{damage_zh}；未躲闪原因：{evade_failure_reason_zh}",
                    confidence=float(action.confidence),
                    attacker_id=attacker.person_id if attacker is not None else action.actor_id,
                    defender_id=defender.person_id if defender is not None else (hit.defender_id if hit is not None else None),
                    target_zh=TARGET_ZH_MAP.get(hit.target, "未判定") if hit is not None else "未判定",
                    metrics=metrics,
                )
            )
        return cards

    def estimate_stability(self, pose: FramePoseResult) -> float:
        if not pose.persons:
            return 0.0
        person = max(pose.persons, key=lambda item: item.score)
        return self._stability_for_person(person)

    def _review_metrics(
        self,
        pose: FramePoseResult,
        previous_pose: FramePoseResult,
        attacker: PosePerson | None,
        defender: PosePerson | None,
        action: CombatActionItem,
        hit: HitEvent | None,
        fatigue: dict,
    ) -> CombatReviewMetrics:
        if attacker is None:
            return CombatReviewMetrics()

        attacker_wrist = self._mean_points(attacker.keypoints_xy[[9, 10]])
        attacker_shoulder = self._mean_points(attacker.keypoints_xy[[5, 6]])
        torso_scale = np.linalg.norm(attacker.keypoints_xy[5] - attacker.keypoints_xy[11]) + 1e-6
        explosiveness_score = self._clip(np.linalg.norm(attacker_wrist - attacker_shoulder) / (torso_scale * 1.3))
        stability_score = self._stability_for_person(attacker)
        impact_score = self._clip(action.confidence + (0.2 if hit is not None else 0.0))

        if defender is None:
            return CombatReviewMetrics(
                impact_score=impact_score,
                balance_break_score=1.0 - stability_score,
                stability_score=stability_score,
                explosiveness_score=explosiveness_score,
                reaction_lag_score=0.35 if fatigue["level"] == "high" else 0.0,
            )

        defender_head = defender.keypoints_xy[0]
        defender_torso = self._mean_points(defender.keypoints_xy[[5, 6, 11, 12]])
        target_point = defender_head if hit is not None and hit.target == "head" else defender_torso
        distance_score = self._clip(1.0 - np.linalg.norm(attacker_wrist - target_point) / (torso_scale * 1.4))
        guard_open_score = self._guard_open_score(defender)
        defender_stability = self._stability_for_person(defender)
        previous_defender = self._resolve_person_by_id(previous_pose, defender.person_id) or defender
        previous_guard_open = self._guard_open_score(previous_defender)
        reaction_lag_base = 0.75 if fatigue["level"] == "high" else 0.45 if fatigue["level"] == "medium" else 0.2
        reaction_lag_score = self._clip(reaction_lag_base + max(0.0, guard_open_score - previous_guard_open))
        balance_break_score = self._clip((1.0 - defender_stability) * 0.8 + max(0.0, distance_score - 0.35) * 0.4)

        return CombatReviewMetrics(
            distance_score=distance_score,
            impact_score=impact_score,
            guard_open_score=guard_open_score,
            balance_break_score=balance_break_score,
            stability_score=stability_score,
            explosiveness_score=explosiveness_score,
            reaction_lag_score=reaction_lag_score,
        )

    def _resolve_pair(self, pose: FramePoseResult, hit: HitEvent | None) -> tuple[PosePerson | None, PosePerson | None]:
        if not pose.persons:
            return None, None
        ordered = sorted(pose.persons, key=lambda item: item.score, reverse=True)
        attacker = ordered[0]
        defender = ordered[1] if len(ordered) > 1 else None
        if hit is None:
            return attacker, defender
        return self._resolve_person_by_id(pose, hit.attacker_id) or attacker, self._resolve_person_by_id(pose, hit.defender_id) or defender

    def _resolve_person_by_id(self, pose: FramePoseResult, person_id: int) -> PosePerson | None:
        for person in pose.persons:
            if person.person_id == person_id:
                return person
        return None

    def _guard_open_score(self, person: PosePerson) -> float:
        head = person.keypoints_xy[0]
        left_wrist = person.keypoints_xy[9]
        right_wrist = person.keypoints_xy[10]
        torso = np.linalg.norm(person.keypoints_xy[5] - person.keypoints_xy[11]) + 1e-6
        mean_dist = (np.linalg.norm(left_wrist - head) + np.linalg.norm(right_wrist - head)) / 2
        return self._clip(mean_dist / (torso * 1.2))

    def _stability_for_person(self, person: PosePerson) -> float:
        k = person.keypoints_xy
        shoulder_center = self._mean_points(k[[5, 6]])
        foot_center = self._mean_points(k[[15, 16]])
        torso = np.linalg.norm(k[5] - k[11]) + 1e-6
        x_dev = abs(shoulder_center[0] - foot_center[0]) / torso
        hip_center_y = (k[11][1] + k[12][1]) / 2
        support_depth = abs(hip_center_y - foot_center[1]) / torso
        return self._clip((1.0 - x_dev) * 0.7 + support_depth * 0.3)

    def _damage_zh(self, hit: HitEvent | None, unstable: bool, confidence: float) -> str:
        if hit is not None and unstable:
            return "击中同时自身失衡风险上升"
        if hit is not None and hit.target == "head":
            return "击中头部"
        if hit is not None and hit.target == "body":
            return "击中躯干"
        if confidence >= 0.66:
            return "形成压制，迫使对手后撤"
        return "未形成有效击中"

    def _evade_failure_reason(
        self,
        metrics: CombatReviewMetrics,
        action_code: str,
        hit: HitEvent | None,
        fatigue: dict,
    ) -> str:
        if hit is None and metrics.impact_score < 0.55:
            return DEFAULT_EVADE_REASON
        if metrics.guard_open_score >= 0.62:
            return "护架打开，头部/躯干暴露"
        if metrics.balance_break_score >= 0.58:
            return "重心滞后，无法及时撤步"
        if fatigue["level"] == "high" or metrics.reaction_lag_score >= 0.72:
            return "连续对抗后反应下降"
        if metrics.distance_score >= 0.68:
            return "距离来不及拉开"
        if action_code in {"hook_punch", "kick", "block"} and metrics.impact_score >= 0.58:
            return "被假动作或上一步动作牵制"
        return DEFAULT_EVADE_REASON

    def _quartet_reason_zh(self, action_code: str, hit: HitEvent | None, fatigue: dict) -> str:
        meta = ACTION_CATALOG.get(action_code)
        if meta is None:
            return DEFAULT_EVADE_REASON
        if hit is not None:
            return f"{meta['action_zh']}进入有效打击路径，对手未能及时修正护架。"
        if fatigue["level"] == "high":
            return f"{meta['action_zh']}阶段节奏持续施压，对手反应速度下降。"
        return f"{meta['action_zh']}形成节奏压制，但命中证据有限。"

    def _suggestion_zh(self, action_code: str) -> str:
        meta = ACTION_CATALOG.get(action_code)
        if meta is None:
            return "保持基础站姿稳定，继续补充有效证据。"
        return meta["suggestion_zh"]

    def _action_zh(self, action_code: str) -> str:
        return ACTION_CATALOG.get(action_code, {}).get("action_zh", action_code)

    def _encode_crop(self, frame: np.ndarray, attacker: PosePerson | None, defender: PosePerson | None) -> str | None:
        crop = frame
        boxes = []
        if attacker is not None:
            boxes.append(attacker.bbox)
        if defender is not None:
            boxes.append(defender.bbox)
        if boxes:
            x1 = min(box[0] for box in boxes)
            y1 = min(box[1] for box in boxes)
            x2 = max(box[2] for box in boxes)
            y2 = max(box[3] for box in boxes)
            height, width = frame.shape[:2]
            margin_x = max(16, int((x2 - x1) * 0.18))
            margin_y = max(16, int((y2 - y1) * 0.18))
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(width, x2 + margin_x)
            y2 = min(height, y2 + margin_y)
            crop = frame[y1:y2, x1:x2]
        ok, encoded = cv2.imencode(".jpg", crop)
        if not ok:
            return None
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def _format_timestamp(self, frame_index: int, fps: float) -> str:
        seconds = frame_index / max(1.0, fps)
        minutes = int(seconds // 60)
        remain = seconds - (minutes * 60)
        return f"{minutes:02d}:{remain:05.2f}"

    def _mean_points(self, points: np.ndarray) -> np.ndarray:
        return np.mean(points, axis=0)

    def _clip(self, value: float) -> float:
        return float(np.clip(value, 0.0, 1.0))
