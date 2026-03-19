#!/usr/bin/env python3
"""CGI wrapper for the Astro Knights expedition selector."""

from __future__ import annotations

import cgi
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.astro_knights_expedition_selector import (  # noqa: E402
    get_available_settings,
    select_expedition,
    select_replacement_mage,
)

DEFAULT_PATHS = {
    "knights_yaml_path": os.path.join(REPO_ROOT, "games", "astro_knights", "data", "astro_knights_knights.yaml"),
    "settings_yaml_path": os.path.join(REPO_ROOT, "games", "astro_knights", "data", "wave_settings.yaml"),
    "waves_yaml_path": os.path.join(REPO_ROOT, "games", "astro_knights", "data", "astro_knights_waves.yaml"),
    "bosses_yaml_path": os.path.join(REPO_ROOT, "games", "astro_knights", "data", "astro_knights_bosses.yaml"),
    "homeworlds_yaml_path": os.path.join(
        REPO_ROOT, "games", "astro_knights", "data", "astro_knights_homeworlds.yaml"
    ),
}


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
    raise ValueError("Expected list or comma-separated string.")


def _parse_int(value: Any, field: str, required: bool = False) -> Optional[int]:
    if value is None or value == "":
        if required:
            raise ValueError(f"Missing required field: {field}")
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {field}") from exc


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
        raise ValueError("JSON body must be an object.")
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


def _handle_select_expedition(data: Dict[str, Any]) -> Dict[str, Any]:
    mage_count = _parse_int(data.get("mage_count"), "mage_count", required=True)
    length = str(data.get("length") or "standard").strip().lower()
    content_waves = _parse_list(data.get("content_waves"))
    content_boxes = _parse_list(data.get("content_boxes"))
    seed = _parse_int(data.get("seed"), "seed")
    max_attempts = _parse_int(data.get("max_attempts"), "max_attempts") or 200
    strictness = str(data.get("strictness") or "open").strip().lower()
    expedition_difficulty = str(data.get("expedition_difficulty") or "standard").strip().lower()
    setting_wave = data.get("setting_wave")

    return select_expedition(
        seed=seed,
        mage_count=mage_count,
        length=length,
        content_waves=content_waves,
        content_boxes=content_boxes,
        max_attempts=max_attempts,
        strictness=strictness,
        expedition_difficulty=expedition_difficulty,
        setting_wave=setting_wave,
        **DEFAULT_PATHS,
    )


def _handle_select_replacement_mage(data: Dict[str, Any]) -> Dict[str, Any]:
    existing_mage_names = _parse_list(data.get("existing_mage_names"))
    if not existing_mage_names:
        raise ValueError("Missing required field: existing_mage_names")
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
        knights_yaml_path=DEFAULT_PATHS["knights_yaml_path"],
        waves_yaml_path=DEFAULT_PATHS["waves_yaml_path"],
    )


def _handle_available_settings() -> Dict[str, Any]:
    return get_available_settings(
        settings_yaml_path=DEFAULT_PATHS["settings_yaml_path"],
        waves_yaml_path=DEFAULT_PATHS["waves_yaml_path"],
    )


def main() -> None:
    try:
        data = _read_request()
        operation = data.get("operation", "selectExpeditionPacket")

        if operation == "availableSettings":
            packet = _handle_available_settings()
        elif operation == "selectReplacementMage":
            packet = _handle_select_replacement_mage(data)
        else:
            packet = _handle_select_expedition(data)

        _send_json(packet)
    except ValueError as exc:
        _send_json({"error": str(exc)}, status="400 Bad Request")
    except Exception as exc:  # noqa: BLE001
        _send_json({"error": "Internal server error", "detail": str(exc)}, status="500 Internal Server Error")


if __name__ == "__main__":
    main()
