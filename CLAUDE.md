# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Expedition Narrator** for Aeon's End, a board game companion that generates narrative expeditions. The system has three components:

1. **Deterministic Selector** (`aeons_end_expedition_selector.py`) - Generates collision-free expedition packets containing mages, nemeses, friends, foes, and wave settings
2. **CGI Wrapper** (`aeons_end_expedition_selector_cgi.py`) - HTTP API exposing the selector (deployed at `skriptguruai.site`)
3. **ChatGPT Custom GPT** - Consumes the API and narrates the expedition using guidance in `narrator_instructions/`

## Commands

### Run Tests
```bash
pytest tests/
```

### Run Selector CLI
```bash
python aeons_end_expedition_selector.py \
  --mages-yaml aeons_end_mages.yaml \
  --settings-yaml wave_settings.yaml \
  --waves-yaml aeons_end_waves.yaml \
  --nemeses-yaml aeons_end_nemeses.yaml \
  --friends-yaml aeons_end_friends.yaml \
  --foes-yaml aeons_end_foes.yaml \
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
| `aeons_end_mages.yaml` | Mage definitions with variants and story notes |
| `aeons_end_nemeses.yaml` | Nemesis definitions by tier (1-4) |
| `aeons_end_friends.yaml` | Friend (ally) definitions |
| `aeons_end_foes.yaml` | Foe definitions |
| `aeons_end_waves.yaml` | Box-to-wave mapping |
| `wave_settings.yaml` | Setting metadata per wave |

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
