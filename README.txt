# expedition-narrator
Shared selector engine and game profiles for expedition narrator GPTs.

## Strategy
- Single repository
- Single Custom GPT (multi-game)
- Game-specific profiles under `games/<game>/`
- Shared selection engine under `core/`

## Repository layout
- `core/aeons_end_expedition_selector.py`: selector implementation currently used by Aeon's End.
- `core/game_profiles.py`: profile registry (`aeons_end`, `astro_knights`, `invincible`) with implementation status.
- `system_prompt.txt`: central system prompt for the single multi-game Custom GPT.
- `aeons_end_*.txt`: flat Aeon's End instruction files intended for Custom GPT upload.
- `multi_game_expedition_selector_openapi.yaml`: unified GPT Action schema intended for Custom GPT upload.
- `games/aeons_end/`: implemented profile for server-side assets and game data.
- `games/astro_knights/`: scaffold profile.
- `games/invincible/`: scaffold profile.
- `multi_game_expedition_selector_cgi.py`: unified action endpoint with required `game` parameter.
- `docs/custom_gpt_multigame_setup.md`: concrete setup steps for one multi-game GPT.
- `docs/server_deployment.md`: operational notes for SSH access, server pull workflow, and live endpoint checks.

## Quick start (Aeon's End selector directly)
```bash
python core/aeons_end_expedition_selector.py \
  --mages-yaml games/aeons_end/data/aeons_end_mages.yaml \
  --settings-yaml games/aeons_end/data/wave_settings.yaml \
  --waves-yaml games/aeons_end/data/aeons_end_waves.yaml \
  --nemeses-yaml games/aeons_end/data/aeons_end_nemeses.yaml \
  --friends-yaml games/aeons_end/data/aeons_end_friends.yaml \
  --foes-yaml games/aeons_end/data/aeons_end_foes.yaml \
  --mage-count 4 \
  --length standard \
  --seed 12345
```

## Multi-game action calls
- `operation=availableGames` (discover games + implementation status)
- `operation=availableSettings&game=<game>`
- `selectExpeditionPacket` with required `game`
- `operation=selectReplacementMage` with required `game`

## Suggested release flow
1. Tag stable single-game baseline: `v1-aeons-end-stable`
2. Continue all work on `main`
3. Tag multi-game milestones (example: `v2-multigame-foundation`)

## Testing
Run when dependencies are available:
```bash
pytest tests/
```

## Legal disclaimer
Aeon's End is a trademark and copyright of Indie Boards and Cards. This project is an
unofficial fan project and is not affiliated with, endorsed by, or sponsored by Indie
Boards and Cards or any official Aeon's End creators.
