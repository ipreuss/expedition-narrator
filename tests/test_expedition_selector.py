import json
import sys
from collections import Counter
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

from core import aeons_end_expedition_selector as selector
from core import astro_knights_expedition_selector as astro_selector


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


def build_multi_wave_data(tmp_path: Path):
    """Build test data with content across multiple waves for strictness testing."""
    waves = {"boxes": {"Box A": "1st Wave", "Box B": "2nd Wave"}}
    settings = {
        "wave_settings": {
            "1st Wave": {"location": "Gravehold"},
            "2nd Wave": {"location": "The Depths"},
        }
    }
    mages = {
        "mages": [
            {"name": "Brama", "variants": [{"name": "Brama", "box": "Box A"}]},
            {"name": "Kadir", "variants": [{"name": "Kadir", "box": "Box A"}]},
            {"name": "Mazra", "variants": [{"name": "Mazra", "box": "Box A"}]},
            {"name": "Rhia", "variants": [{"name": "Rhia", "box": "Box B"}]},
            {"name": "Sura", "variants": [{"name": "Sura", "box": "Box B"}]},
            {"name": "Tala", "variants": [{"name": "Tala", "box": "Box B"}]},
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
        ]
    }
    friends = {
        "friends": [
            {"name": "Lost Captain", "box": "Box A"},
            {"name": "Archivist", "box": "Box A"},
            {"name": "Wanderer", "box": "Box A"},
            {"name": "Bandit Queen", "box": "Box A"},
            {"name": "Blacksmith", "box": "Box B"},
            {"name": "Scholar", "box": "Box B"},
            {"name": "Healer", "box": "Box B"},
            {"name": "Scout", "box": "Box B"},
        ]
    }
    foes = {
        "foes": [
            {"name": "Broodling Pack", "box": "Box A"},
            {"name": "Grub Horde", "box": "Box A"},
            {"name": "Silt Stalkers", "box": "Box A"},
            {"name": "Wailing Throng", "box": "Box A"},
            {"name": "Rift Scourge", "box": "Box B"},
            {"name": "Dark Horde", "box": "Box B"},
            {"name": "Shadow Beasts", "box": "Box B"},
            {"name": "Void Spawn", "box": "Box B"},
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
    return paths, waves


def build_astro_knights_data(tmp_path: Path):
    waves = {
        "boxes": {
            "Astro Knights - Eternity": "2nd Wave",
            "Mystery of Solarus": "2nd Wave",
        }
    }
    settings = {
        "wave_settings": {
            "2nd Wave": {
                "setting": "The Eternity frontier",
                "mood": "Scrappy cosmic defense",
            }
        }
    }
    knights = {
        "knights": [
            {
                "name": "Caleb",
                "variants": [{"name": "Caleb", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Pan",
                "variants": [{"name": "Pan", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Tsana",
                "variants": [{"name": "Tsana", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Reshi",
                "variants": [{"name": "Reshi", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Z.A.K.",
                "variants": [{"name": "Z.A.K.", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Rex and Shield-Bo",
                "variants": [{"name": "Rex and Shield-Bo", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Naoko",
                "variants": [{"name": "Naoko", "box": "Mystery of Solarus", "wave_name": "2nd Wave"}],
            },
            {
                "name": "Sunshine",
                "variants": [{"name": "Sunshine", "box": "Mystery of Solarus", "wave_name": "2nd Wave"}],
            },
        ]
    }
    bosses = {
        "bosses": [
            {
                "name": "Dirathian Behemoth",
                "box": "Astro Knights - Eternity",
                "wave_name": "2nd Wave",
                "battle_difficulties": {"1": "normal", "4": "expert"},
            },
            {
                "name": "Shade Sculptor",
                "box": "Mystery of Solarus",
                "wave_name": "2nd Wave",
                "battle_difficulties": {"1": "normal", "4": "expert"},
            },
            {
                "name": "Volt Fusion",
                "box": "Astro Knights - Eternity",
                "wave_name": "2nd Wave",
                "battle_difficulties": {"2": "normal", "4": "expert"},
            },
            {
                "name": "Solar Collision",
                "box": "Astro Knights - Eternity",
                "wave_name": "2nd Wave",
                "battle_difficulties": {"2": "normal", "3": "expert"},
            },
            {
                "name": "Eternity",
                "box": "Astro Knights - Eternity",
                "wave_name": "2nd Wave",
                "battle_difficulties": {"2": "normal", "4": "expert"},
            },
        ]
    }
    homeworlds = {
        "homeworlds": [
            {"name": "The Galactic Bazaar", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"},
            {"name": "Dirath", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"},
            {"name": "Felis", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"},
            {"name": "The Bobcat", "box": "Astro Knights - Eternity", "wave_name": "2nd Wave"},
            {"name": "Eos", "box": "Mystery of Solarus", "wave_name": "2nd Wave"},
        ]
    }

    paths = {
        "waves": tmp_path / "astro_waves.yaml",
        "settings": tmp_path / "astro_settings.yaml",
        "knights": tmp_path / "astro_knights.yaml",
        "bosses": tmp_path / "astro_bosses.yaml",
        "homeworlds": tmp_path / "astro_homeworlds.yaml",
    }
    write_yaml(paths["waves"], waves)
    write_yaml(paths["settings"], settings)
    write_yaml(paths["knights"], knights)
    write_yaml(paths["bosses"], bosses)
    write_yaml(paths["homeworlds"], homeworlds)
    return paths


def get_entity_boxes(packet, waves_mapping):
    """Extract box info from all entities in a packet."""
    boxes = {"mages": [], "nemeses": [], "friends": [], "foes": []}

    for mage in packet["mages"]:
        boxes["mages"].append(mage["chosen_variant"]["box"])

    for step in packet["battle_plan"]:
        boxes["nemeses"].append(step["nemesis"]["box"])
        if step["friend"]:
            boxes["friends"].append(step["friend"]["box"])
        if step["foe"]:
            boxes["foes"].append(step["foe"]["box"])

    return boxes


def test_strictness_thematic_restricts_all_to_same_wave(tmp_path):
    """Thematic strictness: all entities must come from the same wave as setting."""
    paths, waves_data = build_multi_wave_data(tmp_path)
    box_to_wave = waves_data["boxes"]

    # Run multiple times to ensure consistency
    for seed in [1, 42, 100, 999]:
        packet = selector.select_expedition(
            seed=seed,
            mage_count=2,
            length="standard",
            content_waves=["1st Wave", "2nd Wave"],
            content_boxes=[],
            mages_yaml_path=str(paths["mages"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            nemeses_yaml_path=str(paths["nemeses"]),
            friends_yaml_path=str(paths["friends"]),
            foes_yaml_path=str(paths["foes"]),
            strictness="thematic",
        )

        chosen_wave = packet["setting"]["wave_name"]
        entity_boxes = get_entity_boxes(packet, box_to_wave)

        # All entities should be from boxes belonging to the chosen wave
        for mage_box in entity_boxes["mages"]:
            assert box_to_wave[mage_box] == chosen_wave, f"Mage from {mage_box} not in {chosen_wave}"
        for nem_box in entity_boxes["nemeses"]:
            assert box_to_wave[nem_box] == chosen_wave, f"Nemesis from {nem_box} not in {chosen_wave}"
        for friend_box in entity_boxes["friends"]:
            assert box_to_wave[friend_box] == chosen_wave, f"Friend from {friend_box} not in {chosen_wave}"
        for foe_box in entity_boxes["foes"]:
            assert box_to_wave[foe_box] == chosen_wave, f"Foe from {foe_box} not in {chosen_wave}"

        # Verify strictness is recorded in metadata
        assert packet["meta"]["inputs"]["strictness"] == "thematic"


def test_strictness_mixed_restricts_mages_only(tmp_path):
    """Mixed strictness: mages from same wave as setting, others can be from any wave."""
    paths, waves_data = build_multi_wave_data(tmp_path)
    box_to_wave = waves_data["boxes"]

    # Run multiple times
    for seed in [1, 42, 100, 999]:
        packet = selector.select_expedition(
            seed=seed,
            mage_count=2,
            length="standard",
            content_waves=["1st Wave", "2nd Wave"],
            content_boxes=[],
            mages_yaml_path=str(paths["mages"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            nemeses_yaml_path=str(paths["nemeses"]),
            friends_yaml_path=str(paths["friends"]),
            foes_yaml_path=str(paths["foes"]),
            strictness="mixed",
        )

        chosen_wave = packet["setting"]["wave_name"]
        entity_boxes = get_entity_boxes(packet, box_to_wave)

        # Mages should be from boxes belonging to the chosen wave
        for mage_box in entity_boxes["mages"]:
            assert box_to_wave[mage_box] == chosen_wave, f"Mage from {mage_box} not in {chosen_wave}"

        # Nemeses, friends, foes can be from any wave (no assertion on wave matching)
        # Just verify they exist and are valid boxes
        for nem_box in entity_boxes["nemeses"]:
            assert nem_box in box_to_wave
        for friend_box in entity_boxes["friends"]:
            assert friend_box in box_to_wave
        for foe_box in entity_boxes["foes"]:
            assert foe_box in box_to_wave

        assert packet["meta"]["inputs"]["strictness"] == "mixed"


def test_strictness_open_allows_cross_wave(tmp_path):
    """Open strictness: all entities can be from any wave."""
    paths, waves_data = build_multi_wave_data(tmp_path)
    box_to_wave = waves_data["boxes"]

    # With open strictness and all waves allowed, we might get cross-wave selections
    # Run multiple times to increase chance of seeing cross-wave mixing
    found_cross_wave = False
    for seed in range(1, 50):
        packet = selector.select_expedition(
            seed=seed,
            mage_count=2,
            length="standard",
            content_waves=["1st Wave", "2nd Wave"],
            content_boxes=[],
            mages_yaml_path=str(paths["mages"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            nemeses_yaml_path=str(paths["nemeses"]),
            friends_yaml_path=str(paths["friends"]),
            foes_yaml_path=str(paths["foes"]),
            strictness="open",
        )

        chosen_wave = packet["setting"]["wave_name"]
        entity_boxes = get_entity_boxes(packet, box_to_wave)

        # Check if any entity is from a different wave than the setting
        all_boxes = entity_boxes["mages"] + entity_boxes["nemeses"] + entity_boxes["friends"] + entity_boxes["foes"]
        waves_used = {box_to_wave[box] for box in all_boxes}

        if len(waves_used) > 1:
            found_cross_wave = True
            break

        assert packet["meta"]["inputs"]["strictness"] == "open"

    # With enough seeds, we should find at least one cross-wave selection
    assert found_cross_wave, "Expected to find cross-wave entity selection with open strictness"


def test_strictness_default_is_open(tmp_path):
    """Default strictness should be 'open'."""
    paths = build_base_data(tmp_path)

    packet = selector.select_expedition(
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
        # No strictness parameter - should default to "open"
    )

    assert packet["meta"]["inputs"]["strictness"] == "open"


def test_strictness_invalid_value_raises(tmp_path):
    """Invalid strictness value should raise ValueError."""
    paths = build_base_data(tmp_path)

    with pytest.raises(ValueError, match="strictness must be one of"):
        selector.select_expedition(
            seed=1,
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
            strictness="invalid",
        )


def test_astro_knights_selection_is_deterministic(tmp_path, monkeypatch):
    paths = build_astro_knights_data(tmp_path)
    monkeypatch.setattr(astro_selector, "_now_iso", lambda: "2024-01-01T00:00:00+00:00")

    packet_a = astro_selector.select_expedition(
        seed=99,
        mage_count=2,
        length="standard",
        content_waves=[],
        content_boxes=["Astro Knights - Eternity"],
        knights_yaml_path=str(paths["knights"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        bosses_yaml_path=str(paths["bosses"]),
        homeworlds_yaml_path=str(paths["homeworlds"]),
        expedition_difficulty="advanced",
    )
    packet_b = astro_selector.select_expedition(
        seed=99,
        mage_count=2,
        length="standard",
        content_waves=[],
        content_boxes=["Astro Knights - Eternity"],
        knights_yaml_path=str(paths["knights"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        bosses_yaml_path=str(paths["bosses"]),
        homeworlds_yaml_path=str(paths["homeworlds"]),
        expedition_difficulty="advanced",
    )

    assert json.dumps(packet_a, sort_keys=True) == json.dumps(packet_b, sort_keys=True)
    assert packet_a["setting"]["wave_name"] == "2nd Wave"
    assert packet_a["availability"]["include_friend_foe_pair"] is False
    assert len(packet_a["battle_plan"]) == 4
    assert [step["battle_index"] for step in packet_a["battle_plan"]] == [1, 2, 3, 4]
    assert packet_a["homeworld"]["box"] == "Astro Knights - Eternity"
    assert packet_a["protect_target"] == packet_a["homeworld"]["name"]
    assert packet_a["homeworld"]["name"] in {
        "The Galactic Bazaar",
        "Dirath",
        "Felis",
        "The Bobcat",
    }
    assert packet_a["meta"]["inputs"]["expedition_difficulty"] == "advanced"
    assert [step["boss_difficulty"] for step in packet_a["battle_plan"]] == ["expert", "expert", "nightmare", "nightmare"]
    assert packet_a["final_nemesis"]["battle"] == 4
    assert packet_a["final_nemesis"]["boss_difficulty"] == "nightmare"

    knight_names = extract_names(packet_a["mages"])
    boss_names = extract_names([step["nemesis"] for step in packet_a["battle_plan"]])
    assert knight_names.isdisjoint(boss_names)
    assert len(boss_names) == 4


def test_astro_knights_box_scope_limits_selection(tmp_path):
    paths = build_astro_knights_data(tmp_path)

    packet = astro_selector.select_expedition(
        seed=7,
        mage_count=2,
        length="standard",
        content_waves=[],
        content_boxes=["Astro Knights - Eternity"],
        knights_yaml_path=str(paths["knights"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        bosses_yaml_path=str(paths["bosses"]),
        homeworlds_yaml_path=str(paths["homeworlds"]),
        expedition_difficulty="legendary",
    )

    assert packet["homeworld"]["box"] == "Astro Knights - Eternity"
    assert packet["homeworld"]["name"] in {
        "The Galactic Bazaar",
        "Dirath",
        "Felis",
        "The Bobcat",
    }
    assert [step["battle_index"] for step in packet["battle_plan"]] == [1, 2, 3, 4]
    assert packet["battle_plan"][0]["nemesis"]["name"] == "Dirathian Behemoth"
    assert packet["battle_plan"][2]["nemesis"]["name"] == "Solar Collision"
    assert packet["final_nemesis"]["boss_difficulty"] == "apocalypse"
    assert {mage["chosen_variant"]["box"] for mage in packet["mages"]} == {"Astro Knights - Eternity"}


def test_astro_knights_standard_maps_to_normal_boss_difficulty(tmp_path):
    paths = build_astro_knights_data(tmp_path)

    packet = astro_selector.select_expedition(
        seed=5,
        mage_count=2,
        length="standard",
        content_waves=["2nd Wave"],
        content_boxes=[],
        knights_yaml_path=str(paths["knights"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        bosses_yaml_path=str(paths["bosses"]),
        homeworlds_yaml_path=str(paths["homeworlds"]),
        expedition_difficulty="standard",
    )

    assert [step["boss_difficulty"] for step in packet["battle_plan"]] == ["normal", "normal", "expert", "expert"]


def test_astro_knights_solarus_scope_lacks_full_battle_coverage(tmp_path):
    paths = build_astro_knights_data(tmp_path)

    with pytest.raises(RuntimeError, match="unique Astro Knights boss plan"):
        astro_selector.select_expedition(
            seed=7,
            mage_count=2,
            length="standard",
            content_waves=[],
            content_boxes=["Mystery of Solarus"],
            knights_yaml_path=str(paths["knights"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            bosses_yaml_path=str(paths["bosses"]),
            homeworlds_yaml_path=str(paths["homeworlds"]),
            expedition_difficulty="advanced",
        )


def test_astro_knights_requires_full_battle_coverage(tmp_path):
    paths = build_astro_knights_data(tmp_path)

    with pytest.raises(RuntimeError, match="unique Astro Knights boss plan"):
        astro_selector.select_expedition(
            seed=7,
            mage_count=2,
            length="standard",
            content_waves=[],
            content_boxes=["Mystery of Solarus"],
            knights_yaml_path=str(paths["knights"]),
            settings_yaml_path=str(paths["settings"]),
            waves_yaml_path=str(paths["waves"]),
            bosses_yaml_path=str(paths["bosses"]),
            homeworlds_yaml_path=str(paths["homeworlds"]),
            expedition_difficulty="standard",
        )


def test_astro_knights_battle_specific_difficulty_mapping():
    boss = {
        "name": "Continnua",
        "battle_difficulties": {
            "1": "normal",
            "2": "expert",
        },
    }

    assert astro_selector.resolve_boss_difficulty(boss, "standard", battle_index=2) == "expert"
    assert astro_selector.resolve_boss_difficulty(boss, "advanced", battle_index=2) == "nightmare"
    assert astro_selector.resolve_boss_difficulty(boss, "legendary", battle_index=2) == "apocalypse"


def test_astro_knights_boss_supports_specific_battle():
    boss = {
        "name": "Continnua",
        "battle_difficulties": {
            "1": "normal",
            "2": "expert",
        },
    }

    assert astro_selector.boss_supports_battle(boss, 1) is True
    assert astro_selector.boss_supports_battle(boss, 2) is True
    assert astro_selector.boss_supports_battle(boss, 3) is False


def test_astro_knights_replacement_respects_existing_party(tmp_path, monkeypatch):
    paths = build_astro_knights_data(tmp_path)
    monkeypatch.setattr(astro_selector, "_now_iso", lambda: "2024-01-01T00:00:00+00:00")

    packet = astro_selector.select_replacement_mage(
        seed=12,
        existing_mage_names=["Naoko"],
        content_waves=[],
        content_boxes=["Mystery of Solarus", "Astro Knights - Eternity"],
        knights_yaml_path=str(paths["knights"]),
        waves_yaml_path=str(paths["waves"]),
    )

    assert packet["mage"]["name"] != "Naoko"
    assert packet["meta"]["effective_seed"] == 12


def test_production_yaml_files_are_valid():
    """Ensure all production YAML files can be parsed without errors."""
    import yaml

    production_files = [
        "games/aeons_end/data/aeons_end_mages.yaml",
        "games/aeons_end/data/aeons_end_nemeses.yaml",
        "games/aeons_end/data/aeons_end_waves.yaml",
        "games/aeons_end/data/wave_settings.yaml",
        "games/aeons_end/data/aeons_end_friends.yaml",
        "games/aeons_end/data/aeons_end_foes.yaml",
        "games/astro_knights/data/astro_knights_knights.yaml",
        "games/astro_knights/data/astro_knights_bosses.yaml",
        "games/astro_knights/data/astro_knights_homeworlds.yaml",
        "games/astro_knights/data/astro_knights_waves.yaml",
        "games/astro_knights/data/wave_settings.yaml",
    ]

    for filename in production_files:
        filepath = ROOT / filename
        if filepath.exists():
            with open(filepath, encoding="utf-8") as fp:
                yaml.safe_load(fp)  # raises if invalid YAML


def test_production_nemeses_have_no_duplicate_name_per_box():
    """Nemesis entries must be unique per (name, box)."""
    import yaml

    filepath = ROOT / "games/aeons_end/data/aeons_end_nemeses.yaml"
    with open(filepath, encoding="utf-8") as fp:
        nemeses = yaml.safe_load(fp)["nemeses"]

    counts = Counter((selector.name_key(entry["name"]), entry.get("box")) for entry in nemeses)
    duplicates = [
        (name, box, count)
        for (name, box), count in sorted(counts.items())
        if count > 1
    ]

    assert not duplicates, f"Duplicate nemesis entries per box found: {duplicates}"


def test_production_mage_variants_have_no_duplicate_mage_per_box():
    """A mage can have variants across waves, but should be unique within a box."""
    import yaml

    filepath = ROOT / "games/aeons_end/data/aeons_end_mages.yaml"
    with open(filepath, encoding="utf-8") as fp:
        mages = yaml.safe_load(fp)["mages"]

    counts = Counter()
    for mage in mages:
        mage_name = selector.name_key(mage["name"])
        for variant in mage.get("variants", []):
            counts[(mage_name, variant.get("box"))] += 1

    duplicates = [
        (name, box, count)
        for (name, box), count in sorted(counts.items())
        if count > 1
    ]

    assert not duplicates, f"Duplicate mage variants per box found: {duplicates}"


def test_production_astro_knights_eternity_homeworlds_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_homeworlds.yaml"
    with open(filepath, encoding="utf-8") as fp:
        homeworlds = yaml.safe_load(fp)["homeworlds"]

    eternity_homeworlds = {
        entry["name"]
        for entry in homeworlds
        if entry.get("box") == "Astro Knights - Eternity"
    }

    assert eternity_homeworlds == {
        "The Galactic Bazaar",
        "Dirath",
        "Felis",
        "The Bobcat",
    }


def test_production_astro_knights_eternity_knights_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_knights.yaml"
    with open(filepath, encoding="utf-8") as fp:
        knights = yaml.safe_load(fp)["knights"]

    eternity_knights = {
        entry["name"]
        for entry in knights
        if any(variant.get("box") == "Astro Knights - Eternity" for variant in entry.get("variants", []))
    }

    assert eternity_knights == {
        "Caleb",
        "Pan",
        "Tsana",
        "Reshi",
        "Z.A.K.",
        "Rex and Shield-Bo",
    }


def test_production_astro_knights_base_box_knights_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_knights.yaml"
    with open(filepath, encoding="utf-8") as fp:
        knights = yaml.safe_load(fp)["knights"]

    base_box_knights = {
        entry["name"]
        for entry in knights
        if any(variant.get("box") == "Astro Knights" for variant in entry.get("variants", []))
    }

    assert base_box_knights == {
        "Christina Ngara",
        "Gavriil",
        "Toli Iridia",
        "Silas T'Ferran",
        "Z.A.K.",
        "Nasma Gueramana",
    }


def test_production_astro_knights_zak_has_base_and_eternity_variants():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_knights.yaml"
    with open(filepath, encoding="utf-8") as fp:
        knights = yaml.safe_load(fp)["knights"]

    by_name = {entry["name"]: entry for entry in knights}
    zak_boxes = {variant.get("box") for variant in by_name["Z.A.K."].get("variants", [])}

    assert zak_boxes == {"Astro Knights", "Astro Knights - Eternity"}


def test_production_astro_knights_orion_system_knights_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_knights.yaml"
    with open(filepath, encoding="utf-8") as fp:
        knights = yaml.safe_load(fp)["knights"]

    orion_knights = {
        entry["name"]
        for entry in knights
        if any(variant.get("box") == "The Orion System" for variant in entry.get("variants", []))
    }

    assert orion_knights == {
        "Deleth",
        "Alexios Berada",
    }


def test_production_astro_knights_savage_skies_knights_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_knights.yaml"
    with open(filepath, encoding="utf-8") as fp:
        knights = yaml.safe_load(fp)["knights"]

    savage_skies_knights = {
        entry["name"]
        for entry in knights
        if any(variant.get("box") == "Savage Skies" for variant in entry.get("variants", []))
    }

    assert savage_skies_knights == {
        "Scuttlebutt",
        "Tala Cadiz",
    }


def test_production_astro_knights_orion_system_bosses_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"
    with open(filepath, encoding="utf-8") as fp:
        bosses = yaml.safe_load(fp)["bosses"]

    orion_bosses = {
        entry["name"]
        for entry in bosses
        if entry.get("box") == "The Orion System"
    }

    assert orion_bosses == {
        "Fission Parasite",
    }


def test_production_astro_knights_savage_skies_bosses_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"
    with open(filepath, encoding="utf-8") as fp:
        bosses = yaml.safe_load(fp)["bosses"]

    savage_skies_bosses = {
        entry["name"]
        for entry in bosses
        if entry.get("box") == "Savage Skies"
    }

    assert savage_skies_bosses == {
        "The Blackhole Galleon",
    }


def test_production_astro_knights_base_box_bosses_match_expected_set():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"
    with open(filepath, encoding="utf-8") as fp:
        bosses = yaml.safe_load(fp)["bosses"]

    base_box_bosses = {
        entry["name"]
        for entry in bosses
        if entry.get("box") == "Astro Knights"
    }

    assert base_box_bosses == {
        "Continnua",
        "Lunaris",
        "Architect 0-815",
        "Furion",
    }


def test_production_astro_knights_base_box_scope_supports_full_expedition(monkeypatch):
    monkeypatch.setattr(astro_selector, "_now_iso", lambda: "2024-01-01T00:00:00+00:00")

    packet = astro_selector.select_expedition(
        seed=321,
        mage_count=2,
        length="standard",
        content_waves=[],
        content_boxes=["Astro Knights"],
        knights_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_knights.yaml"),
        settings_yaml_path=str(ROOT / "games/astro_knights/data/wave_settings.yaml"),
        waves_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_waves.yaml"),
        bosses_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"),
        homeworlds_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_homeworlds.yaml"),
        expedition_difficulty="advanced",
    )

    assert packet["setting"]["wave_name"] == "1st Wave"
    assert packet["homeworld"]["box"] == "Astro Knights"
    assert [step["battle_index"] for step in packet["battle_plan"]] == [1, 2, 3, 4]
    assert {step["nemesis"]["box"] for step in packet["battle_plan"]} == {"Astro Knights"}
    assert len({step["nemesis"]["name"] for step in packet["battle_plan"]}) == 4
    assert {mage["chosen_variant"]["box"] for mage in packet["mages"]} == {"Astro Knights"}
    assert packet["final_nemesis"]["battle"] == 4


def test_production_astro_knights_known_eternity_boss_battle_difficulties():
    import yaml

    filepath = ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"
    with open(filepath, encoding="utf-8") as fp:
        bosses = yaml.safe_load(fp)["bosses"]

    by_name = {entry["name"]: entry for entry in bosses}

    assert by_name["Shade Sculptor"]["battle_difficulties"] == {1: "normal", 4: "expert"}
    assert by_name["Dirathian Behemoth"]["battle_difficulties"] == {1: "normal"}
    assert by_name["Volt Fusion"]["battle_difficulties"] == {2: "normal", 4: "expert"}
    assert by_name["Solar Collision"]["battle_difficulties"] == {2: "normal", 3: "expert"}
    assert by_name["Eternity"]["battle_difficulties"] == {2: "normal", 4: "expert"}


def test_production_astro_knights_eternity_scope_supports_full_expedition(monkeypatch):
    monkeypatch.setattr(astro_selector, "_now_iso", lambda: "2024-01-01T00:00:00+00:00")

    packet = astro_selector.select_expedition(
        seed=123,
        mage_count=2,
        length="standard",
        content_waves=[],
        content_boxes=["Astro Knights - Eternity"],
        knights_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_knights.yaml"),
        settings_yaml_path=str(ROOT / "games/astro_knights/data/wave_settings.yaml"),
        waves_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_waves.yaml"),
        bosses_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_bosses.yaml"),
        homeworlds_yaml_path=str(ROOT / "games/astro_knights/data/astro_knights_homeworlds.yaml"),
        expedition_difficulty="advanced",
    )

    assert packet["homeworld"]["box"] == "Astro Knights - Eternity"
    assert [step["battle_index"] for step in packet["battle_plan"]] == [1, 2, 3, 4]
    assert {step["nemesis"]["box"] for step in packet["battle_plan"]} == {"Astro Knights - Eternity"}
    assert len({step["nemesis"]["name"] for step in packet["battle_plan"]}) == 4
    assert packet["final_nemesis"]["battle"] == 4


def test_get_available_settings():
    """Test that get_available_settings returns correct structure."""
    from core.aeons_end_expedition_selector import get_available_settings

    result = get_available_settings(
        settings_yaml_path=str(ROOT / "games/aeons_end/data/wave_settings.yaml"),
        waves_yaml_path=str(ROOT / "games/aeons_end/data/aeons_end_waves.yaml"),
    )

    assert "waves" in result
    assert isinstance(result["waves"], list)
    assert len(result["waves"]) > 0

    # Check structure of each wave entry
    for wave in result["waves"]:
        assert "name" in wave
        assert "variants" in wave
        assert isinstance(wave["name"], str)
        assert wave["variants"] is None or isinstance(wave["variants"], list)

    # Check that Wave 7 has variants (past/future)
    wave_7 = next((w for w in result["waves"] if "7th" in w["name"]), None)
    assert wave_7 is not None
    assert wave_7["variants"] is not None
    assert "past" in wave_7["variants"]
    assert "future" in wave_7["variants"]

    # Check that Wave 8 has no variants
    wave_8 = next((w for w in result["waves"] if "8th" in w["name"]), None)
    assert wave_8 is not None
    assert wave_8["variants"] is None

    # Check boxes are returned
    assert "boxes" in result
    assert isinstance(result["boxes"], list)
    assert len(result["boxes"]) > 0

    # Check structure of each box entry
    for box in result["boxes"]:
        assert "name" in box
        assert "wave" in box
        assert isinstance(box["name"], str)
        assert isinstance(box["wave"], str)

    # Check a specific box
    past_and_future = next((b for b in result["boxes"] if b["name"] == "Past and Future"), None)
    assert past_and_future is not None
    assert past_and_future["wave"] == "7th Wave"


def test_setting_wave_override(tmp_path):
    """Test that setting_wave forces a specific wave's setting."""
    paths, _ = build_multi_wave_data(tmp_path)

    result = selector.select_expedition(
        seed=1,
        mage_count=2,
        length="standard",
        content_waves=["1st Wave", "2nd Wave"],
        content_boxes=[],
        mages_yaml_path=str(paths["mages"]),
        settings_yaml_path=str(paths["settings"]),
        waves_yaml_path=str(paths["waves"]),
        nemeses_yaml_path=str(paths["nemeses"]),
        friends_yaml_path=str(paths["friends"]),
        foes_yaml_path=str(paths["foes"]),
        setting_wave="2nd Wave",  # Force 2nd Wave setting
    )

    assert result["setting"]["wave_name"] == "2nd Wave"


def test_setting_variant_requires_setting_wave(tmp_path):
    """Test that setting_variant without setting_wave raises an error."""
    paths = build_base_data(tmp_path)

    with pytest.raises(ValueError, match="setting_variant requires setting_wave"):
        selector.select_expedition(
            seed=1,
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
            setting_variant="future",  # variant without wave
        )


def test_setting_wave_invalid_raises(tmp_path):
    """Test that an invalid setting_wave raises an error."""
    paths = build_base_data(tmp_path)

    with pytest.raises(ValueError, match="setting_wave.*not found"):
        selector.select_expedition(
            seed=1,
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
            setting_wave="99th Wave",  # invalid wave
        )


def test_setting_variant_invalid_for_wave_without_variants(tmp_path):
    """Test that setting_variant for a wave without variants raises an error."""
    paths = build_base_data(tmp_path)  # Base data has no variants

    with pytest.raises(ValueError, match="has no variants"):
        selector.select_expedition(
            seed=1,
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
            setting_wave="1st Wave",
            setting_variant="future",  # 1st Wave has no variants
        )
