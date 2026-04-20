from __future__ import annotations

import os

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

KEYS = {
    "VISION_PRIMARY": os.getenv("VISION_PRIMARY_KEY", NVIDIA_API_KEY),
    "PARSER_NODE": os.getenv("PARSER_NODE_KEY", ""),
    "REWARD_SCORING": os.getenv("REWARD_SCORING_KEY", ""),
}

MODELS = {
    "VISION": os.getenv("VISION_MODEL", "meta/llama-3.2-90b-vision-instruct"),
    "TACTICAL": os.getenv("TACTICAL_MODEL", "meta/llama-3.1-8b-instruct"),
    "PARSER": os.getenv("PARSER_MODEL", "nvidia/nemotron-parse"),
    "REWARD": os.getenv("REWARD_MODEL", "nvidia/llama-3.1-nemotron-70b-reward"),
}

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

