#!/usr/bin/env python3
"""
Utilities for inspecting expedition packets.

Provides:
- deterministic seed resolution (seed fallback to attempt_seed)
- single-pass extraction for story-relevant inputs
- packet validation helpers
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import re


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ").strip())


def _name_key(name: str) -> str:
    return _norm_space(name).lower()


def resolve_effective_seed(meta: Dict[str, Any]) -> Optional[int]:
    """Return meta.seed if present, otherwise meta.attempt_seed."""
    seed = meta.get("seed")
    if seed is not None:
        return seed
    return meta.get("attempt_seed")


def validate_packet(
    packet: Dict[str, Any],
    *,
    expected_mage_count: Optional[int] = None,
    expected_battles: Optional[int] = None,
) -> None:
    required = [
        "meta",
        "setting",
        "protect_target",
        "mages",
        "final_nemesis",
        "battle_plan",
        "availability",
    ]
    for key in required:
        if key not in packet:
            raise ValueError(f"Missing required key: {key}")

    mages = packet["mages"]
    battle_plan = packet["battle_plan"]

    if not isinstance(mages, list):
        raise ValueError("Packet 'mages' must be a list")
    if not isinstance(battle_plan, list):
        raise ValueError("Packet 'battle_plan' must be a list")

    if expected_mage_count is not None and len(mages) != expected_mage_count:
        raise ValueError(f"Expected {expected_mage_count} mages, found {len(mages)}")
    if expected_battles is not None and len(battle_plan) != expected_battles:
        raise ValueError(f"Expected {expected_battles} battles, found {len(battle_plan)}")

    def collect_names(items: List[Dict[str, Any]]) -> Set[str]:
        return {_name_key(str(item.get("name") or "")) for item in items}

    mage_names = collect_names(mages)
    nemesis_names = collect_names([step["nemesis"] for step in battle_plan])
    friend_names = collect_names([step["friend"] for step in battle_plan if step.get("friend")])
    foe_names = collect_names([step["foe"] for step in battle_plan if step.get("foe")])

    if not mage_names.isdisjoint(nemesis_names):
        raise ValueError("Mage/nemesis name overlap detected")
    if not mage_names.isdisjoint(friend_names):
        raise ValueError("Mage/friend name overlap detected")
    if not mage_names.isdisjoint(foe_names):
        raise ValueError("Mage/foe name overlap detected")
    if not nemesis_names.isdisjoint(friend_names):
        raise ValueError("Nemesis/friend name overlap detected")
    if not nemesis_names.isdisjoint(foe_names):
        raise ValueError("Nemesis/foe name overlap detected")
    if not friend_names.isdisjoint(foe_names):
        raise ValueError("Friend/foe name overlap detected")


def extract_story_inputs(packet: Dict[str, Any]) -> Dict[str, Any]:
    setting = packet.get("setting", {})
    story_setting = {
        "wave_name": setting.get("wave_name"),
        "setting": setting.get("setting"),
        "mood": setting.get("mood"),
        "themes": setting.get("themes"),
        "possible_expeditions": setting.get("possible_expeditions"),
    }

    def mage_brief(mage: Dict[str, Any]) -> Dict[str, Any]:
        variant = mage.get("chosen_variant") or {}
        return {
            "name": mage.get("name"),
            "box": variant.get("box"),
            "background": variant.get("background", mage.get("background")),
            "appearance": variant.get("appearance", mage.get("appearance")),
            "story_notes": variant.get("story_notes", mage.get("story_notes")),
            "strengths": variant.get("strengths", mage.get("strengths")),
            "weaknesses": variant.get("weaknesses", mage.get("weaknesses")),
        }

    mages = [mage_brief(mage) for mage in packet.get("mages", [])]

    def plan_entry(step: Dict[str, Any]) -> Dict[str, Any]:
        def compact(entity: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            if not entity:
                return None
            return {
                "name": entity.get("name"),
                "box": entity.get("box"),
                "battle": entity.get("battle"),
                "background": entity.get("background"),
                "story_notes": entity.get("story_notes"),
            }

        return {
            "battle_index": step.get("battle_index"),
            "tier": step.get("tier"),
            "nemesis": compact(step.get("nemesis")),
            "friend": compact(step.get("friend")),
            "foe": compact(step.get("foe")),
        }

    battle_plan = [plan_entry(step) for step in packet.get("battle_plan", [])]

    return {
        "meta": {
            "generated_at_utc": packet.get("meta", {}).get("generated_at_utc"),
            "seed": packet.get("meta", {}).get("seed"),
            "attempt_seed": packet.get("meta", {}).get("attempt_seed"),
            "effective_seed": resolve_effective_seed(packet.get("meta", {})),
        },
        "setting": story_setting,
        "mages": mages,
        "battle_plan": battle_plan,
        "final_nemesis": packet.get("final_nemesis"),
        "protect_target": packet.get("protect_target"),
    }
