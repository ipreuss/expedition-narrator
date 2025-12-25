# expedition-narrator
Scripts and data files for the Aeon‘s End expedition narrator GPT.

## Overview
This repository contains the selector script, YAML datasets, and narration guidance used to
assemble Aeon’s End expedition packets for a GPT-based narrator. The selector performs
collision-free selection only; narration and win/lose state are handled by the narrator prompt.

## Repository layout
- `aeons_end_expedition_selector.py`: Deterministic selector that builds an expedition packet.
- `aeons_end_mages.yaml`: Mage dataset (including variants and story notes).
- `aeons_end_nemeses.yaml`: Nemesis dataset.
- `aeons_end_friends.yaml`: Friend dataset.
- `aeons_end_foes.yaml`: Foe dataset.
- `wave_settings.yaml`: Wave settings used to build expedition structure.
- `aeons_end_waves.yaml`: Wave text/settings used by the selector.
- `aeons_end_expedition_packet_schema.txt`: JSON schema for selector output.
- `aeons_end_operational_instructions.txt`: Process and handoff contract for narration.
- `aeons_end_narration_style_guide.txt`: Voice and formatting guidance.
- `aeons_end_background_selection_rules.txt`: Rules for interpreting YAML fields.
- `aeons_end_narration_style_selector.txt`: Style selector reference.
- `system_prompt.txt`: End-to-end narrator system prompt.

## Quick start
Run the selector directly with Python 3:

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

The selector prints a JSON expedition packet that conforms to
`aeons_end_expedition_packet_schema.txt`.

## Selector guarantees
Given valid datasets and scope, the selector ensures:
- No repeated nemesis across the planned battle sequence.
- No repeated friend or foe across the planned battle sequence.
- No name overlap between selected mages and any selected friend/foe/nemesis.

If the selector cannot satisfy constraints, it exits with an error, indicating a dataset or scope issue.

## Notes for narrators
- Read the selector output and follow the narration guidance in `system_prompt.txt`.
- Do not improvise selection in prose; the selector is authoritative.
- The Handoff format (a metadata code block, not the narration) never uses `Reinforcement: none`; omit the `Reinforcement:` line entirely when no reward/reinforcement applies.
