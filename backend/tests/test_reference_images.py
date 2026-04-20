from __future__ import annotations

from services.reference_images import _is_whitelisted


def test_github_whitelist_allows_known_sources():
    assert _is_whitelisted("https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/docs/images/pose_tracking_full_body_landmarks.png")
    assert _is_whitelisted("https://raw.githubusercontent.com/ultralytics/ultralytics/main/docs/en/images/tasks/pose.jpg")
    assert _is_whitelisted("https://commons.wikimedia.org/wiki/Special:FilePath/Fbiagentsgun.jpg")


def test_github_whitelist_blocks_unknown_sources():
    assert not _is_whitelisted("https://example.com/pose.jpg")
    assert not _is_whitelisted("https://raw.githubusercontent.com/random-user/random-repo/main/test.jpg")
    assert not _is_whitelisted("https://commons.wikimedia.org/wiki/File:SomethingElse.jpg")
