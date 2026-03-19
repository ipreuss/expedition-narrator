# Astro Knights Profile

Status: initial implementation.

Current scope:
- Wave 2 only
- `Astro Knights - Eternity`
- `Mystery of Solarus`
- Deterministic selection of one homeworld, one knight team, and a 4-battle boss plan

Implemented files:
- `data/`: Astro Knights Wave-2 datasets
- `api/astro_knights_expedition_selector_openapi.yaml`: game-specific schema
- `api/astro_knights_expedition_selector_cgi.py`: game-specific wrapper

Current recommendation:
Use the unified multi-game action schema and set `game=astro_knights`.
