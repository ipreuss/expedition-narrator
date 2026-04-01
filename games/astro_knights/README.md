# Astro Knights Profile

Status: active implementation.

Current scope:
- `1st Wave`
- `2nd Wave`
- `Astro Knights`
- `The Orion System`
- `Astro Knights - Eternity`
- `Mystery of Solarus`
- `Savage Skies`
- Deterministic selection of one homeworld, one knight team, and a 4-battle boss plan

Implemented files:
- `data/`: Astro Knights datasets
- `api/astro_knights_expedition_selector_openapi.yaml`: game-specific schema
- `api/astro_knights_expedition_selector_cgi.py`: game-specific wrapper

Current recommendation:
Use the unified multi-game action schema and set `game=astro_knights`.
