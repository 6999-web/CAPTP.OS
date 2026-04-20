from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from settings import settings
from cv.types import FrameWeaponResult, WeaponDetection


@dataclass
class WeaponEngineStatus:
    yolo_ready: bool


class WeaponEngine:
    def __init__(self) -> None:
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        if not settings.yolo_weapon_model:
            return
        try:
            from ultralytics import YOLO

            self._model = YOLO(settings.yolo_weapon_model)
        except Exception:
            self._model = None

    @property
    def status(self) -> WeaponEngineStatus:
        return WeaponEngineStatus(yolo_ready=self._model is not None)

    def infer(self, frame: np.ndarray) -> FrameWeaponResult:
        result = FrameWeaponResult()
        if self._model is None:
            result.fallback_used = True
            return result

        try:
            outputs = self._model.predict(frame, verbose=False, device=settings.device)
            if not outputs:
                return result

            pred = outputs[0]
            names = pred.names if hasattr(pred, "names") else {}
            boxes = pred.boxes
            if boxes is None:
                return result

            xyxy = boxes.xyxy.cpu().numpy() if boxes.xyxy is not None else []
            cls = boxes.cls.cpu().numpy() if boxes.cls is not None else []
            conf = boxes.conf.cpu().numpy() if boxes.conf is not None else []

            for i in range(len(xyxy)):
                x1, y1, x2, y2 = xyxy[i].astype(int).tolist()
                cls_idx = int(cls[i]) if i < len(cls) else -1
                cls_name = names.get(cls_idx, str(cls_idx)) if isinstance(names, dict) else str(cls_idx)
                score = float(conf[i]) if i < len(conf) else 0.0
                result.weapons.append(
                    WeaponDetection(
                        cls_name=cls_name,
                        bbox=(x1, y1, x2, y2),
                        score=score,
                        muzzle_direction=self._estimate_muzzle_direction((x1, y1, x2, y2)),
                    )
                )
        except Exception:
            result.fallback_used = True

        return result

    def _estimate_muzzle_direction(self, bbox: tuple[int, int, int, int]) -> str:
        x1, y1, x2, y2 = bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        if w >= h * 1.2:
            return "horizontal"
        if h >= w * 1.2:
            return "vertical"
        return "diagonal"

