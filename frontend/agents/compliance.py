REQUIRED_DIVERSITY_CHARACTERS = {"friend_char_white", "friend_char_latino", "friend_char_asian"}


def check_diversity(attributes: list[dict]) -> dict:
    designed = {
        a["character_or_track"]
        for a in attributes
        if a["character_or_track"] in REQUIRED_DIVERSITY_CHARACTERS
        and a["attribute_key"] == "status"
        and a["attribute_value"] == "designed"
    }
    missing = sorted(REQUIRED_DIVERSITY_CHARACTERS - designed)
    return {"passed": not missing, "missing": missing}


def check_music_policy(attributes: list[dict]) -> dict:
    provenance = next((a["attribute_value"] for a in attributes if a["attribute_key"] == "provenance"), None)
    return {"passed": provenance == "original", "provenance": provenance}


def check_pacing(attributes: list[dict]) -> dict:
    angles = [a["attribute_value"] for a in attributes if a["attribute_key"] == "camera_angle"]
    passed = len(set(angles)) > 1
    return {"passed": passed, "angles_used": angles}
