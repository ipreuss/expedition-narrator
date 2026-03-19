from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class GameProfile:
    key: str
    display_name: str
    implemented: bool
    instruction_location: str
    data_dir: str
    openapi_schema: str
    selector_cgi: str


GAME_PROFILES: Dict[str, GameProfile] = {
    "aeons_end": GameProfile(
        key="aeons_end",
        display_name="Aeon's End",
        implemented=True,
        instruction_location="gpt/system_prompt.txt plus gpt/aeons_end/*.txt",
        data_dir="games/aeons_end/data",
        openapi_schema="games/aeons_end/api/aeons_end_expedition_selector_openapi.yaml",
        selector_cgi="games/aeons_end/api/aeons_end_expedition_selector_cgi.py",
    ),
    "astro_knights": GameProfile(
        key="astro_knights",
        display_name="Astro Knights",
        implemented=False,
        instruction_location="gpt/system_prompt.txt plus future gpt/astro_knights/*.txt",
        data_dir="games/astro_knights/data",
        openapi_schema="games/astro_knights/api/astro_knights_expedition_selector_openapi.yaml",
        selector_cgi="games/astro_knights/api/astro_knights_expedition_selector_cgi.py",
    ),
    "invincible": GameProfile(
        key="invincible",
        display_name="Invincible",
        implemented=False,
        instruction_location="gpt/system_prompt.txt plus future gpt/invincible/*.txt",
        data_dir="games/invincible/data",
        openapi_schema="games/invincible/api/invincible_expedition_selector_openapi.yaml",
        selector_cgi="games/invincible/api/invincible_expedition_selector_cgi.py",
    ),
}


def get_game_profile(game_key: str) -> GameProfile:
    if game_key not in GAME_PROFILES:
        available = ", ".join(sorted(GAME_PROFILES))
        raise KeyError(f"Unknown game '{game_key}'. Available: {available}")
    return GAME_PROFILES[game_key]
