from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PosePerson:
    person_id: int
    bbox: tuple[int, int, int, int]
    score: float
    keypoints_xy: np.ndarray  # shape [K,2]
    keypoints_conf: np.ndarray  # shape [K]


@dataclass
class HandLandmarkSet:
    hand_label: str
    points_xy: np.ndarray  # shape [21,2]
    score: float = 0.0


@dataclass
class FramePoseResult:
    persons: list[PosePerson] = field(default_factory=list)
    hands: list[HandLandmarkSet] = field(default_factory=list)
    fallback_used: bool = False


@dataclass
class WeaponDetection:
    cls_name: str
    bbox: tuple[int, int, int, int]
    score: float
    muzzle_direction: str = "unknown"


@dataclass
class FrameWeaponResult:
    weapons: list[WeaponDetection] = field(default_factory=list)
    fallback_used: bool = False

