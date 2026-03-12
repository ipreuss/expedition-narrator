# Agent Instructions

## Instruction Changes: Clarity Check
- Whenever you change narration or operational instructions, review the surrounding guidance for potential ambiguity, overlap, or contradiction introduced by the change.
- If any phrasing could be misunderstood (e.g., does it end a response vs. change ordering), revise the language in the same edit until the flow is unambiguous and consistent with related files.

## OpenAPI Schemas for ChatGPT GPT Actions

When creating or modifying OpenAPI schemas intended for use as ChatGPT GPT Actions:

### Confirmation Behavior (`x-openai-isConsequential`)
- **GET requests**: No user confirmation required (default behavior).
- **POST/PUT/DELETE requests**: User confirmation required by default.
- To **skip confirmation** for POST requests that have no side effects (read-only operations), add:
  ```yaml
  x-openai-isConsequential: false
  ```
- Only use `false` when the endpoint:
  - Does not modify server state
  - Has no side effects
  - Is essentially a "query" operation using POST for technical reasons (e.g., complex parameters, URL length limits)

### When to Use POST vs GET
- **GET**: Simple queries with few, short parameters.
- **POST**: Prefer when:
  - Parameters include lists or complex structures (e.g., `content_boxes`, `content_waves`)
  - Parameter values may be long (box names, wave names)
  - URL length could exceed browser/server limits (~2000 chars)

### Automatic Application
When adding or modifying OpenAPI schemas for GPT Actions in this repository:
1. Always consider whether POST endpoints need `x-openai-isConsequential: false`.
2. Document the rationale in the schema description if not obvious.
3. Ensure the CGI/backend supports both GET and POST where practical.

## Project Architecture

This project is an **Expedition Narrator** codebase with one multi-game Custom GPT and game-specific server assets, consisting of:
1. A **deterministic selector** that generates expedition packets
2. A **CGI wrapper** exposing the selector as an HTTP API
3. A **ChatGPT Custom GPT** that uses the API as a GPT Action and narrates the expedition

### Key Files

| File | Purpose |
|------|---------|
| `core/aeons_end_expedition_selector.py` | Core selector logic (collision-free selection of mages, nemeses, friends, foes) |
| `multi_game_expedition_selector_cgi.py` | Unified CGI wrapper for HTTP access (GET + POST) |
| `multi_game_expedition_selector_openapi.yaml` | Unified OpenAPI 3.1.0 schema for GPT Action integration |
| `expedition_packet_tools.py` | Utilities: seed resolution, packet validation, story data extraction |
| `system_prompt.txt` | Central system prompt for the multi-game Custom GPT |
| `aeons_end_operational_instructions.txt` | Aeon's End narrator workflow and handoff contract |

### Data Files (YAML)

| File | Content |
|------|---------|
| `games/aeons_end/data/aeons_end_mages.yaml` | Mage definitions with variants and story notes |
| `games/aeons_end/data/aeons_end_nemeses.yaml` | Nemesis definitions by tier (1-4) |
| `games/aeons_end/data/aeons_end_friends.yaml` | Friend (ally) definitions |
| `games/aeons_end/data/aeons_end_foes.yaml` | Foe definitions |
| `games/aeons_end/data/aeons_end_waves.yaml` | Wave-to-box mapping |
| `games/aeons_end/data/wave_settings.yaml` | Setting metadata per wave |

### Selector Guarantees

The selector ensures (via retry mechanism):
- No repeated nemesis in the battle sequence
- No repeated friend or foe across battles
- No name overlap between mages and any friend/foe/nemesis
- Friends and foes appear together per battle (or both null if unavailable)

### API Endpoint

- **URL**: `https://skriptguruai.site/cgi-bin/expedition-narrator/multi_game_expedition_selector_cgi.py`
- **Methods**: GET (query params) and POST (JSON body)
- **Required params**: `game` (string), `mage_count` (integer)
- **Optional params**: `length`, `content_waves`, `content_boxes`, `seed`, `max_attempts`

### Testing

Tests are in `tests/test_expedition_selector.py`. Run with:
```bash
.venv/bin/pytest tests/
```
