from datetime import datetime
from agents.clickhouse_client import get_client

# Synthetic examiner-safe snapshot. These rows do not describe real studio
# operations, provider accounts, catalog identifiers, or collaborators.
DATA_AS_OF = "2026-08-01T00:00:00Z"


def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


PRODUCTION_EVENTS = [
    ("track_demo_horizon", "track", "distribution", "in_review", _dt("2026-07-28 10:00:00"), "Synthetic distributor review"),
    ("track_demo_orbit", "track", "distribution", "not_started", _dt("2026-07-28 10:00:00"), "Synthetic demo row"),
    ("episode_demo_1", "episode", "script", "done", _dt("2026-07-25 09:00:00"), "Synthetic screenplay approved"),
    ("episode_demo_1", "episode", "voice_casting", "in_progress", _dt("2026-07-27 11:00:00"), "Synthetic candidates pending approval"),
    ("episode_demo_1", "episode", "video_gen", "in_progress", _dt("2026-07-29 15:00:00"), "Four synthetic scenes share one angle for compliance demonstration"),
    ("episode_demo_1", "episode", "edit", "not_started", _dt("2026-07-30 09:00:00"), "Synthetic demo row"),
    ("episode_demo_1", "episode", "publish", "not_started", _dt("2026-07-30 09:00:00"), "Synthetic demo row"),
]

CASTING_AND_ASSETS = [
    ("episode_demo_1", "friend_char_white", "status", "not_designed"),
    ("episode_demo_1", "friend_char_latino", "status", "not_designed"),
    ("episode_demo_1", "friend_char_asian", "status", "not_designed"),
    ("episode_demo_1", "demo_lead_a", "voice_candidate", "candidate_a"),
    ("episode_demo_1", "demo_lead_b", "voice_candidate", "candidate_b"),
    ("episode_demo_1", "scene_demo_1", "camera_angle", "push-in"),
    ("episode_demo_1", "scene_demo_2", "camera_angle", "push-in"),
    ("episode_demo_1", "scene_demo_3", "camera_angle", "push-in"),
    ("episode_demo_1", "scene_demo_4", "camera_angle", "push-in"),
    ("track_demo_horizon", "track", "provenance", "original"),
    ("track_demo_orbit", "track", "provenance", "original"),
]


def seed():
    client = get_client()
    client.insert(
        "production_events",
        PRODUCTION_EVENTS,
        column_names=["item_id", "item_type", "stage", "status", "ts", "notes"],
    )
    client.insert(
        "casting_and_assets",
        CASTING_AND_ASSETS,
        column_names=["item_id", "character_or_track", "attribute_key", "attribute_value"],
    )


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(PRODUCTION_EVENTS)} production_events rows, {len(CASTING_AND_ASSETS)} casting_and_assets rows.")
