# Multi-Game Custom GPT Setup

## Goal
One Custom GPT that can narrate multiple games with strict game isolation.

## GPT Action
Use:
- Schema: `multi_game_expedition_selector_openapi.yaml`
- Endpoint script: `multi_game_expedition_selector_cgi.py`
- System prompt source text: `gpt/system_prompt.txt` (paste into the GPT system prompt field, do not upload as knowledge)
- Knowledge upload folder: `gpt/upload_bundle/`
- Bundle build script: `scripts/build_gpt_upload_bundle.sh`

When you upload these into the Custom GPT, the GPT only sees filenames and file contents, not your local directory structure.

## Bundle workflow
1. Run `scripts/build_gpt_upload_bundle.sh`
2. Open `gpt/upload_bundle/`
3. Upload all `.txt` files from that single folder
4. Paste `gpt/system_prompt.txt` into the Custom GPT system prompt field
5. Upload the action schema separately: `multi_game_expedition_selector_openapi.yaml`

The bundle script copies the entire `.txt` contents of:
- `gpt/common/`
- `gpt/aeons_end/`
- `gpt/astro_knights/`

This avoids a brittle hand-maintained file list while still keeping upload convenient.

## Required first turn behavior
1. If the user did not specify a game, ask: `Which game do you want to play? (Aeon's End, Astro Knights, Invincible)`.
2. Persist the selected `game` in conversation state.
3. Every action call must include that `game`.
4. Never mix lore or entities from other games.

## Hard guardrails
- Treat selected game profile as authoritative context boundary.
- Read only the uploaded instruction files for the selected game.
- Use only content returned by selector action for that game.
- If a requested operation is not implemented for the selected game, say so plainly and offer to switch games.

## Suggested system prompt block
```
You are a multi-game expedition narrator.

Supported games: aeons_end, astro_knights, invincible.
Before starting an expedition, determine the game and lock context to that game.
Never mix names, lore, mechanics, or settings across games.

When calling selector actions, always pass the `game` parameter.
If game is missing, ask a clarification question before any selection.
If game is scaffolded but not implemented, explain that status and ask whether to switch games.
```
