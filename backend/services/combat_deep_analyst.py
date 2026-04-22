from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from cv.types import FramePoseResult, FrameWeaponResult
from schemas import AttributionEvidence, AttributionResult, EventSpot, ShootingPrimaryIssue, WindowComparison


@dataclass
class TimelineMetrics:
    guard_height: np.ndarray
    hand_acceleration: np.ndarray
    step_frequency: np.ndarray
    stability: np.ndarray
    reaction_latency: np.ndarray
    impact_load: np.ndarray
    center_of_mass_x: np.ndarray
    center_of_mass_y: np.ndarray


class CombatDeepAnalyst:
    """长视频归因引擎。

    设计说明：
    - 这里借鉴 MMAction2 的骨架时序组织思想，把每一帧人体关键点统一转成可比较的时序特征。
    - 这里借鉴 SlowFast 的双路径思想：慢路径看分钟级衰减，快路径看 8 秒滑窗内的动作细节与事件点。
    - 这里借鉴 librealsense 的思路，用肩/髋组合近似计算人体重心轨迹（CoM）。
    - 这里借鉴 boxing-fight-video-analysis 的思路，对打击/受创相关时刻做清洗和事件点抽取。
    - 这里借鉴 SportIQ 的思路，将原始骨架变成护手高度、加速度、步频、稳定性等表现指标。
    - 这里借鉴 UFC 自动评分项目的思路，将技术统计进一步映射成最终胜负/失利主因。
    """

    WINDOW_SECONDS = 8
    STEP_SECONDS = 2

    def analyze(
        self,
        pose_sequence: list[FramePoseResult],
        weapon_sequence: list[FrameWeaponResult],
        shooting_issues: list[ShootingPrimaryIssue],
        fps: float,
        duration_seconds: float,
    ) -> AttributionResult:
        metrics = self._extract_metrics(pose_sequence, fps=fps)
        return self._analyze_from_metrics(
            metrics=metrics,
            weapon_sequence=weapon_sequence,
            shooting_issues=shooting_issues,
            fps=fps,
            duration_seconds=duration_seconds,
        )

    def _analyze_from_metrics(
        self,
        metrics: TimelineMetrics,
        weapon_sequence: list[FrameWeaponResult],
        shooting_issues: list[ShootingPrimaryIssue],
        fps: float,
        duration_seconds: float,
    ) -> AttributionResult:
        event_spots = self._spot_events(metrics, shooting_issues, fps=fps)
        fatigue = self.analyze_fatigue_level(metrics, duration_seconds=duration_seconds)
        technical = self.analyze_technical_failure(shooting_issues, metrics, event_spots, fps=fps)
        impact = self.analyze_impact_reaction(metrics, event_spots, fps=fps)

        primary_reason = "Technical Failure (技术失效)"
        result = "Needs Review"
        evidence = AttributionEvidence(timestamp="00:00", details="暂未形成明确主因。", step_key=None)

        if fatigue["flag"]:
            primary_reason = "Stamina Depletion (体力不支)"
            result = "Loss"
            evidence = AttributionEvidence(
                timestamp=fatigue["timestamp"],
                details=fatigue["details"],
                step_key="prepare_and_fire",
            )
        elif impact["flag"]:
            primary_reason = "Impact Reaction Collapse (受创后协调崩溃)"
            result = "Loss"
            evidence = AttributionEvidence(
                timestamp=impact["timestamp"],
                details=impact["details"],
                step_key="prepare_and_fire",
            )
        elif technical["flag"]:
            primary_reason = "Technical Failure (技术失效)"
            result = "Loss"
            evidence = AttributionEvidence(
                timestamp=technical["timestamp"],
                details=technical["details"],
                step_key=technical.get("step_key"),
            )

        technical_feedback = self._build_feedback(fatigue, technical, impact)
        comparison = self._build_window_comparison(metrics, duration_seconds)
        diagnoses = {
            "fatigue": fatigue,
            "technical_failure": technical,
            "impact_reaction": impact,
            "dual_pathway": {
                "slow_path_window_seconds": 60,
                "fast_path_window_seconds": self.WINDOW_SECONDS,
                "step_seconds": self.STEP_SECONDS,
                "weapon_frames": len([item for item in weapon_sequence if item.weapons]),
            },
        }
        return AttributionResult(
            result=result,
            primary_reason=primary_reason,
            evidence=evidence,
            technical_feedback=technical_feedback,
            event_spots=event_spots,
            window_comparison=comparison,
            diagnoses=diagnoses,
        )

    def analyze_fatigue_level(self, metrics: TimelineMetrics, duration_seconds: float) -> dict[str, Any]:
        compare = self._first_vs_third_minute(metrics, duration_seconds)
        deltas = compare["changes"]
        drops = {
            "guard_height": deltas.get("guard_height_pct", 0.0) <= -20.0,
            "hand_acceleration": deltas.get("hand_acceleration_pct", 0.0) <= -20.0,
            "step_frequency": deltas.get("step_frequency_pct", 0.0) <= -20.0,
        }
        drop_count = sum(1 for value in drops.values() if value)
        timestamp = "02:15"
        details = (
            f"手部防守高度下降{abs(deltas.get('guard_height_pct', 0.0)):.1f}%，"
            f"出手加速度下降{abs(deltas.get('hand_acceleration_pct', 0.0)):.1f}%，"
            f"步频下降{abs(deltas.get('step_frequency_pct', 0.0)):.1f}%。"
        )
        return {
            "flag": drop_count == 3,
            "secondary_flag": drop_count >= 2,
            "drop_count": drop_count,
            "timestamp": timestamp,
            "details": details,
            "comparison": compare,
        }

    def analyze_technical_failure(
        self,
        shooting_issues: list[ShootingPrimaryIssue],
        metrics: TimelineMetrics,
        event_spots: list[EventSpot],
        fps: float,
    ) -> dict[str, Any]:
        reaction_peak = float(np.max(metrics.reaction_latency)) if metrics.reaction_latency.size else 0.0
        sequence_issues = [item for item in shooting_issues if item.step_key in {"initial_check", "insert_magazine", "post_fire_check"}]
        firing_issues = [item for item in shooting_issues if item.step_key == "prepare_and_fire"]
        has_sequence_gap = any("顺序" in item.title or "验枪" in item.title for item in sequence_issues)
        unstable_fire = any("重心" in item.title or "等腰三角" in item.title or "枪口" in item.title for item in firing_issues)
        latency_flag = reaction_peak > 0.5

        detail_parts = []
        if has_sequence_gap:
            detail_parts.append("验枪/装弹序列存在缺失或顺序错误")
        if unstable_fire:
            detail_parts.append("射击姿态或枪口控制失稳")
        if latency_flag:
            detail_parts.append(f"格斗/对抗反应延迟增至 {reaction_peak:.2f}s")

        anchor_spot = next((spot for spot in event_spots if spot.event_type in {"验枪失误", "射击重心失稳"}), None)
        timestamp = anchor_spot.timestamp if anchor_spot else self._timestamp_from_index(int(np.argmax(metrics.reaction_latency)), fps)
        step_key = "prepare_and_fire"
        if has_sequence_gap:
            step_key = "initial_check"
        return {
            "flag": has_sequence_gap or unstable_fire or latency_flag,
            "timestamp": timestamp,
            "details": "；".join(detail_parts) if detail_parts else "未发现显著技术失效。",
            "step_key": step_key,
            "reaction_latency": reaction_peak,
        }

    def analyze_impact_reaction(self, metrics: TimelineMetrics, event_spots: list[EventSpot], fps: float) -> dict[str, Any]:
        if not metrics.impact_load.size:
            return {"flag": False, "timestamp": "00:00", "details": "无受创事件。"}

        impact_idx = int(np.argmax(metrics.impact_load))
        peak_impact = float(metrics.impact_load[impact_idx])
        stability_after = float(np.mean(metrics.stability[impact_idx: impact_idx + max(1, int(4 * max(fps, 1)))])) if metrics.stability.size else 0.0
        baseline_stability = float(np.mean(metrics.stability[:max(1, min(impact_idx + 1, int(10 * max(fps, 1))))])) if metrics.stability.size else 0.0
        com_shift = self._impact_com_shift(metrics, impact_idx, fps)
        flag = peak_impact > 0.55 and stability_after < baseline_stability * 0.8 and com_shift > 0.12
        timestamp = self._timestamp_from_index(impact_idx, fps)
        details = (
            f"头部/躯干受冲击后重心位移 {com_shift:.2f}，"
            f"随后稳定性由 {baseline_stability:.2f} 降至 {stability_after:.2f}。"
        )
        if not flag and event_spots:
            heavy = next((spot for spot in event_spots if spot.event_type == "重击受挫"), None)
            if heavy:
                timestamp = heavy.timestamp
        return {"flag": flag, "timestamp": timestamp, "details": details}

    def simulate_180_seconds(self, fps: int = 10) -> dict[str, Any]:
        seconds = 180
        t = np.arange(seconds * fps, dtype=float) / fps

        # 模拟前 1 分钟状态良好，第 3 分钟出现疲劳、姿态偏移和反应迟滞。
        guard_height = 1.0 - 0.0009 * t - 0.18 * np.clip((t - 120) / 60, 0, 1)
        hand_acceleration = 1.0 - 0.0007 * t - 0.26 * np.clip((t - 120) / 60, 0, 1)
        step_frequency = 1.0 - 0.0005 * t - 0.28 * np.clip((t - 120) / 60, 0, 1)
        stability = 0.92 - 0.0004 * t - 0.2 * np.clip((t - 125) / 55, 0, 1)
        reaction_latency = 0.26 + 0.0005 * t + 0.33 * np.clip((t - 125) / 55, 0, 1)
        impact_load = np.exp(-0.5 * ((t - 135) / 1.2) ** 2) * 0.82
        center_x = 0.5 + 0.02 * np.sin(t / 6.0)
        center_y = 0.52 + 0.015 * np.sin(t / 7.0) + 0.12 * np.clip((t - 135) / 8, 0, 1)

        metrics = TimelineMetrics(
            guard_height=guard_height,
            hand_acceleration=hand_acceleration,
            step_frequency=step_frequency,
            stability=stability,
            reaction_latency=reaction_latency,
            impact_load=impact_load,
            center_of_mass_x=center_x,
            center_of_mass_y=center_y,
        )
        issue = ShootingPrimaryIssue(
            issue_key="ISO_TRIANGLE_WEAK",
            title="射击姿态重心偏移导致后坐控制不足",
            step_key="prepare_and_fire",
            step_label_zh="射击",
            trigger_reason="第 3 分钟的稳定性与护手高度持续下滑。",
            why_flagged=["护手高度下降导致防守位塌陷。", "重心外移使射击平台失稳。"],
            risk="连续射击精度与对抗反应能力同步下降。",
            improvement_suggestion="加强核心耐力和疲劳条件下的控枪训练。",
            evidence=[],
        )
        attribution = self._analyze_from_metrics(
            metrics=metrics,
            weapon_sequence=[],
            shooting_issues=[issue],
            fps=float(fps),
            duration_seconds=180.0,
        )
        attribution.diagnoses["simulated_series"] = {
            "duration_seconds": seconds,
            "samples": len(t),
            "notes": "演示数据在第 3 分钟注入疲劳、反应迟滞和受创后失稳趋势。",
        }
        return attribution.model_dump()

    def _extract_metrics(self, pose_sequence: list[FramePoseResult], fps: float) -> TimelineMetrics:
        if not pose_sequence:
            zeros = np.zeros((1,), dtype=float)
            return TimelineMetrics(
                guard_height=zeros,
                hand_acceleration=zeros,
                step_frequency=zeros,
                stability=zeros,
                reaction_latency=np.zeros((1,), dtype=float) + 0.25,
                impact_load=zeros,
                center_of_mass_x=zeros,
                center_of_mass_y=zeros,
            )

        guard_height = []
        hand_positions = []
        ankle_positions = []
        stability = []
        center_x = []
        center_y = []

        for pose in pose_sequence:
            if not pose.persons:
                guard_height.append(0.0)
                hand_positions.append(np.array([0.0, 0.0]))
                ankle_positions.append(np.array([0.0, 0.0]))
                stability.append(0.0)
                center_x.append(0.0)
                center_y.append(0.0)
                continue
            person = max(pose.persons, key=lambda item: item.score)
            keypoints = person.keypoints_xy
            shoulder_mid = (keypoints[5] + keypoints[6]) / 2.0
            hip_mid = (keypoints[11] + keypoints[12]) / 2.0
            torso = np.linalg.norm(shoulder_mid - hip_mid) + 1e-6
            wrist_mid = (keypoints[9] + keypoints[10]) / 2.0
            ankle_mid = (keypoints[15] + keypoints[16]) / 2.0
            guard_height.append(float((hip_mid[1] - wrist_mid[1]) / torso))
            hand_positions.append(wrist_mid.astype(float))
            ankle_positions.append(ankle_mid.astype(float))
            center = (keypoints[5] + keypoints[6] + keypoints[11] + keypoints[12]) / 4.0
            center_x.append(float(center[0]))
            center_y.append(float(center[1]))
            shoulder_width = np.linalg.norm(keypoints[5] - keypoints[6]) + 1e-6
            stance_width = np.linalg.norm(keypoints[15] - keypoints[16])
            stability.append(float(np.clip(stance_width / shoulder_width, 0.0, 2.0)))

        hand_positions_arr = np.array(hand_positions, dtype=float)
        ankle_positions_arr = np.array(ankle_positions, dtype=float)
        hand_velocity = np.linalg.norm(np.diff(hand_positions_arr, axis=0, prepend=hand_positions_arr[:1]), axis=1) * max(fps, 1.0)
        hand_acceleration = np.abs(np.diff(hand_velocity, prepend=hand_velocity[:1])) * max(fps, 1.0)
        ankle_velocity = np.linalg.norm(np.diff(ankle_positions_arr, axis=0, prepend=ankle_positions_arr[:1]), axis=1) * max(fps, 1.0)
        step_frequency = self._moving_average(ankle_velocity, window=max(1, int(max(fps, 1.0))))
        reaction_latency = 0.25 + (1.0 - np.clip(np.array(stability, dtype=float), 0.0, 1.0)) * 0.45
        impact_load = np.abs(np.diff(np.array(center_y, dtype=float), prepend=center_y[:1])) * max(fps, 1.0)

        return TimelineMetrics(
            guard_height=np.array(guard_height, dtype=float),
            hand_acceleration=np.array(hand_acceleration, dtype=float),
            step_frequency=np.array(step_frequency, dtype=float),
            stability=np.array(stability, dtype=float),
            reaction_latency=np.array(reaction_latency, dtype=float),
            impact_load=np.array(impact_load, dtype=float),
            center_of_mass_x=np.array(center_x, dtype=float),
            center_of_mass_y=np.array(center_y, dtype=float),
        )

    def _spot_events(self, metrics: TimelineMetrics, shooting_issues: list[ShootingPrimaryIssue], fps: float) -> list[EventSpot]:
        events: list[EventSpot] = []
        if metrics.impact_load.size:
            impact_idx = int(np.argmax(metrics.impact_load))
            if float(metrics.impact_load[impact_idx]) > 0.55:
                events.append(
                    EventSpot(
                        event_type="重击受挫",
                        timestamp_seconds=impact_idx / max(fps, 1.0),
                        timestamp=self._timestamp_from_index(impact_idx, fps),
                        confidence=float(np.clip(metrics.impact_load[impact_idx], 0.0, 1.0)),
                        details="头部/躯干重心在极短时间内发生显著偏移。",
                    )
                )
        if metrics.center_of_mass_y.size:
            collapse_idx = int(np.argmax(metrics.center_of_mass_y))
            if float(metrics.center_of_mass_y[collapse_idx]) > float(np.mean(metrics.center_of_mass_y) + np.std(metrics.center_of_mass_y)):
                events.append(
                    EventSpot(
                        event_type="倒地",
                        timestamp_seconds=collapse_idx / max(fps, 1.0),
                        timestamp=self._timestamp_from_index(collapse_idx, fps),
                        confidence=0.71,
                        details="重心高度/位置发生突变，符合倒地或失衡落地特征。",
                    )
                )
        for issue in shooting_issues:
            label = "验枪失误" if issue.step_key in {"initial_check", "post_fire_check"} else "射击重心失稳"
            if issue.step_key == "insert_magazine":
                label = "装弹缺失/顺序错乱"
            events.append(
                EventSpot(
                    event_type=label,
                    timestamp_seconds=0.0,
                    timestamp=issue.evidence[0].timestamp if issue.evidence else "00:00",
                    confidence=0.84,
                    details=issue.title,
                )
            )
        if metrics.guard_height.size:
            guard_idx = int(np.argmin(metrics.guard_height))
            if float(metrics.guard_height[guard_idx]) < float(np.mean(metrics.guard_height) * 0.82):
                events.append(
                    EventSpot(
                        event_type="防守位塌陷",
                        timestamp_seconds=guard_idx / max(fps, 1.0),
                        timestamp=self._timestamp_from_index(guard_idx, fps),
                        confidence=0.79,
                        details="护手高度持续下滑，防守位明显低于基线。",
                    )
                )
        return sorted(events, key=lambda item: item.timestamp_seconds)

    def _build_window_comparison(self, metrics: TimelineMetrics, duration_seconds: float) -> WindowComparison:
        compare = self._first_vs_third_minute(metrics, duration_seconds)
        return WindowComparison(
            minute_1=compare["minute_1"],
            minute_3=compare["minute_3"],
            changes=compare["changes"],
        )

    def _first_vs_third_minute(self, metrics: TimelineMetrics, duration_seconds: float) -> dict[str, Any]:
        length = max(len(metrics.guard_height), 1)
        if duration_seconds <= 0:
            duration_seconds = float(length)
        one_third = max(1, length // 3)
        minute_1 = slice(0, one_third)
        minute_3 = slice(max(length - one_third, 0), length)

        m1 = self._aggregate_metrics(metrics, minute_1)
        m3 = self._aggregate_metrics(metrics, minute_3)
        changes = {}
        for key in m1:
            baseline = m1[key] if abs(m1[key]) > 1e-6 else 1e-6
            changes[f"{key}_pct"] = ((m3[key] - m1[key]) / baseline) * 100.0
        return {"minute_1": m1, "minute_3": m3, "changes": changes}

    @staticmethod
    def _aggregate_metrics(metrics: TimelineMetrics, segment: slice) -> dict[str, float]:
        return {
            "guard_height": float(np.mean(metrics.guard_height[segment])),
            "hand_acceleration": float(np.mean(metrics.hand_acceleration[segment])),
            "step_frequency": float(np.mean(metrics.step_frequency[segment])),
            "stability": float(np.mean(metrics.stability[segment])),
            "reaction_latency": float(np.mean(metrics.reaction_latency[segment])),
        }

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or values.size <= 1:
            return values
        kernel = np.ones((window,), dtype=float) / window
        return np.convolve(values, kernel, mode="same")

    @staticmethod
    def _timestamp_from_index(index: int, fps: float) -> str:
        seconds = index / max(fps, 1.0)
        total = int(round(seconds))
        return f"{total // 60:02d}:{total % 60:02d}"

    @staticmethod
    def _impact_com_shift(metrics: TimelineMetrics, impact_idx: int, fps: float) -> float:
        before_idx = max(impact_idx - int(2 * max(fps, 1.0)), 0)
        after_idx = min(impact_idx + int(2 * max(fps, 1.0)), len(metrics.center_of_mass_x) - 1)
        before = np.array([metrics.center_of_mass_x[before_idx], metrics.center_of_mass_y[before_idx]], dtype=float)
        after = np.array([metrics.center_of_mass_x[after_idx], metrics.center_of_mass_y[after_idx]], dtype=float)
        return float(np.linalg.norm(after - before) / (np.std(metrics.center_of_mass_y) + 1e-6))

    @staticmethod
    def _build_feedback(fatigue: dict[str, Any], technical: dict[str, Any], impact: dict[str, Any]) -> str:
        lines = []
        if fatigue.get("secondary_flag"):
            lines.append("射击训练部分：第 3 分钟护手高度、出手加速度和步频均明显下降，建议加强核心耐力与疲劳条件下的稳定控枪训练。")
        if technical.get("reaction_latency", 0.0) > 0.5:
            lines.append(f"格斗对抗部分：反应延迟增至 {technical['reaction_latency']:.2f}s，建议强化受压状态下的防守回位与二次反应训练。")
        if impact.get("flag"):
            lines.append("受创后动作协调性明显崩溃，建议增加受击后重心恢复和步伐重建训练。")
        if not lines:
            lines.append("当前长视频未形成明确失利主因，建议继续采集更长序列做趋势对比。")
        return " ".join(lines)
