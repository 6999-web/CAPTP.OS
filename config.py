# 智警实战综合训练平台 (CAPTP) 根目录配置文件

NVIDIA_API_KEY = "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"

KEYS = {
    "VISION_PRIMARY": "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",
    "PARSER_NODE": "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",
    "REWARD_SCORING": "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"
}

MODELS = {
    "VISION": "meta/llama-3.2-90b-vision-instruct",
    "TACTICAL": "meta/llama-3.1-8b-instruct",
    "PARSER": "nvidia/nemotron-parse", 
    "REWARD": "nvidia/llama-3.1-nemotron-70b-reward"
}

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
