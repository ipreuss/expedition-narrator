import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without PyYAML
    yaml = SimpleNamespace(safe_load=lambda stream: json.load(stream))  # type: ignore

import aeons_end_expedition_selector as selector
import expedition_packet_tools as tools


def write_yaml(path: Path, data) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def build_base_data(tmp_path: Path):
    waves = {"boxes": {"Box A": "1st Wave", "Box B": "2nd Wave"}}
    settings = {"wave_settings": {"1st Wave": {"location": "Gravehold"}}}
    mages = {
        "mages": [
            {"name": "Brama", "variants": [{"name": "Brama", "box": "Box A"}]},
            {"name": "Kadir", "variants": [{"name": "Kadir", "box": "Box A"}]},
        ]
    }
    nemeses = {
        "nemeses": [
            {"name": "Carapace Queen", "battle": 1, "box": "Box A"},
            {"name": "Hollow Crown", "battle": 2, "box": "Box A"},
            {"name": "Crooked Mask", "battle": 3, "box": "Box A"},
            {"name": "Knight of Shackles", "battle": 4, "box": "Box A"},
        ]
    }
    friends = {
        "friends": [
            {"name": "Lost Captain", "box": "Box A"},
            {"name": "Archivist", "box": "Box A"},
            {"name": "Wanderer", "box": "Box A"},
            {"name": "Bandit Queen", "box": "Box A"},
        ]
    }
    foes = {
        "foes": [
            {"name": "Broodling Pack", "box": "Box A"},
            {"name": "Grub Horde", "box": "Box A"},
            {"name": "Silt Stalkers", "box": "Box A"},
            {"name": "Wailing Throng", "box": "Box A"},
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


def build_packet(tmp_path: Path):
    paths = build_base_data(tmp_path)
    return selector.select_expedition(
        seed=123,
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


def test_resolve_effective_seed():
    assert tools.resolve_effective_seed({"seed": 5, "attempt_seed": 10}) == 5
    assert tools.resolve_effective_seed({"seed": None, "attempt_seed": 10}) == 10


def test_validate_and_extract_story_inputs(tmp_path: Path):
    packet = build_packet(tmp_path)
    tools.validate_packet(packet, expected_mage_count=2, expected_battles=4)
    story = tools.extract_story_inputs(packet)

    assert story["meta"]["effective_seed"] == packet["meta"]["effective_seed"]
    assert len(story["mages"]) == 2
    assert len(story["battle_plan"]) == 4
