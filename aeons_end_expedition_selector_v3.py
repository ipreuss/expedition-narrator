#!/usr/bin/env python3
"""
Aeon's End Expedition Selector (selection-only) — v3 (collision-free)

What it does
- Selects: setting (wave), mages (with variants), a battle-plan of nemeses by tier, plus rotating friends/foes.
- Uses YAML datasets and Python RNG only.
- Outputs an expedition packet (JSON) containing verbatim YAML payloads for chosen entities.

Guarantee (given your datasets)
- No repeated nemesis across the planned battle sequence.
- No repeated friend or foe across the planned battle sequence.
- No name overlap between mages and any selected friend/foe/nemesis.
If constraints cannot be satisfied, the selector fails with an error (dataset/scope issue).

Out of scope
- No narration.
- No win/lose state, rematches, reinforcements, or reward timing.

Determinism
- With the same inputs + seed, output is stable.
- Internally it may reroll candidate sets until constraints are met, but this process is deterministic per seed.

CLI example
  python aeons_end_expedition_selector_v3.py \\
    --mages-yaml aeons_end_mages_final_clean4.yaml \\
    --settings-yaml wave_settings.yaml \\
    --waves-yaml aeons_end_waves.yaml \\
    --nemeses-yaml aeons_end_nemeses.yaml \\
    --friends-yaml aeons_end_friends.yaml \\
    --foes-yaml aeons_end_foes.yaml \\
    --mage-count 4 \\
    --length standard \\
    --content-waves \"1st Wave\" \\
    --seed 12345
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import random
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import yaml


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()

def _split_csv(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

def _norm_space(s: str) -> str:
    s = s.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s.strip())

def _norm_key(s: str) -> str:
    return _norm_space(s).lower()

def _safe_get(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None

def _choose(rng: random.Random, items: Sequence[Any]) -> Any:
    if not items:
        raise ValueError("No candidates available for selection.")
    return items[rng.randrange(len(items))]

def _shuffle_copy(rng: random.Random, items: Sequence[Any]) -> List[Any]:
    out = list(items)
    rng.shuffle(out)
    return out

def name_key(name: str) -> str:
    return _norm_key(name)


def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_box_to_wave(path: str) -> Dict[str, str]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "boxes" not in data or not isinstance(data["boxes"], dict):
        raise ValueError("waves YAML must be a dict with key 'boxes' mapping box_name -> wave_name")
    return {_norm_space(k): _norm_space(v) for k, v in data["boxes"].items()}

def load_settings_by_wave(path: str) -> Dict[str, Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "wave_settings" not in data or not isinstance(data["wave_settings"], dict):
        raise ValueError("settings YAML must be a dict with key 'wave_settings' mapping wave_name -> setting data")
    out: Dict[str, Dict[str, Any]] = {}
    for wave_name, payload in data["wave_settings"].items():
        if isinstance(payload, dict):
            out[_norm_space(str(wave_name))] = copy.deepcopy(payload)
    return out

def load_mages(path: str) -> List[Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or "mages" not in data or not isinstance(data["mages"], list):
        raise ValueError("mages YAML must be a dict with key 'mages' containing a list")
    return data["mages"]

def load_list_root(path: str, root_key: str) -> List[Dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, dict) or root_key not in data or not isinstance(data[root_key], list):
        raise ValueError(f"{path} must be a dict with key '{root_key}' containing a list")
    return data[root_key]


def resolve_allowed_waves(
    allowed_wave_inputs: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[str]:
    wave_set = {_norm_space(w) for w in allowed_wave_inputs if w.strip()}
    for b in allowed_boxes:
        bn = _norm_space(b)
        if bn in box_to_wave:
            wave_set.add(_norm_space(box_to_wave[bn]))
    return sorted(wave_set)

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

    allowed_boxes_k = {name_key(x) for x in allowed_boxes}
    allowed_waves_k = {name_key(x) for x in allowed_waves}

    if entity_box:
        eb = _norm_space(entity_box)
        if allowed_boxes and name_key(eb) in allowed_boxes_k:
            return True
        w = box_to_wave.get(eb)
        if w and allowed_waves and name_key(w) in allowed_waves_k:
            return True

    if entity_wave and allowed_waves and name_key(_norm_space(entity_wave)) in allowed_waves_k:
        return True

    return False


def eligible_mages_with_variants(
    mages: List[Dict[str, Any]],
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    out: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    for m in mages:
        variants = m.get("variants") or []
        in_scope_variants: List[Dict[str, Any]] = []
        for v in variants:
            v_box = _safe_get(v, "box")
            v_wave = _safe_get(v, "wave_name", "wave_id")
            if in_scope_by_box_or_wave(
                entity_box=str(v_box) if v_box else None,
                entity_wave=str(v_wave) if v_wave else None,
                allowed_waves=allowed_waves,
                allowed_boxes=allowed_boxes,
                box_to_wave=box_to_wave,
            ):
                in_scope_variants.append(v)
        if in_scope_variants:
            out.append((m, in_scope_variants))
    return out

def choose_mages_no_repeat(
    rng: random.Random,
    mages: List[Dict[str, Any]],
    mage_count: int,
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[Dict[str, Any]]:
    eligible = eligible_mages_with_variants(mages, allowed_waves, allowed_boxes, box_to_wave)
    if mage_count > len(eligible):
        raise ValueError(f"Not enough eligible mages: need {mage_count}, have {len(eligible)}")
    pool = _shuffle_copy(rng, eligible)
    chosen = pool[:mage_count]
    result: List[Dict[str, Any]] = []
    used_names: Set[str] = set()
    for m, variants in chosen:
        nm = str(m.get("name") or "")
        nk = name_key(nm)
        if nk in used_names:
            raise ValueError("Mage name collision inside selection pool (unexpected)")
        used_names.add(nk)
        entry = copy.deepcopy(m)
        entry["chosen_variant"] = copy.deepcopy(_choose(rng, variants))
        result.append(entry)
    return result


def tiers_for_length(length: str, rng: random.Random, available_tiers: Sequence[int]) -> List[int]:
    length = _norm_key(length)
    if length == "standard":
        return [1, 2, 3, 4]
    if length == "long":
        return [1, 1, 2, 2, 3, 3, 4, 4]
    if length == "short":
        has1 = 1 in available_tiers
        has2 = 2 in available_tiers
        if has1 and has2:
            first = rng.choice([1, 2])
        elif has1:
            first = 1
        elif has2:
            first = 2
        else:
            raise ValueError("No Tier 1 or Tier 2 nemeses available for short expedition")
        return [first, 3, 4]
    raise ValueError("length must be one of: short, standard, long")


def group_nemeses_by_tier(nemeses: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {1: [], 2: [], 3: [], 4: []}
    for n in nemeses:
        t = _safe_get(n, "battle")
        if t is None:
            continue
        try:
            tier = int(t)
        except Exception:
            continue
        if tier in out:
            out[tier].append(n)
    return out

def filter_by_scope_list(
    lst: List[Dict[str, Any]],
    allowed_waves: Sequence[str],
    allowed_boxes: Sequence[str],
    box_to_wave: Dict[str, str],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for e in lst:
        box = _safe_get(e, "box")
        if in_scope_by_box_or_wave(
            entity_box=str(box) if box else None,
            entity_wave=None,
            allowed_waves=allowed_waves,
            allowed_boxes=allowed_boxes,
            box_to_wave=box_to_wave,
        ):
            out.append(e)
    return out

def detect_outcasts_from_wave_name(wave_name: Optional[str]) -> bool:
    return bool(wave_name) and name_key(wave_name) == name_key("5th Wave")


class SelectionError(RuntimeError):
    pass

def _require_unique_names(items: Sequence[Optional[Dict[str, Any]]], label: str) -> None:
    seen: Set[str] = set()
    for it in items:
        if not it:
            continue
        nm = str(_safe_get(it, "name") or "")
        nk = name_key(nm)
        if nk in seen:
            raise SelectionError(f"Duplicate {label} name selected: {nm}")
        seen.add(nk)

def _require_no_overlap(a: Sequence[Dict[str, Any]], b: Sequence[Optional[Dict[str, Any]]], label_a: str, label_b: str) -> None:
    a_names = {name_key(str(_safe_get(x, "name") or "")) for x in a}
    for it in b:
        if not it:
            continue
        nm = name_key(str(_safe_get(it, "name") or ""))
        if nm in a_names:
            raise SelectionError(f"Name overlap between {label_a} and {label_b}: {_safe_get(it,'name')}")

def _pick_unique_from_pool(
    rng: random.Random,
    pool: List[Dict[str, Any]],
    count: int,
    forbidden: Set[str],
    label: str,
) -> List[Dict[str, Any]]:
    candidates = [x for x in pool if name_key(str(_safe_get(x, "name") or "")) not in forbidden]
    if len(candidates) < count:
        raise SelectionError(f"Not enough unique {label} candidates after forbidding overlaps")
    picked = _shuffle_copy(rng, candidates)[:count]
    _require_unique_names(picked, label)
    return [copy.deepcopy(x) for x in picked]

def _pick_nemeses_for_tiers(
    rng: random.Random,
    by_tier: Dict[int, List[Dict[str, Any]]],
    tiers: List[int],
    forbidden: Set[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not by_tier[4]:
        raise SelectionError("No Tier 4 nemeses available")
    final_pool = [n for n in by_tier[4] if name_key(str(_safe_get(n, "name") or "")) not in forbidden]
    if not final_pool:
        raise SelectionError("No Tier 4 nemeses available after forbidding overlaps")
    final = copy.deepcopy(_choose(rng, final_pool))
    used = {name_key(str(_safe_get(final, "name") or ""))}

    plan: List[Dict[str, Any]] = []
    for idx, tier in enumerate(tiers, start=1):
        if tier == 4 and idx == len(tiers):
            nem = copy.deepcopy(final)
        else:
            pool = by_tier.get(tier, [])
            if not pool:
                raise SelectionError(f"No nemeses available for tier {tier}")
            cand = [
                n for n in pool
                if name_key(str(_safe_get(n, "name") or "")) not in forbidden
                and name_key(str(_safe_get(n, "name") or "")) not in used
            ]
            if not cand:
                raise SelectionError(f"No unique nemesis available for tier {tier} (would repeat or overlap)")
            nem = copy.deepcopy(_choose(rng, cand))
        used.add(name_key(str(_safe_get(nem, "name") or "")))
        plan.append({"battle_index": idx, "tier": tier, "nemesis": nem})
    _require_unique_names([p["nemesis"] for p in plan], "nemesis")
    return plan, final


def select_expedition(
    *,
    seed: Optional[int],
    mage_count: int,
    length: str,
    content_waves: Sequence[str],
    content_boxes: Sequence[str],
    mages_yaml_path: str,
    settings_yaml_path: str,
    waves_yaml_path: str,
    nemeses_yaml_path: str,
    friends_yaml_path: str,
    foes_yaml_path: str,
    max_attempts: int = 200,
) -> Dict[str, Any]:
    base_rng = random.Random(seed)

    box_to_wave = load_box_to_wave(waves_yaml_path)
    allowed_waves = resolve_allowed_waves(content_waves, content_boxes, box_to_wave)
    allowed_boxes = [_norm_space(b) for b in content_boxes]

    settings_by_wave = load_settings_by_wave(settings_yaml_path)
    if not settings_by_wave:
        raise ValueError("No settings found in settings YAML")

    mages_all = load_mages(mages_yaml_path)
    nemeses_all = load_list_root(nemeses_yaml_path, "nemeses")
    friends_all = load_list_root(friends_yaml_path, "friends")
    foes_all = load_list_root(foes_yaml_path, "foes")


    wave_candidates = list(settings_by_wave.keys())
    if allowed_waves:
        allowed_set = {name_key(x) for x in allowed_waves}
        wave_candidates = [w for w in wave_candidates if name_key(w) in allowed_set]
    if not wave_candidates:
        raise ValueError("No settings available in scope")


    nemeses_in_scope = filter_by_scope_list(nemeses_all, allowed_waves, allowed_boxes, box_to_wave)
    by_tier = group_nemeses_by_tier(nemeses_in_scope)
    available_tiers = [t for t, lst in by_tier.items() if lst]
    if not available_tiers:
        raise ValueError("No nemeses available in scope")


    friends_in_scope = filter_by_scope_list(friends_all, allowed_waves, allowed_boxes, box_to_wave)
    foes_in_scope = filter_by_scope_list(foes_all, allowed_waves, allowed_boxes, box_to_wave)


    friends_available = bool(friends_in_scope)
    foes_available = bool(foes_in_scope)
    if friends_available != foes_available:
        raise ValueError("Friend/Foe availability mismatch in scope (unexpected for your datasets)")


    include_friend_foe_pair = friends_available and foes_available

    last_err: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        attempt_seed = base_rng.randrange(0, 2**63)
        rng = random.Random(attempt_seed)
        try:
            chosen_wave = _choose(rng, wave_candidates)
            setting_payload = copy.deepcopy(settings_by_wave[chosen_wave])
            chosen_setting = {"wave_name": chosen_wave, **setting_payload}


            protect_target: Optional[str] = None
            if detect_outcasts_from_wave_name(chosen_wave):
                protect_target = rng.choice(["Gravehold", "Xaxos"])


            chosen_mages = choose_mages_no_repeat(rng, mages_all, mage_count, allowed_waves, allowed_boxes, box_to_wave)
            mage_names = {name_key(str(m.get("name") or "")) for m in chosen_mages}


            tiers = tiers_for_length(length, rng, available_tiers)


            battle_plan, chosen_final = _pick_nemeses_for_tiers(rng, by_tier, tiers, mage_names)
            nemesis_names = {name_key(str(_safe_get(step["nemesis"], "name") or "")) for step in battle_plan}


            if include_friend_foe_pair:
                forbidden_ff = set(mage_names) | set(nemesis_names)
                chosen_friends = _pick_unique_from_pool(rng, friends_in_scope, len(battle_plan), forbidden_ff, "friend")
                forbidden_foe = forbidden_ff | {name_key(str(_safe_get(f, "name") or "")) for f in chosen_friends}
                chosen_foes = _pick_unique_from_pool(rng, foes_in_scope, len(battle_plan), forbidden_foe, "foe")


                for i, step in enumerate(battle_plan):
                    step["friend"] = chosen_friends[i]
                    step["foe"] = chosen_foes[i]


                _require_no_overlap(chosen_mages, chosen_friends, "mages", "friends")
                _require_no_overlap(chosen_mages, chosen_foes, "mages", "foes")
                _require_no_overlap([s["nemesis"] for s in battle_plan], chosen_friends, "nemeses", "friends")
                _require_no_overlap([s["nemesis"] for s in battle_plan], chosen_foes, "nemeses", "foes")
            else:
                for step in battle_plan:
                    step["friend"] = None
                    step["foe"] = None


            packet: Dict[str, Any] = {
                "meta": {
                    "generated_at_utc": _now_iso(),
                    "seed": seed,
                    "attempt": attempt,
                    "attempt_seed": attempt_seed,
                    "inputs": {
                        "mage_count": mage_count,
                        "length": _norm_space(length),
                        "content_waves": list(content_waves),
                        "content_boxes": list(content_boxes),
                    },
                },
                "setting": chosen_setting,
                "protect_target": protect_target,
                "mages": chosen_mages,
                "final_nemesis": chosen_final,
                "battle_plan": battle_plan,
                "availability": {
                    "friends_available": friends_available,
                    "foes_available": foes_available,
                    "include_friend_foe_pair": include_friend_foe_pair,
                },
            }
            return packet

        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Unable to find a collision-free selection after {max_attempts} attempts. Last error: {last_err}")


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Select Aeon's End expedition content (selection only; collision-free).")


    p.add_argument("--mages-yaml", required=True)
    p.add_argument("--settings-yaml", required=True)
    p.add_argument("--waves-yaml", required=True)
    p.add_argument("--nemeses-yaml", required=True)
    p.add_argument("--friends-yaml", required=True)
    p.add_argument("--foes-yaml", required=True)


    p.add_argument("--mage-count", type=int, required=True)
    p.add_argument("--length", choices=["short", "standard", "long"], default="standard")
    p.add_argument("--content-waves", default="", help="Comma-separated wave names (e.g., '1st Wave,2nd Wave').")
    p.add_argument("--content-boxes", default="", help="Comma-separated box names.")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--max-attempts", type=int, default=200)
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    packet = select_expedition(
        seed=args.seed,
        mage_count=args.mage_count,
        length=args.length,
        content_waves=_split_csv(args.content_waves),
        content_boxes=_split_csv(args.content_boxes),
        mages_yaml_path=args.mages_yaml,
        settings_yaml_path=args.settings_yaml,
        waves_yaml_path=args.waves_yaml,
        nemeses_yaml_path=args.nemeses_yaml,
        friends_yaml_path=args.friends_yaml,
        foes_yaml_path=args.foes_yaml,
        max_attempts=args.max_attempts,
    )
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
