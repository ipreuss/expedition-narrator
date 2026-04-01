# Invincible Profile Scaffold

Status: scaffolded, not implemented.

Planned files:
- `data/`: Invincible datasets
- `api/invincible_expedition_selector_openapi.yaml`: optional game-specific schema
- `api/invincible_expedition_selector_cgi.py`: optional game-specific wrapper
- `gpt/invincible/*.txt`: instruction files for Custom GPT upload once implemented

Planned instruction note:
- once `gpt/invincible/*.txt` exists, it should include the shared self-description policy and an Invincible-specific legal disclaimer for user-facing capability explanations

Current recommendation:
Use the unified multi-game action schema and set `game=invincible` once implementation is complete.
