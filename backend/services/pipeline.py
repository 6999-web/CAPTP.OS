from __future__ import annotations

import time
from collections import deque

import cv2
import numpy as np

from schemas import AnalyzeMode, AnalyzeResult, CombatResult, FatigueResult, MetaResult, ShootingEvidence, ShootingFlowStage, ShootingResult
from settings import settings
from cv.action_temporal import ActionTemporalAnalyzer
from cv.combat_analysis import CombatAnalyzer
from cv.fatigue_engine import FatigueEngine
from cv.pose_engine import PoseEngine
from cv.reasoning_bridge import ReasoningBridge
from cv.shooting_rules import ShootingFlowStateMachine, ShootingRulesAnalyzer
from cv.video_input import VideoInputService
from cv.weapon_engine import WeaponEngine
from services.combat_deep_analyst import CombatDeepAnalyst
from services.shooting_reporting import build_step_reports


class VisionPipeline:
    def __init__(self) -> None:
        self.video_input = VideoInputService()
        self.pose_engine = PoseEngine()
        self.weapon_engine = WeaponEngine()
        self.shooting_rules = ShootingRulesAnalyzer()
        self.temporal = ActionTemporalAnalyzer()
        self.combat = CombatAnalyzer()
        self.fatigue = FatigueEngine()
        self.reasoning = ReasoningBridge()
        self.deep_analyst = CombatDeepAnalyst()
        self.stream_pose_window: deque = deque(maxlen=12)
        self.flow_state = ShootingFlowStateMachine()

    def model_health(self) -> dict:
        return {
            "ready": True,
            "runtime_profile": settings.runtime_profile,
            "device": settings.device,
            "loaded_models": {
                "yolo_pose": self.pose_engine.status.yolo_ready,
                "mediapipe": self.pose_engine.status.mediapipe_ready,
                "mmpose": self.pose_engine.status.mmpose_ready,
                "yolo_weapon": self.weapon_engine.status.yolo_ready,
                "mmaction2": self.temporal.status.mmaction_ready,
                "st_gcn": self.temporal.status.stgcn_ready,
                "agcn": self.temporal.status.agcn_ready,
            },
            "versions": {
                "opencv": cv2.__version__,
                "numpy": np.__version__,
            },
        }

    def analyze_file(self, content: bytes, filename: str, content_type: str, mode: AnalyzeMode) -> AnalyzeResult:
        t0 = time.perf_counter()
        source = self.video_input.infer_source_type(filename, content_type)

        if source == "image":
            frame = self.video_input.decode_image(content)
            result = self._analyze_frame_internal(frame, mode=mode, frame_index=0, fps=0.0)
        else:
            bundle = self.video_input.sample_video_bundle(content, max_frames=48, profile="uniform")
            result = self._analyze_sequence_internal(
                bundle["frames"],
                mode=mode,
                fps=bundle["fps"],
                duration_seconds=bundle["duration_seconds"],
                attach_attribution=bundle["duration_seconds"] >= 90.0,
            )

        result.meta.latency_ms = (time.perf_counter() - t0) * 1000.0
        return result

    def analyze_long_video(self, content: bytes, filename: str, content_type: str, mode: AnalyzeMode) -> AnalyzeResult:
        t0 = time.perf_counter()
        source = self.video_input.infer_source_type(filename, content_type)
        if source != "video":
            raise ValueError("Long video endpoint requires video input")

        bundle = self.video_input.sample_video_bundle(content, max_frames=180, profile="slowfast")
        result = self._analyze_sequence_internal(
            bundle["frames"],
            mode=mode,
            fps=bundle["fps"],
            duration_seconds=bundle["duration_seconds"],
            attach_attribution=True,
        )
        result.meta.latency_ms = (time.perf_counter() - t0) * 1000.0
        return result

    def analyze_frame(self, frame: np.ndarray, mode: AnalyzeMode, frame_index: int = 0, fps: float = 0.0) -> AnalyzeResult:
        t0 = time.perf_counter()
        result = self._analyze_frame_internal(frame, mode=mode, frame_index=frame_index, fps=fps)
        result.meta.latency_ms = (time.perf_counter() - t0) * 1000.0
        return result

    def _analyze_sequence_internal(
        self,
        frames: list[np.ndarray],
        mode: AnalyzeMode,
        fps: float,
        duration_seconds: float = 0.0,
        attach_attribution: bool = False,
    ) -> AnalyzeResult:
        pose_seq = []
        weapon_seq = []
        all_hits = []
        all_combat_actions = []
        all_quartets = []
        all_violations = []
        all_evidence = []
        last_shooting = None
        fallback_used = False

        local_flow = ShootingFlowStateMachine()

        for idx, frame in enumerate(frames):
            pose = self.pose_engine.infer(frame, frame_index=idx)
            weapon = self.weapon_engine.infer(frame)
            posture_eval = self.shooting_rules.evaluate_posture(pose, weapon, frame_index=idx)
            event = self.shooting_rules.infer_flow_event(pose, weapon, posture_eval)
            stage = local_flow.ingest(event)

            temporal_one = self.temporal.analyze_frame(pose, weapon)
            combat_actions = self.combat.build_actions(temporal_one.dominant_action, temporal_one.confidence, idx)
            hits = self.combat.estimate_hits(pose, idx)
            evidence_item = ShootingEvidence(
                frame_index=idx,
                label=str(event.value if event else stage.value),
                confidence=temporal_one.confidence,
            )

            pose_seq.append(pose)
            weapon_seq.append(weapon)
            all_combat_actions.extend(combat_actions)
            all_hits.extend(hits)
            all_violations.extend(posture_eval.violations)
            all_evidence.append(evidence_item)
            fallback_used = fallback_used or pose.fallback_used or weapon.fallback_used

            last_shooting = ShootingResult(
                posture_compliance=posture_eval.compliance,
                posture_score=posture_eval.score,
                flow_stage=stage,
                flow_order_ok=local_flow.order_ok,
                violations=list(all_violations),
                evidence=list(all_evidence),
            )

        seq_temporal = self.temporal.analyze_sequence(pose_seq, weapon_seq)
        fatigue = self.fatigue.update(pose_seq)
        quartets = self.combat.build_quartets(all_combat_actions, all_hits, fatigue, fps or 12.0)
        review_cards = self.combat.build_review_cards(
            frames=frames,
            poses=pose_seq,
            actions=all_combat_actions,
            hits=all_hits,
            fatigue=fatigue,
            fps=fps or 12.0,
        )
        all_quartets.extend(quartets)

        combat_result = CombatResult(
            actions=all_combat_actions,
            quartets=all_quartets,
            fatigue=FatigueResult(**fatigue),
            hit_events=all_hits,
            stability=float(np.mean([self.combat.estimate_stability(p) for p in pose_seq])) if pose_seq else 0.0,
            review_cards=review_cards,
            supported_actions=self.combat.supported_actions(),
        )

        if last_shooting is None:
            last_shooting = ShootingResult(
                posture_compliance=False,
                posture_score=0.0,
                flow_stage=ShootingFlowStage.check_weapon,
                flow_order_ok=False,
                violations=[],
                evidence=[],
            )

        ui_stage_label, step_reports, primary_issues = build_step_reports(
            flow_stage=last_shooting.flow_stage.value,
            flow_order_ok=last_shooting.flow_order_ok,
            violations=last_shooting.violations,
            evidence=last_shooting.evidence,
            fps=fps or 0.0,
        )
        last_shooting.ui_stage_label = ui_stage_label
        last_shooting.step_reports = step_reports
        last_shooting.primary_issues = primary_issues

        payload = AnalyzeResult(
            shooting=last_shooting,
            combat=combat_result,
            meta=MetaResult(
                fps=fps,
                persons=len(pose_seq[-1].persons) if pose_seq else 0,
                device=settings.device,
                fallback_used=fallback_used,
            ),
            reasoning=None,
            attribution=None,
        )
        if attach_attribution:
            payload.attribution = self.deep_analyst.analyze(
                pose_sequence=pose_seq,
                weapon_sequence=weapon_seq,
                shooting_issues=primary_issues,
                fps=fps or 1.0,
                duration_seconds=duration_seconds or float(len(frames)),
            )

        low_conf = (seq_temporal.confidence < 0.58) or (not last_shooting.flow_order_ok)
        payload.reasoning = self.reasoning.enrich(payload.model_dump(), low_conf)
        return payload

    def _analyze_frame_internal(self, frame: np.ndarray, mode: AnalyzeMode, frame_index: int, fps: float) -> AnalyzeResult:
        pose = self.pose_engine.infer(frame, frame_index=frame_index)
        weapon = self.weapon_engine.infer(frame)

        posture = self.shooting_rules.evaluate_posture(pose, weapon, frame_index=frame_index)
        event = self.shooting_rules.infer_flow_event(pose, weapon, posture)
        stage = self.flow_state.ingest(event)

        temporal = self.temporal.analyze_frame(pose, weapon)
        actions = self.combat.build_actions(temporal.dominant_action, temporal.confidence, frame_index)
        hits = self.combat.estimate_hits(pose, frame_index)

        self.stream_pose_window.append(pose)
        fatigue_raw = self.fatigue.update(list(self.stream_pose_window))

        quartets = self.combat.build_quartets(actions, hits, fatigue_raw, fps or 12.0)
        stability = self.combat.estimate_stability(pose)
        review_cards = self.combat.build_review_cards(
            frames=[frame],
            poses=[pose],
            actions=actions,
            hits=hits,
            fatigue=fatigue_raw,
            fps=fps or 12.0,
        )
        evidence = [ShootingEvidence(frame_index=frame_index, label=str(event.value if event else stage.value), confidence=temporal.confidence)]
        ui_stage_label, step_reports, primary_issues = build_step_reports(
            flow_stage=stage.value,
            flow_order_ok=self.flow_state.order_ok,
            violations=posture.violations,
            evidence=evidence,
            fps=fps or 0.0,
        )

        shooting = ShootingResult(
            posture_compliance=posture.compliance,
            posture_score=posture.score,
            flow_stage=stage,
            flow_order_ok=self.flow_state.order_ok,
            violations=posture.violations,
            evidence=evidence,
            ui_stage_label=ui_stage_label,
            step_reports=step_reports,
            primary_issues=primary_issues,
        )
        combat = CombatResult(
            actions=actions,
            quartets=quartets,
            fatigue=FatigueResult(**fatigue_raw),
            hit_events=hits,
            stability=stability,
            review_cards=review_cards,
            supported_actions=self.combat.supported_actions(),
        )
        meta = MetaResult(
            fps=fps,
            persons=len(pose.persons),
            device=settings.device,
            fallback_used=pose.fallback_used or weapon.fallback_used,
        )
        output = AnalyzeResult(shooting=shooting, combat=combat, meta=meta, reasoning=None, attribution=None)

        low_conf = temporal.confidence < 0.58
        output.reasoning = self.reasoning.enrich(output.model_dump(), low_conf)
        return output


pipeline = VisionPipeline()
