from __future__ import annotations

from typing import Iterable

from schemas import ShootingEvidence, ShootingIssueEvidence, ShootingPrimaryIssue, ShootingStepReport, Violation


UI_STEP_ORDER = ["receive_weapon", "initial_check", "insert_magazine", "prepare_and_fire", "post_fire_check"]

UI_STEP_LABELS = {
    "receive_weapon": "发枪",
    "initial_check": "初次验枪",
    "insert_magazine": "装弹夹",
    "prepare_and_fire": "射击",
    "post_fire_check": "终次验枪",
}

FLOW_STAGE_TO_UI = {
    "pass_gun_method_1": "receive_weapon",
    "pass_gun_method_2": "receive_weapon",
    "check_weapon": "initial_check",
    "insert_magazine": "insert_magazine",
    "prepare_and_fire": "prepare_and_fire",
    "post_fire_check": "post_fire_check",
}

STEP_ACTION_HINTS = {
    "receive_weapon": ["接枪", "确认接枪方式"],
    "initial_check": ["卸弹匣", "查弹膛", "保险确认"],
    "insert_magazine": ["插入弹匣", "建立待击姿态"],
    "prepare_and_fire": ["拔枪/举枪", "建立等腰三角", "完成射击"],
    "post_fire_check": ["卸下弹匣", "再次查验弹膛"],
}

