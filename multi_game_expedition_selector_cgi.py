#!/usr/bin/env python3
"""Unified CGI wrapper for multi-game expedition selection.

Supported today:
- game=aeons_end

Scaffolded (not implemented yet):
- game=astro_knights
- game=invincible
"""

from __future__ import annotations

import cgi
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.game_profiles import GAME_PROFILES, get_game_profile  # noqa: E402

AEONS_END_PATHS = {
    "mages_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "aeons_end_mages.yaml"),
    "settings_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "wave_settings.yaml"),
    "waves_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "aeons_end_waves.yaml"),
    "nemeses_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "aeons_end_nemeses.yaml"),
    "friends_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "aeons_end_friends.yaml"),
    "foes_yaml_path": os.path.join(REPO_ROOT, "games", "aeons_end", "data", "aeons_end_foes.yaml"),
}


class ApiError(Exception):
    def __init__(self, message: str, status: str = "400 Bad Request") -> None:
        super().__init__(message)
        self.status = status


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return _split_csv(value)
    raise ApiError("Expected list or comma-separated string.")


def _parse_int(value: Any, field: str, required: bool = False) -> Optional[int]:
    if value is None or value == "":
        if required:
            raise ApiError(f"Missing required field: {field}")
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"Invalid integer for {field}") from exc


def _send_json(payload: Dict[str, Any], status: str = "200 OK") -> None:
    print(f"Status: {status}")
    print("Content-Type: application/json; charset=utf-8")
    print()
    print(json.dumps(payload, ensure_ascii=False))


def _read_json_body() -> Dict[str, Any]:
    try:
        length = int(os.environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    body = sys.stdin.read(length) if length > 0 else ""
    if not body.strip():
        return {}
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ApiError("JSON body must be an object.")
    return data


def _read_form_body() -> Dict[str, Any]:
    form = cgi.FieldStorage()
    data: Dict[str, Any] = {}
    for key in form.keys():
        data[key] = form.getfirst(key)
    return data


def _read_query_params() -> Dict[str, Any]:
    query = os.environ.get("QUERY_STRING", "")
    parsed = parse_qs(query, keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items()}


def _read_request() -> Dict[str, Any]:
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    content_type = os.environ.get("CONTENT_TYPE", "")
    data: Dict[str, Any] = {}

    if method in {"POST", "PUT"}:
        if "application/json" in content_type:
            data.update(_read_json_body())
        else:
            data.update(_read_form_body())

    data.update(_read_query_params())
    return data


def _require_game(data: Dict[str, Any]) -> str:
    game = str(data.get("game") or "").strip()
    if not game:
        raise ApiError("Missing required field: game")
    try:
        profile = get_game_profile(game)
    except KeyError as exc:
        raise ApiError(str(exc)) from exc

    if not profile.implemented:
        raise ApiError(
            f"Game '{game}' is scaffolded but not implemented yet.",
            status="501 Not Implemented",
        )
    return profile.key


def _available_games() -> Dict[str, Any]:
    games = [
        {
            "key": profile.key,
            "display_name": profile.display_name,
            "implemented": profile.implemented,
        }
        for profile in GAME_PROFILES.values()
    ]
    return {"games": sorted(games, key=lambda game: game["key"])}


def _handle_available_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    game = _require_game(data)
    if game != "aeons_end":
        raise ApiError(f"availableSettings is not implemented for '{game}'", status="501 Not Implemented")
    from core.aeons_end_expedition_selector import get_available_settings

    return get_available_settings(
        settings_yaml_path=AEONS_END_PATHS["settings_yaml_path"],
        waves_yaml_path=AEONS_END_PATHS["waves_yaml_path"],
    )


def _handle_select_expedition(data: Dict[str, Any]) -> Dict[str, Any]:
    game = _require_game(data)
    if game != "aeons_end":
        raise ApiError(f"selectExpeditionPacket is not implemented for '{game}'", status="501 Not Implemented")
    from core.aeons_end_expedition_selector import select_expedition

    mage_count = _parse_int(data.get("mage_count"), "mage_count", required=True)
    length = str(data.get("length") or "standard").strip().lower()
    if length not in {"short", "standard", "long"}:
        raise ApiError("length must be one of: short, standard, long")

    content_waves = _parse_list(data.get("content_waves"))
    content_boxes = _parse_list(data.get("content_boxes"))
    seed = _parse_int(data.get("seed"), "seed")
    max_attempts = _parse_int(data.get("max_attempts"), "max_attempts") or 200
    mage_recruitment_chance = _parse_int(data.get("mage_recruitment_chance"), "mage_recruitment_chance") or 100
    strictness = str(data.get("strictness") or "open").strip().lower()
    setting_wave = data.get("setting_wave")
    setting_variant = data.get("setting_variant")

    return select_expedition(
        seed=seed,
        mage_count=mage_count,
        length=length,
        content_waves=content_waves,
        content_boxes=content_boxes,
        max_attempts=max_attempts,
        mage_recruitment_chance=mage_recruitment_chance,
        strictness=strictness,
        setting_wave=setting_wave,
        setting_variant=setting_variant,
        **AEONS_END_PATHS,
    )


def _handle_select_replacement_mage(data: Dict[str, Any]) -> Dict[str, Any]:
    game = _require_game(data)
    if game != "aeons_end":
        raise ApiError(f"selectReplacementMage is not implemented for '{game}'", status="501 Not Implemented")
    from core.aeons_end_expedition_selector import select_replacement_mage

    existing_mage_names = _parse_list(data.get("existing_mage_names"))
    if not existing_mage_names:
        raise ApiError("Missing required field: existing_mage_names")
    content_waves = _parse_list(data.get("content_waves"))
    content_boxes = _parse_list(data.get("content_boxes"))
    seed = _parse_int(data.get("seed"), "seed")
    max_attempts = _parse_int(data.get("max_attempts"), "max_attempts") or 200

    return select_replacement_mage(
        seed=seed,
        existing_mage_names=existing_mage_names,
        content_waves=content_waves,
        content_boxes=content_boxes,
        max_attempts=max_attempts,
        mages_yaml_path=AEONS_END_PATHS["mages_yaml_path"],
        waves_yaml_path=AEONS_END_PATHS["waves_yaml_path"],
    )


def main() -> None:
    try:
        data = _read_request()
        operation = data.get("operation", "selectExpeditionPacket")

        if operation == "availableGames":
            packet = _available_games()
        elif operation == "availableSettings":
            packet = _handle_available_settings(data)
        elif operation == "selectReplacementMage":
            packet = _handle_select_replacement_mage(data)
        else:
            packet = _handle_select_expedition(data)

        _send_json(packet)
    except ApiError as exc:
        _send_json({"error": str(exc)}, status=exc.status)
    except Exception as exc:  # noqa: BLE001
        _send_json({"error": "Internal server error", "detail": str(exc)}, status="500 Internal Server Error")


if __name__ == "__main__":
    main()
