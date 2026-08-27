from agents.compliance import check_diversity, check_music_policy, check_pacing


def test_check_diversity_fails_when_friend_chars_not_designed():
    attrs = [
        {"character_or_track": "friend_char_white", "attribute_key": "status", "attribute_value": "not_designed"},
        {"character_or_track": "friend_char_latino", "attribute_key": "status", "attribute_value": "not_designed"},
        {"character_or_track": "friend_char_asian", "attribute_key": "status", "attribute_value": "not_designed"},
    ]
    result = check_diversity(attrs)
    assert result["passed"] is False
    assert result["missing"] == ["friend_char_asian", "friend_char_latino", "friend_char_white"]


def test_check_diversity_passes_when_all_designed():
    attrs = [
        {"character_or_track": c, "attribute_key": "status", "attribute_value": "designed"}
        for c in ("friend_char_white", "friend_char_latino", "friend_char_asian")
    ]
    result = check_diversity(attrs)
    assert result["passed"] is True
    assert result["missing"] == []


def test_check_music_policy_passes_for_original():
    attrs = [{"character_or_track": "track", "attribute_key": "provenance", "attribute_value": "original"}]
    assert check_music_policy(attrs)["passed"] is True


def test_check_music_policy_fails_for_missing_provenance():
    assert check_music_policy([])["passed"] is False


def test_check_pacing_fails_when_all_angles_repeat():
    attrs = [
        {"attribute_key": "camera_angle", "attribute_value": "push-in"},
        {"attribute_key": "camera_angle", "attribute_value": "push-in"},
        {"attribute_key": "camera_angle", "attribute_value": "push-in"},
    ]
    result = check_pacing(attrs)
    assert result["passed"] is False
    assert result["angles_used"] == ["push-in", "push-in", "push-in"]


def test_check_pacing_passes_with_varied_angles():
    attrs = [
        {"attribute_key": "camera_angle", "attribute_value": "wide"},
        {"attribute_key": "camera_angle", "attribute_value": "push-in"},
    ]
    assert check_pacing(attrs)["passed"] is True
