import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = SimpleNamespace(safe_load=lambda stream: json.load(stream))  # type: ignore
    sys.modules["yaml"] = yaml  # type: ignore

import multi_game_expedition_selector_cgi as multi_cgi


def test_available_games_reports_astro_knights_as_implemented():
    packet = multi_cgi._available_games()
    by_key = {game["key"]: game for game in packet["games"]}

    assert by_key["astro_knights"]["implemented"] is True


def test_multi_game_routes_astro_knights_selection():
    packet = multi_cgi._handle_select_expedition(
        {
            "game": "astro_knights",
            "mage_count": 2,
            "content_boxes": ["Astro Knights - Eternity"],
            "expedition_difficulty": "advanced",
            "seed": 123,
        }
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
    assert packet["final_nemesis"]["box"] == "Astro Knights - Eternity"
    assert packet["final_nemesis"]["battle"] == 4
    assert packet["final_nemesis"]["boss_difficulty"] == "nightmare"
    assert {mage["chosen_variant"]["box"] for mage in packet["mages"]} == {"Astro Knights - Eternity"}


def test_multi_game_routes_astro_knights_available_settings():
    packet = multi_cgi._handle_available_settings({"game": "astro_knights"})

    assert packet["waves"] == [{"name": "1st Wave", "variants": None}, {"name": "2nd Wave", "variants": None}]
    assert {box["name"] for box in packet["boxes"]} == {
        "Astro Knights",
        "The Orion System",
        "Astro Knights - Eternity",
        "Mystery of Solarus",
        "Savage Skies",
    }