VIOLATION_META = {
    "NO_PERSON": {
        "title": "画面中未识别到有效人员",
        "step_key": "prepare_and_fire",
        "trigger_reason": "当前帧未检测到可用于射击评估的人体关键点。",
        "why_flagged": [
            "没有人体主体就无法判断枪口方向、姿态和流程动作。",
            "该帧的射击结论可信度不足。",
        ],
        "risk": "系统无法确认当前动作是否安全，评估结果会缺失关键依据。",
        "improvement_suggestion": "请保证人物完整入镜并提升画面清晰度。",
    },
    "SHOULDER_UNLEVEL": {
        "title": "双肩不平，射击平台不稳定",
        "step_key": "prepare_and_fire",
        "trigger_reason": "系统检测到双肩高度差超过稳定持枪阈值。",
        "why_flagged": [
            "双肩不平会导致枪口回正路径不一致。",
            "连续击发时更容易出现左右散布。",
        ],
        "risk": "后坐力传导不均衡，影响稳定控枪。",
        "improvement_suggestion": "收紧核心并让双肩保持近似平齐。",
    },
    "ISO_TRIANGLE_WEAK": {
        "title": "双臂未形成稳定等腰三角",
        "step_key": "prepare_and_fire",
        "trigger_reason": "双臂长度比例或肘部角度未达到标准等腰三角姿态阈值。",
        "why_flagged": [
            "手臂结构不对称会让枪口回正变慢。",
            "双肘角度差异会放大后坐力扰动。",
        ],
        "risk": "击发稳定性下降，目标散布会变大。",
        "improvement_suggestion": "双臂自然前伸、双肘微屈并让肩肘腕形成对称结构。",
    },
    "ARM_NOT_EXTENDED": {
        "title": "手臂前伸不足",
        "step_key": "prepare_and_fire",
        "trigger_reason": "系统检测到双腕到双肩的伸展比例低于稳定射击阈值。",
        "why_flagged": [
            "前伸不足会缩短稳定支撑链条。",
            "击发时更容易把扳机扰动传回躯干。",
        ],
        "risk": "控枪刚性不足，影响击发一致性。",
        "improvement_suggestion": "在不锁死关节的前提下，适度完成双臂前伸。",
    },
    "KNEE_BEND_OUT_OF_RANGE": {
        "title": "膝关节角度不在稳定射击区间",
        "step_key": "prepare_and_fire",
        "trigger_reason": "膝关节平均屈伸角度超出稳定射击推荐区间。",
        "why_flagged": [
            "膝盖过直会降低吸收后坐力能力。",
            "膝盖过屈会让重心上下波动更明显。",
        ],
        "risk": "重心缓冲能力下降，连续射击稳定性受损。",
        "improvement_suggestion": "保持膝盖微屈，让下肢成为柔性支撑。",
    },
    "STANCE_TOO_NARROW": {
        "title": "站位过窄",
        "step_key": "prepare_and_fire",
        "trigger_reason": "双脚间距小于肩宽稳定阈值。",
        "why_flagged": [
            "站位过窄会降低横向稳定性。",
            "受后坐力或外力扰动时更容易失衡。",
        ],
        "risk": "射击和转移过程中容易出现重心偏移。",
        "improvement_suggestion": "至少保持肩宽站姿，留出稳定缓冲空间。",
    },
    "HEAD_NOT_ALIGNED": {
        "title": "头部未保持正向对齐",
        "step_key": "prepare_and_fire",
        "trigger_reason": "鼻尖相对肩线中心偏移超过稳定对准阈值。",
        "why_flagged": [
            "头部偏移会影响瞄准线一致性。",
            "头肩不对齐会带动上身扭转。",
        ],
        "risk": "瞄准基线不稳定，影响射击精度。",
        "improvement_suggestion": "保持头部自然正直，眼线与枪口方向一致。",
    },
    "HANDS_INCOMPLETE": {
        "title": "双手包覆握把不完整",
        "step_key": "prepare_and_fire",
        "trigger_reason": "系统未识别到完整双手握持信息，无法确认双手包覆结构。",
        "why_flagged": [
            "双手包覆不完整会降低控枪稳定性。",
            "支撑手缺失会让后坐力控制明显变差。",
        ],
        "risk": "控枪稳定性和安全性同时下降。",
        "improvement_suggestion": "主手建立高握把，辅手完整包覆并补足支撑。",
    },
    "THUMB_PARALLEL_WEAK": {
        "title": "拇指支撑不稳定",
        "step_key": "prepare_and_fire",
        "trigger_reason": "系统检测到双拇指相对位置未达到稳定支撑阈值。",
        "why_flagged": [
            "拇指支撑弱会降低辅助手对枪身的包覆稳定性。",
            "射击时枪口回位容易出现扭摆。",
        ],
        "risk": "后坐力控制不足，连续击发回位变慢。",
        "improvement_suggestion": "让辅手掌根贴合握把并维持平顺拇指朝向。",
    },
    "EJECTION_PORT_HAND_RISK": {
        "title": "手指过近抛壳口",
        "step_key": "prepare_and_fire",
        "trigger_reason": "手指/拇指与抛壳口区域距离低于安全阈值。",
        "why_flagged": [
            "过近抛壳口会影响枪械正常工作空间。",
            "存在被滑套或抛壳干扰的风险。",
        ],
        "risk": "可能造成安全风险或射击动作中断。",
        "improvement_suggestion": "确保支撑手远离抛壳口及滑套运动路径。",
    },
    "MUZZLE_NON_SAFE_ZONE": {
        "title": "枪口指向非安全区域",
        "step_key": "prepare_and_fire",
        "trigger_reason": "枪口矢量与人员/保护区域方向重合，超出安全方向阈值。",
        "why_flagged": [
            "枪口不得覆盖无关人员或非安全方向。",
            "这是高优先级安全违例。",
        ],
        "risk": "存在严重安全事故风险。",
        "improvement_suggestion": "立即将枪口调整回安全方向并重新建立姿态。",
    },
    "MUZZLE_DIRECTION_RISK": {
        "title": "枪口方向存在风险",
        "step_key": "prepare_and_fire",
        "trigger_reason": "枪口方向未满足安全下靶线/射向判定要求。",
        "why_flagged": [
            "枪口方向偏离安全区会放大事故风险。",
            "方向控制不稳通常和姿态链条失衡一起出现。",
        ],
        "risk": "安全边界不足，评估判定降级。",
        "improvement_suggestion": "重新校正枪口朝向并确认目标线。",
    },
}


def ui_stage_label(flow_stage: str) -> str:
    step_key = FLOW_STAGE_TO_UI.get(flow_stage, "initial_check")
    return UI_STEP_LABELS[step_key]


