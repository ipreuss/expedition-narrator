from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

import expedition_packet_tools as tools
import multi_game_expedition_selector_cgi as multi_cgi


@pytest.mark.parametrize(
    "payload, expected_mages, expected_battles",
    [
        (
            {
                "game": "aeons_end",
                "mage_count": 2,
                "seed": 123,
                "length": "standard",
            },
            2,
            4,
        ),
        (
            {
                "game": "astro_knights",
                "mage_count": 2,
                "seed": 123,
                "content_boxes": ["Astro Knights - Eternity"],
                "expedition_difficulty": "advanced",
                "length": "standard",
            },
            2,
            4,
        ),
    ],
)
def test_select_expedition_smoke_for_implemented_games(payload, expected_mages, expected_battles):
    packet = multi_cgi._handle_select_expedition(payload)

    tools.validate_packet(packet, expected_mage_count=expected_mages, expected_battles=expected_battles)
    story = tools.extract_story_inputs(packet)

    assert story["meta"]["effective_seed"] is not None
    assert len(story["mages"]) == expected_mages
    assert len(story["battle_plan"]) == expected_battles


@pytest.mark.parametrize("game", ["aeons_end", "astro_knights"])
def test_available_settings_smoke_for_implemented_games(game):
    settings = multi_cgi._handle_available_settings({"game": game})

    assert isinstance(settings["waves"], list)
    assert isinstance(settings["boxes"], list)
    assert settings["waves"], "Expected at least one wave"
    assert settings["boxes"], "Expected at least one box"


def test_invincible_smoke_reports_not_implemented_errors():
    with pytest.raises(multi_cgi.ApiError, match="not implemented"):
        multi_cgi._handle_available_settings({"game": "invincible"})

    with pytest.raises(multi_cgi.ApiError, match="not implemented"):
        multi_cgi._handle_select_expedition({"game": "invincible", "mage_count": 2})
