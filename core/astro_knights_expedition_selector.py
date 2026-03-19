#!/usr/bin/env python3
"""
Astro Knights expedition selector.

Initial implementation scope:
- Wave 2 content only
- Boxes: Astro Knights - Eternity, Mystery of Solarus
- Deterministic selection of one homeworld, one boss encounter, and a knight team

The packet shape intentionally mirrors the shared expedition schema so the
multi-game CGI and packet helpers can keep working without game-specific forks.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import random
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

import yaml


Strictness = Literal["thematic", "mixed", "open"]
VALID_STRICTNESS = ("thematic", "mixed", "open")
ExpeditionDifficulty = Literal["standard", "advanced", "legendary"]
VALID_EXPEDITION_DIFFICULTIES = ("standard", "advanced", "legendary")
DIFFICULTY_LADDER = ("normal", "expert", "nightmare", "apocalypse")
EXPEDITION_DIFFICULTY_OFFSETS = {
    "standard": 0,
    "advanced": 1,
    "legendary": 2,
}


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _norm_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ").strip())


def _norm_key(value: str) -> str:
    return _norm_space(value).lower()


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _choose(rng: random.Random, items: Sequence[Any]) -> Any:
    if not items:
        raise ValueError("No candidates available for selection.")
    return items[rng.randrange(len(items))]


def _shuffle_copy(rng: random.Random, items: Sequence[Any]) -> List[Any]:
    out = list(items)
    rng.shuffle(out)
    return out


def _resolve_effective_seed(seed: Optional[int], attempt_seed: int) -> int:
    return seed if seed is not None else attempt_seed


def name_key(name: str) -> str:
    return _norm_key(name)


def _safe_get(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_box_to_wave(path: str) -> Dict[str, str]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "boxes" not in data or not isinstance(data["boxes"], dict):
        raise ValueError("waves YAML must be a dict with key 'boxes' mapping box_name -> wave_name")
    return {_norm_space(box): _norm_space(wave) for box, wave in data["boxes"].items()}


def load_settings_by_wave(path: str) -> Dict[str, Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "wave_settings" not in data or not isinstance(data["wave_settings"], dict):
        raise ValueError("settings YAML must be a dict with key 'wave_settings' mapping wave_name -> setting data")
    out: Dict[str, Dict[str, Any]] = {}
    for wave_name, payload in data["wave_settings"].items():
        if isinstance(payload, dict):
            out[_norm_space(str(wave_name))] = copy.deepcopy(payload)
    return out


def load_knights(path: str) -> List[Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "knights" not in data or not isinstance(data["knights"], list):
        raise ValueError("knights YAML must be a dict with key 'knights' containing a list")
    return data["knights"]


def load_list_root(path: str, root_key: str) -> List[Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or root_key not in data or not isinstance(data[root_key], list):
        raise ValueError(f"{path} must be a dict with key '{root_key}' containing a list")
    return data[root_key]


def _normalize_scope_list(values: Sequence[str]) -> List[str]:
    cleaned = [_norm_space(str(value)) for value in values if str(value).strip()]
    if any(name_key(value) == "all" for value in cleaned):
        return []
    return cleaned


def resolve_allowed_waves(
    allowed_wave_inputs: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[str]:
    wave_set = {_norm_space(wave) for wave in allowed_wave_inputs if wave.strip()}
    for box in allowed_boxes:
        normalized_box = _norm_space(box)
        if normalized_box in box_to_wave:
            wave_set.add(_norm_space(box_to_wave[normalized_box]))
    return sorted(wave_set)


def infer_boxes_from_waves(
    allowed_wave_inputs: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[str]:
    wave_keys = {name_key(_norm_space(wave)) for wave in allowed_wave_inputs if wave.strip()}
    if not wave_keys:
        return []
    return sorted([box for box, wave in box_to_wave.items() if name_key(wave) in wave_keys])


def in_scope_by_box_or_wave(
    *,
    entity_box: Optional[str],
    entity_wave: Optional[str],
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> bool:
    if not allowed_waves and not allowed_boxes:
        return True

    allowed_boxes_k = {name_key(value) for value in allowed_boxes}
    allowed_waves_k = {name_key(value) for value in allowed_waves}

    if entity_box:
        box = _norm_space(entity_box)
        if allowed_boxes and name_key(box) in allowed_boxes_k:
            return True
        wave = box_to_wave.get(box)
        if wave and allowed_waves and name_key(wave) in allowed_waves_k:
            return True

    if entity_wave and allowed_waves and name_key(_norm_space(entity_wave)) in allowed_waves_k:
        return True

    return False


def get_boxes_for_wave(wave_name: str, box_to_wave: Dict[str, str]) -> List[str]:
    wave_k = name_key(wave_name)
    return sorted([box for box, wave in box_to_wave.items() if name_key(wave) == wave_k])


def eligible_knights_with_variants(
    knights: List[Dict[str, Any]],
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    out: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    for knight in knights:
        variants = knight.get("variants") or []
        in_scope_variants: List[Dict[str, Any]] = []
        for variant in variants:
            variant_box = _safe_get(variant, "box")
            variant_wave = _safe_get(variant, "wave_name", "wave_id")
            if in_scope_by_box_or_wave(
                entity_box=str(variant_box) if variant_box else None,
                entity_wave=str(variant_wave) if variant_wave else None,
                allowed_waves=allowed_waves,
                allowed_boxes=allowed_boxes,
                box_to_wave=box_to_wave,
            ):
                in_scope_variants.append(variant)
        if in_scope_variants:
            out.append((knight, in_scope_variants))
    return out


def choose_knights_no_repeat(
    rng: random.Random,
    knights: List[Dict[str, Any]],
    knight_count: int,
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
    forbidden_names: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    eligible = eligible_knights_with_variants(knights, allowed_waves, allowed_boxes, box_to_wave)
    forbidden = {name_key(name) for name in (forbidden_names or [])}
    available = [
        (knight, variants) for knight, variants in eligible if name_key(str(knight.get("name") or "")) not in forbidden
    ]
    if knight_count > len(available):
        raise ValueError(f"Not enough eligible Astro Knights: need {knight_count}, have {len(available)}")

    chosen = _shuffle_copy(rng, available)[:knight_count]
    result: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for knight, variants in chosen:
        knight_name = str(knight.get("name") or "")
        knight_key = name_key(knight_name)
        if knight_key in seen:
            raise ValueError(f"Duplicate Astro Knight selected: {knight_name}")
        seen.add(knight_key)
        entry = copy.deepcopy(knight)
        entry["chosen_variant"] = copy.deepcopy(_choose(rng, variants))
        result.append(entry)
    return result


def filter_by_scope(
    entities: List[Dict[str, Any]],
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for entity in entities:
        if entity.get("implemented") is False:
            continue
        entity_box = _safe_get(entity, "box")
        entity_wave = _safe_get(entity, "wave_name", "wave_id")
        if in_scope_by_box_or_wave(
            entity_box=str(entity_box) if entity_box else None,
            entity_wave=str(entity_wave) if entity_wave else None,
            allowed_waves=allowed_waves,
            allowed_boxes=allowed_boxes,
            box_to_wave=box_to_wave,
        ):
            out.append(copy.deepcopy(entity))
    return out


def get_available_settings(
    settings_yaml_path: Optional[str] = None,
    waves_yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    repo_root = os.path.dirname(os.path.dirname(__file__))
    if settings_yaml_path is None:
        settings_yaml_path = os.path.join(repo_root, "games", "astro_knights", "data", "wave_settings.yaml")
    if waves_yaml_path is None:
        waves_yaml_path = os.path.join(repo_root, "games", "astro_knights", "data", "astro_knights_waves.yaml")

    settings_by_wave = load_settings_by_wave(settings_yaml_path)
    waves = [{"name": wave_name, "variants": None} for wave_name in sorted(settings_by_wave)]

    waves_data = load_yaml(waves_yaml_path)
    box_mapping = waves_data.get("boxes", {})
    boxes = [{"name": box_name, "wave": wave_name} for box_name, wave_name in box_mapping.items()]
    boxes.sort(key=lambda box: (box["wave"], box["name"]))
    return {"waves": waves, "boxes": boxes}


def boss_supports_battle(boss: Dict[str, Any], battle_index: int) -> bool:
    battle_difficulties = boss.get("battle_difficulties")
    if not isinstance(battle_difficulties, dict):
        return False
    return str(battle_index) in {str(key) for key in battle_difficulties.keys()}


def choose_unique_boss_plan(
    rng: random.Random,
    bosses: List[Dict[str, Any]],
    battle_indices: Sequence[int],
    forbidden_names: Sequence[str],
) -> List[Dict[str, Any]]:
    forbidden = {name_key(name) for name in forbidden_names}

    def backtrack(position: int, used_names: set[str]) -> Optional[List[Dict[str, Any]]]:
        if position >= len(battle_indices):
            return []

        battle_index = battle_indices[position]
        candidates = [
            boss
            for boss in bosses
            if boss_supports_battle(boss, battle_index)
            and name_key(str(boss.get("name") or "")) not in forbidden
            and name_key(str(boss.get("name") or "")) not in used_names
        ]
        candidates = _shuffle_copy(rng, candidates)

        for boss in candidates:
            boss_name = name_key(str(boss.get("name") or ""))
            remainder = backtrack(position + 1, used_names | {boss_name})
            if remainder is not None:
                return [copy.deepcopy(boss), *remainder]
        return None

    plan = backtrack(0, set())
    if plan is None:
        battle_list = ", ".join(str(index) for index in battle_indices)
        raise ValueError(f"Unable to build a unique Astro Knights boss plan for battles {battle_list}")
    return plan


def resolve_boss_difficulty(
    boss: Dict[str, Any],
    expedition_difficulty: ExpeditionDifficulty,
    battle_index: Optional[int] = None,
) -> str:
    if battle_index is None:
        raw_battle = boss.get("battle")
        try:
            battle_index = int(raw_battle)
        except (TypeError, ValueError):
            battle_index = None

    battle_difficulties = boss.get("battle_difficulties")
    standard_difficulty = ""
    if isinstance(battle_difficulties, dict) and battle_index is not None:
        standard_difficulty = str(
            battle_difficulties.get(str(battle_index)) or battle_difficulties.get(battle_index) or ""
        ).strip().lower()

    if standard_difficulty not in DIFFICULTY_LADDER:
        boss_name = boss.get("name", "<unknown boss>")
        raise ValueError(
            f"Boss '{boss_name}' has unsupported standard difficulty '{standard_difficulty}'"
            f"{f' for battle {battle_index}' if battle_index is not None else ''}. "
            f"Expected one of: {', '.join(DIFFICULTY_LADDER)}"
        )

    base_index = DIFFICULTY_LADDER.index(standard_difficulty)
    offset = EXPEDITION_DIFFICULTY_OFFSETS[expedition_difficulty]
    resolved_index = min(base_index + offset, len(DIFFICULTY_LADDER) - 1)
    return DIFFICULTY_LADDER[resolved_index]


def select_expedition(
    *,
    seed: Optional[int],
    mage_count: int,
    length: str,
    content_waves: Sequence[str],
    content_boxes: Sequence[str],
    knights_yaml_path: str,
    settings_yaml_path: str,
    waves_yaml_path: str,
    bosses_yaml_path: str,
    homeworlds_yaml_path: str,
    max_attempts: int = 200,
    mage_recruitment_chance: int = 0,
    strictness: Strictness = "open",
    expedition_difficulty: ExpeditionDifficulty = "standard",
    setting_wave: Optional[str] = None,
    setting_variant: Optional[str] = None,
) -> Dict[str, Any]:
    if strictness not in VALID_STRICTNESS:
        raise ValueError(f"strictness must be one of: {', '.join(VALID_STRICTNESS)}")
    if expedition_difficulty not in VALID_EXPEDITION_DIFFICULTIES:
        raise ValueError(
            f"expedition_difficulty must be one of: {', '.join(VALID_EXPEDITION_DIFFICULTIES)}"
        )
    if _norm_key(length) != "standard":
        raise ValueError("astro_knights currently supports only standard 4-battle expeditions")
    if setting_variant is not None:
        raise ValueError("setting_variant is not supported for astro_knights")
    if mage_count < 1 or mage_count > 4:
        raise ValueError("mage_count must be between 1 and 4 for astro_knights")

    base_rng = random.Random(seed)

    box_to_wave = load_box_to_wave(waves_yaml_path)
    normalized_waves = _normalize_scope_list(content_waves)
    normalized_boxes = _normalize_scope_list(content_boxes)
    explicit_waves = normalized_waves
    allowed_boxes = sorted(set(_norm_space(box) for box in normalized_boxes))
    allowed_boxes.extend(infer_boxes_from_waves(explicit_waves, box_to_wave))
    allowed_boxes = sorted(set(allowed_boxes))
    allowed_waves_for_settings = resolve_allowed_waves(explicit_waves, normalized_boxes, box_to_wave)

    settings_by_wave = load_settings_by_wave(settings_yaml_path)
    if not settings_by_wave:
        raise ValueError("No settings found in settings YAML")

    wave_candidates = list(settings_by_wave.keys())
    if allowed_waves_for_settings:
        allowed_wave_keys = {name_key(wave) for wave in allowed_waves_for_settings}
        wave_candidates = [wave for wave in wave_candidates if name_key(wave) in allowed_wave_keys]
    if not wave_candidates:
        raise ValueError("No settings available in scope")

    forced_wave: Optional[str] = None
    if setting_wave is not None:
        normalized_setting_wave = _norm_space(setting_wave)
        matches = [wave for wave in settings_by_wave if name_key(wave) == name_key(normalized_setting_wave)]
        if not matches:
            available_waves = ", ".join(sorted(settings_by_wave))
            raise ValueError(f"setting_wave '{setting_wave}' not found. Available waves: {available_waves}")
        forced_wave = matches[0]

    knights_all = load_knights(knights_yaml_path)
    bosses_all = load_list_root(bosses_yaml_path, "bosses")
    homeworlds_all = load_list_root(homeworlds_yaml_path, "homeworlds")

    last_err: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        attempt_seed = base_rng.randrange(0, 2**63)
        rng = random.Random(attempt_seed)
        try:
            chosen_wave = forced_wave if forced_wave is not None else _choose(rng, wave_candidates)
            setting_payload = copy.deepcopy(settings_by_wave[chosen_wave])
            wave_boxes = get_boxes_for_wave(chosen_wave, box_to_wave)

            if strictness == "thematic":
                knight_waves = [chosen_wave]
                knight_boxes = wave_boxes
                bosses_in_scope = filter_by_scope(bosses_all, [chosen_wave], wave_boxes, box_to_wave)
                homeworlds_in_scope = filter_by_scope(homeworlds_all, [chosen_wave], wave_boxes, box_to_wave)
            else:
                knight_waves = explicit_waves
                knight_boxes = allowed_boxes
                bosses_in_scope = filter_by_scope(bosses_all, explicit_waves, allowed_boxes, box_to_wave)
                homeworlds_in_scope = filter_by_scope(homeworlds_all, explicit_waves, allowed_boxes, box_to_wave)

            if strictness == "mixed":
                knight_waves = [chosen_wave]
                knight_boxes = wave_boxes

            if not bosses_in_scope:
                raise ValueError("No bosses available in scope")
            if not homeworlds_in_scope:
                raise ValueError("No homeworlds available in scope")

            chosen_homeworld = _choose(rng, homeworlds_in_scope)
            chosen_knights = choose_knights_no_repeat(
                rng,
                knights_all,
                mage_count,
                knight_waves,
                knight_boxes,
                box_to_wave,
            )
            knight_names = {name_key(str(knight.get("name") or "")) for knight in chosen_knights}
            battle_indices = [1, 2, 3, 4]
            boss_sequence = choose_unique_boss_plan(
                rng,
                bosses_in_scope,
                battle_indices,
                forbidden_names=list(knight_names),
            )

            battle_plan: List[Dict[str, Any]] = []
            for battle_index, boss in zip(battle_indices, boss_sequence):
                boss["battle"] = battle_index
                boss["boss_difficulty"] = resolve_boss_difficulty(
                    boss, expedition_difficulty, battle_index=battle_index
                )
                battle_plan.append(
                    {
                        "battle_index": battle_index,
                        "tier": battle_index,
                        "nemesis": boss,
                        "friend": None,
                        "foe": None,
                        "recruit": None,
                        "boss_difficulty": boss["boss_difficulty"],
                    }
                )

            chosen_final = copy.deepcopy(battle_plan[-1]["nemesis"])

            chosen_setting = {
                "wave_name": chosen_wave,
                **setting_payload,
                "homeworld_name": chosen_homeworld.get("name"),
                "homeworld_box": chosen_homeworld.get("box"),
                "homeworld_background": chosen_homeworld.get("background"),
                "expedition_difficulty": expedition_difficulty,
            }

            packet: Dict[str, Any] = {
                "meta": {
                    "generated_at_utc": _now_iso(),
                    "seed": seed,
                    "attempt": attempt,
                    "attempt_seed": attempt_seed,
                    "effective_seed": _resolve_effective_seed(seed, attempt_seed),
                    "inputs": {
                        "mage_count": mage_count,
                        "length": _norm_space(length),
                        "content_waves": list(normalized_waves),
                        "content_boxes": list(normalized_boxes),
                        "mage_recruitment_chance": mage_recruitment_chance,
                        "strictness": strictness,
                        "expedition_difficulty": expedition_difficulty,
                    },
                },
                "setting": chosen_setting,
                "homeworld": chosen_homeworld,
                "protect_target": chosen_homeworld.get("name"),
                "mages": chosen_knights,
                "final_nemesis": chosen_final,
                "battle_plan": battle_plan,
                "availability": {
                    "friends_available": False,
                    "foes_available": False,
                    "include_friend_foe_pair": False,
                },
            }
            return packet
        except Exception as exc:
            last_err = exc
            continue

    raise RuntimeError(
        f"Unable to find an Astro Knights selection after {max_attempts} attempts. Last error: {last_err}"
    )


def select_replacement_mage(
    *,
    seed: Optional[int],
    existing_mage_names: Sequence[str],
    content_waves: Sequence[str],
    content_boxes: Sequence[str],
    knights_yaml_path: str,
    waves_yaml_path: str,
    max_attempts: int = 200,
) -> Dict[str, Any]:
    base_rng = random.Random(seed)

    box_to_wave = load_box_to_wave(waves_yaml_path)
    normalized_waves = _normalize_scope_list(content_waves)
    normalized_boxes = _normalize_scope_list(content_boxes)
    explicit_waves = normalized_waves
    allowed_boxes = sorted(set(_norm_space(box) for box in normalized_boxes))
    allowed_boxes.extend(infer_boxes_from_waves(explicit_waves, box_to_wave))
    allowed_boxes = sorted(set(allowed_boxes))

    knights_all = load_knights(knights_yaml_path)

    last_err: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        attempt_seed = base_rng.randrange(0, 2**63)
        rng = random.Random(attempt_seed)
        try:
            replacement = choose_knights_no_repeat(
                rng,
                knights_all,
                1,
                explicit_waves,
                allowed_boxes,
                box_to_wave,
                forbidden_names=existing_mage_names,
            )[0]
            return {
                "meta": {
                    "generated_at_utc": _now_iso(),
                    "seed": seed,
                    "attempt": attempt,
                    "attempt_seed": attempt_seed,
                    "effective_seed": _resolve_effective_seed(seed, attempt_seed),
                    "inputs": {
                        "existing_mage_names": list(existing_mage_names),
                        "content_waves": list(normalized_waves),
                        "content_boxes": list(normalized_boxes),
                    },
                },
                "mage": replacement,
            }
        except Exception as exc:
            last_err = exc
            continue

    raise RuntimeError(
        f"Unable to find an Astro Knights replacement after {max_attempts} attempts. Last error: {last_err}"
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select Astro Knights expedition content.")
    parser.add_argument("--knights-yaml", required=True)
    parser.add_argument("--settings-yaml", required=True)
    parser.add_argument("--waves-yaml", required=True)
    parser.add_argument("--bosses-yaml", required=True)
    parser.add_argument("--homeworlds-yaml", required=True)
    parser.add_argument("--mage-count", type=int, required=True)
    parser.add_argument("--length", choices=["short", "standard", "long"], default="standard")
    parser.add_argument("--content-waves", default="")
    parser.add_argument("--content-boxes", default="")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-attempts", type=int, default=200)
    parser.add_argument("--strictness", choices=["thematic", "mixed", "open"], default="open")
    parser.add_argument(
        "--expedition-difficulty",
        choices=["standard", "advanced", "legendary"],
        default="standard",
    )
    parser.add_argument("--setting-wave", default=None)
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    packet = select_expedition(
        seed=args.seed,
        mage_count=args.mage_count,
        length=args.length,
        content_waves=_split_csv(args.content_waves),
        content_boxes=_split_csv(args.content_boxes),
        knights_yaml_path=args.knights_yaml,
        settings_yaml_path=args.settings_yaml,
        waves_yaml_path=args.waves_yaml,
        bosses_yaml_path=args.bosses_yaml,
        homeworlds_yaml_path=args.homeworlds_yaml,
        max_attempts=args.max_attempts,
        strictness=args.strictness,
        expedition_difficulty=args.expedition_difficulty,
        setting_wave=args.setting_wave,
    )
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
