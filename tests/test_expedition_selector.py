import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without PyYAML
    yaml = SimpleNamespace(safe_load=lambda stream: json.load(stream))  # type: ignore
    sys.modules["yaml"] = yaml  # type: ignore

import aeons_end_expedition_selector as selector


def write_yaml(path: Path, data) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def build_base_data(tmp_path: Path):
    waves = {"boxes": {"Box A": "1st Wave", "Box B": "2nd Wave", "Outcasts": "5th Wave"}}
    settings = {
        "wave_settings": {
            "1st Wave": {"location": "Gravehold"},
            "2nd Wave": {"location": "The Depths"},
            "5th Wave": {"location": "Outcasts"},
        }
    }
    mages = {
        "mages": [
            {"name": "Brama", "variants": [{"name": "Brama", "box": "Box A"}]},
            {"name": "Kadir", "variants": [{"name": "Kadir", "box": "Box A"}]},
            {"name": "Mazra", "variants": [{"name": "Mazra", "box": "Box A"}]},
            {"name": "Rhia", "variants": [{"name": "Rhia", "box": "Box B"}]},
            {"name": "Sura", "variants": [{"name": "Sura", "box": "Outcasts"}]},
        ]
    }
    nemeses = {
        "nemeses": [
            {"name": "Carapace Queen", "battle": 1, "box": "Box A"},
            {"name": "Hollow Crown", "battle": 2, "box": "Box A"},
            {"name": "Crooked Mask", "battle": 3, "box": "Box A"},
            {"name": "Knight of Shackles", "battle": 4, "box": "Box A"},
            {"name": "Seer of Darkfire", "battle": 1, "box": "Box B"},
            {"name": "Prince of Gluttons", "battle": 2, "box": "Box B"},
            {"name": "Wraithmonger", "battle": 3, "box": "Box B"},
            {"name": "Wayward One", "battle": 4, "box": "Box B"},
            {"name": "Horde-Crone", "battle": 4, "box": "Outcasts"},
            {"name": "Siltborn Titan", "battle": 3, "box": "Outcasts"},
            {"name": "Bellowing Serpent", "battle": 1, "box": "Outcasts"},
        ]
    }
    friends = {
        "friends": [
            {"name": "Lost Captain", "box": "Box A"},
            {"name": "Archivist", "box": "Box A"},
            {"name": "Wanderer", "box": "Box A"},
            {"name": "Bandit Queen", "box": "Box A"},
            {"name": "Blacksmith", "box": "Box B"},
            {"name": "Snarecaller", "box": "Outcasts"},
            {"name": "Nomad", "box": "Outcasts"},
            {"name": "Tidecaller", "box": "Outcasts"},
        ]
    }
    foes = {
        "foes": [
            {"name": "Broodling Pack", "box": "Box A"},
            {"name": "Grub Horde", "box": "Box A"},
            {"name": "Silt Stalkers", "box": "Box A"},
            {"name": "Wailing Throng", "box": "Box A"},
            {"name": "Rift Scourge", "box": "Box B"},
            {"name": "Scuttling Swarm", "box": "Outcasts"},
            {"name": "Drowned Thrall", "box": "Outcasts"},
            {"name": "Cinder Brutes", "box": "Outcasts"},
        ]
    }

    paths = {
        "waves": tmp_path / "waves.yaml",
        "settings": tmp_path / "settings.yaml",
        "mages": tmp_path / "mages.yaml",
        "nemeses": tmp_path / "nemeses.yaml",
        "friends": tmp_path / "friends.yaml",
        "foes": tmp_path / "foes.yaml",
    }
    write_yaml(paths["waves"], waves)
    write_yaml(paths["settings"], settings)
    write_yaml(paths["mages"], mages)
    write_yaml(paths["nemeses"], nemeses)
    write_yaml(paths["friends"], friends)
    write_yaml(paths["foes"], foes)
    return paths


def extract_names(items):
    return {selector.name_key(item["name"]) for item in items}


