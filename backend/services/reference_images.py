from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from settings import settings


ALLOWED_HOSTS = {"raw.githubusercontent.com", "commons.wikimedia.org", "upload.wikimedia.org"}
ALLOWED_REPO_PREFIXES = (
    "/google-ai-edge/mediapipe/",
    "/ultralytics/ultralytics/",
    "/open-mmlab/mmpose/",
    "/wiki/Special:FilePath/",
    "/wikipedia/commons/",
)


@dataclass(frozen=True)
class ReferenceImageResolution:
    selected_url: str
    source_checked: bool
    fallback_used: bool
    reason: str


def _is_whitelisted(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in ALLOWED_HOSTS:
        return False
    return any(parsed.path.startswith(prefix) for prefix in ALLOWED_REPO_PREFIXES)


def _url_reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=timeout) as resp:  # nosec B310: controlled whitelist URL
            return 200 <= int(getattr(resp, "status", 0)) < 400
    except Exception:
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=timeout) as resp:  # nosec B310: controlled whitelist URL
                return 200 <= int(getattr(resp, "status", 0)) < 400
        except Exception:
            return False


def resolve_reference_image() -> ReferenceImageResolution:
    # Prefer first valid whitelisted source to avoid runtime network dependency in backend process.
    for source in settings.github_reference_sources:
        if _is_whitelisted(source):
            return ReferenceImageResolution(
                selected_url=source,
                source_checked=True,
                fallback_used=False,
                reason="whitelist_selected",
            )

    for source in settings.github_reference_sources:
        if not _is_whitelisted(source):
            continue
        if _url_reachable(source):
            return ReferenceImageResolution(
                selected_url=source,
                source_checked=True,
                fallback_used=False,
                reason="github_whitelist_ok",
            )
    return ReferenceImageResolution(
        selected_url=settings.reference_image_fallback,
        source_checked=True,
        fallback_used=True,
        reason="fallback_to_local",
    )
