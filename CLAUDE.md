# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the **Expedition Narrator** codebase, now organized as one multi-game Custom GPT plus game-specific server-side assets. The system has three components:

1. **Deterministic Selector** (`core/aeons_end_expedition_selector.py`) - Generates collision-free expedition packets containing mages, nemeses, friends, foes, and wave settings
2. **CGI Wrapper** (`multi_game_expedition_selector_cgi.py`) - HTTP API exposing the selector (deployed at `skriptguruai.site`)
3. **ChatGPT Custom GPT** - Consumes the API and narrates the expedition using the GPT asset files under `gpt/` (`gpt/system_prompt.txt` and `gpt/aeons_end/*.txt`)

## Commands

### Run Tests
```bash
.venv/bin/pytest tests/
```

### Run Selector CLI
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
  --content-waves "1st Wave" \
  --seed 12345
```

## Architecture

### Selector Guarantees
The selector ensures (via retry mechanism up to `max_attempts`):
- No repeated nemesis across the battle sequence
- No repeated friend or foe across battles
- No name overlap between mages and any friend/foe/nemesis
- Friends and foes appear together per battle (or both null if unavailable)

### Strictness Modes
The `strictness` parameter controls entity scoping:
- `thematic`: All entities (mages, nemeses, friends, foes) from the same wave as the setting
- `mixed`: Mages from the same wave as setting; others from any allowed content
- `open` (default): All entities from any allowed content

### Data Files (YAML)
| File | Content |
|------|---------|
| `games/aeons_end/data/aeons_end_mages.yaml` | Mage definitions with variants and story notes |
| `games/aeons_end/data/aeons_end_nemeses.yaml` | Nemesis definitions by tier (1-4) |
| `games/aeons_end/data/aeons_end_friends.yaml` | Friend (ally) definitions |
| `games/aeons_end/data/aeons_end_foes.yaml` | Foe definitions |
| `games/aeons_end/data/aeons_end_waves.yaml` | Box-to-wave mapping |
| `games/aeons_end/data/wave_settings.yaml` | Setting metadata per wave |

### Utility Module
`expedition_packet_tools.py` provides:
- `resolve_effective_seed()` - Get seed from packet meta (falls back to attempt_seed)
- `validate_packet()` - Verify packet structure and collision constraints
- `extract_story_inputs()` - Extract story-relevant data from packet

## Testing Requirements

**Run tests after any change to data files** (`*.yaml`, `*.txt`) before committing. This ensures the selector still parses datasets correctly.

## Agent Instructions

When modifying narration or operational instructions, review surrounding guidance for potential ambiguity, overlap, or contradiction introduced by the change.

### OpenAPI Schemas for GPT Actions
- Use `x-openai-isConsequential: false` for POST endpoints that are read-only operations
- Prefer POST over GET when parameters include lists or complex structures

## Legal Note
Aeon's End is a trademark of Indie Boards and Cards. This is an unofficial fan project.