def test_standard_selection_is_collision_free_and_deterministic(tmp_path, monkeypatch):
    paths = build_base_data(tmp_path)
    monkeypatch.setattr(selector, "_now_iso", lambda: "2024-01-01T00:00:00+00:00")

    packet_a = selector.select_expedition(
        seed=12345,
        mage_count=2,
        length="standard",
        content_waves=["1st Wave"],
        content_boxes=[],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
    )
    packet_b = selector.select_expedition(
        seed=12345,
        mage_count=2,
        length="standard",
        content_waves=["1st Wave"],
        content_boxes=[],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
    )

    assert json.dumps(packet_a, sort_keys=True) == json.dumps(packet_b, sort_keys=True)
    assert packet_a["availability"]["include_friend_foe_pair"] is True
    assert len(packet_a["battle_plan"]) == 4

    mage_names = extract_names(packet_a["mages"])
    nemesis_names = extract_names([step["nemesis"] for step in packet_a["battle_plan"]])
    friend_names = extract_names([step["friend"] for step in packet_a["battle_plan"]])
    foe_names = extract_names([step["foe"] for step in packet_a["battle_plan"]])

    assert mage_names.isdisjoint(nemesis_names)
    assert mage_names.isdisjoint(friend_names)
    assert mage_names.isdisjoint(foe_names)
    assert nemesis_names.isdisjoint(friend_names)
    assert nemesis_names.isdisjoint(foe_names)
    assert friend_names.isdisjoint(foe_names)


def test_scope_limits_wave_choice(tmp_path):
    paths = build_base_data(tmp_path)
    write_yaml(paths["friends"], {"friends": [{"name": "Archivist", "box": "Box A"}]})
    write_yaml(paths["foes"], {"foes": [{"name": "Broodling Pack", "box": "Box A"}]})

    packet = selector.select_expedition(
        seed=77,
        mage_count=1,
        length="standard",
        content_waves=["2nd Wave"],
        content_boxes=[],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
    )

    assert packet["setting"]["wave_name"] == "2nd Wave"


def test_short_length_picks_tier_one_when_tier_two_missing(tmp_path):
    paths = build_base_data(tmp_path)
    nemeses = {
        "nemeses": [
            {"name": "Root Tyrant", "battle": 1, "box": "Box A"},
            {"name": "Mindfire Overlord", "battle": 3, "box": "Box A"},
            {"name": "Umbra Titan", "battle": 4, "box": "Box A"},
        ]
    }
    write_yaml(paths["nemeses"], nemeses)

    packet = selector.select_expedition(
        seed=9,
        mage_count=1,
        length="short",
        content_waves=["1st Wave"],
        content_boxes=[],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
    )

    tiers = [step["tier"] for step in packet["battle_plan"]]
    assert tiers[0] == 1
    assert tiers == [1, 3, 4]


def test_outcasts_wave_sets_protect_target(tmp_path):
    paths = build_base_data(tmp_path)

    packet = selector.select_expedition(
        seed=101,
        mage_count=1,
        length="short",
        content_waves=["5th Wave"],
        content_boxes=["Outcasts"],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
    )

    assert packet["setting"]["wave_name"] == "5th Wave"
    assert packet["protect_target"] in {"Gravehold", "Xaxos"}


def test_friend_foe_availability_mismatch_raises(tmp_path):
    paths = build_base_data(tmp_path)
    foes = {"foes": [{"name": "Rift Scourge", "box": "Box B"}]}
    write_yaml(paths["foes"], foes)

    with pytest.raises(ValueError, match="Friend/Foe availability mismatch"):
        selector.select_expedition(
            seed=5,
            mage_count=1,
            length="standard",
            content_waves=["1st Wave"],
            content_boxes=[],
            mages_yaml_path=str(paths["mages"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            nemeses_yaml_path=str(paths["nemeses"]),
            friends_yaml_path=str(paths["friends"]),
            foes_yaml_path=str(paths["foes"]),
        )