def _format_timestamp(frame_index: int, fps: float) -> str:
    if fps <= 0:
        return f"帧{frame_index}"
    seconds = frame_index / fps
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def build_primary_issue(violation: Violation, fps: float = 0.0) -> ShootingPrimaryIssue:
    meta = VIOLATION_META.get(
        violation.code,
        {
            "title": violation.description,
            "step_key": "prepare_and_fire",
            "trigger_reason": violation.description,
            "why_flagged": ["该问题由规则引擎触发，需要结合证据帧复核。"],
            "risk": "该问题会降低流程合规性或动作稳定性。",
            "improvement_suggestion": "请对照证据帧修正当前动作。",
        },
    )
    step_key = meta["step_key"]
    evidence = [
        ShootingIssueEvidence(
            frame_index=violation.evidence_frame_idx,
            timestamp=_format_timestamp(violation.evidence_frame_idx, fps),
            label=violation.code,
            confidence=1.0,
            detail=violation.description,
        )
    ]
    return ShootingPrimaryIssue(
        issue_key=violation.code,
        title=meta["title"],
        step_key=step_key,
        step_label_zh=UI_STEP_LABELS[step_key],
        trigger_reason=meta["trigger_reason"],
        why_flagged=list(meta["why_flagged"]),
        risk=meta["risk"],
        improvement_suggestion=meta["improvement_suggestion"],
        evidence=evidence,
    )


def build_step_reports(
    flow_stage: str,
    flow_order_ok: bool,
    violations: Iterable[Violation],
    evidence: list[ShootingEvidence],
    fps: float = 0.0,
) -> tuple[str, list[ShootingStepReport], list[ShootingPrimaryIssue]]:
    current_step = FLOW_STAGE_TO_UI.get(flow_stage, "initial_check")
    issue_models = [build_primary_issue(item, fps=fps) for item in violations]
    issues_by_step: dict[str, list[ShootingPrimaryIssue]] = {key: [] for key in UI_STEP_ORDER}
    for issue in issue_models:
        issues_by_step.setdefault(issue.step_key, []).append(issue)

    evidence_by_step: dict[str, list[ShootingEvidence]] = {key: [] for key in UI_STEP_ORDER}
    for item in evidence:
        step_key = FLOW_STAGE_TO_UI.get(item.label, current_step)
        evidence_by_step.setdefault(step_key, []).append(item)

    current_idx = UI_STEP_ORDER.index(current_step)
    reports: list[ShootingStepReport] = []
    for idx, step_key in enumerate(UI_STEP_ORDER):
        status = "pending"
        if idx < current_idx:
            status = "completed"
        elif idx == current_idx:
            status = "current"
        if issues_by_step.get(step_key):
            status = "issue"

        why_flagged: list[str] = []
        missing_actions: list[str] = []
        if idx == current_idx and not flow_order_ok:
            why_flagged.append("当前步骤存在顺序错误或跳步。")
        if status in {"current", "issue"}:
            missing_actions = STEP_ACTION_HINTS.get(step_key, [])

        reports.append(
            ShootingStepReport(
                step_key=step_key,
                step_label_zh=UI_STEP_LABELS[step_key],
                status=status,
                detected_actions=[item.label for item in evidence_by_step.get(step_key, [])],
                missing_actions=missing_actions,
                issues=issues_by_step.get(step_key, []),
                evidence=evidence_by_step.get(step_key, []),
                why_flagged=why_flagged,
            )
        )

    if not flow_order_ok:
        order_issue = ShootingPrimaryIssue(
            issue_key="FLOW_ORDER_RISK",
            title="流程顺序存在风险",
            step_key=current_step,
            step_label_zh=UI_STEP_LABELS[current_step],
            trigger_reason="当前动作顺序与标准射击 SOP 不一致。",
            why_flagged=[
                "系统检测到流程出现跳步、逆序或缺步。",
                "顺序错误会让验枪、装弹和复核状态不明确。",
            ],
            risk="会放大枪械状态不明和训练评估失真的风险。",
            improvement_suggestion="请回到当前步骤并按 SOP 顺序重新执行。",
            evidence=[
                ShootingIssueEvidence(
                    frame_index=evidence[-1].frame_index if evidence else 0,
                    timestamp=_format_timestamp(evidence[-1].frame_index, fps) if evidence else None,
                    label="flow_order_ok=false",
                    confidence=1.0,
                    detail="流程顺序校验未通过",
                )
            ],
        )
        issue_models.insert(0, order_issue)
        for report in reports:
            if report.step_key == current_step:
                report.issues.insert(0, order_issue)
                if "当前步骤存在顺序错误或跳步。" not in report.why_flagged:
                    report.why_flagged.append("当前步骤存在顺序错误或跳步。")
                report.status = "issue"

    return UI_STEP_LABELS[current_step], reports, issue_models
