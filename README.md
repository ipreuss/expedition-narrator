# expedition-narrator
Scripts and data files for the Aeon‘s End expedition narrator GPT.

## Overview
This repository contains the selector script, YAML datasets, and narration guidance used to
assemble Aeon’s End expedition packets for a GPT-based narrator. The selector performs
collision-free selection only; narration and win/lose state are handled by the narrator prompt.

## Repository layout
- `aeons_end_expedition_selector_v3.py`: Deterministic selector that builds an expedition packet.
- `aeons_end_mages_final_clean4.yaml`: Mage dataset (including variants and story notes).
- `aeons_end_nemeses.yaml`: Nemesis dataset.
- `aeons_end_friends.yaml`: Friend dataset.
- `aeons_end_foes.yaml`: Foe dataset.
- `wave_settings.yaml`: Wave settings used to build expedition structure.
- `aeons_end_waves.yaml`: Wave text/settings used by the selector.
- `Aeons_End_Expedition_Packet_Schema.md`: JSON schema for selector output.
- `Aeons_End_Operational_Instructions_With_Selector_v3_1.md`: Process and handoff contract for narration.
- `Aeons_End_Narration_Style_Guide_Canonical.md`: Voice and formatting guidance.
- `Aeons_End_Background_And_Selection_Rules_Clean.md`: Rules for interpreting YAML fields.
- `Aeons_End_Narration_Style_Selector_Reconstructed.md`: Style selector reference.
- `system_prompt.md`: End-to-end narrator system prompt.

## Quick start
Run the selector directly with Python 3:

```bash
python aeons_end_expedition_selector_v3.py \
  --mages-yaml aeons_end_mages_final_clean4.yaml \
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
`Aeons_End_Expedition_Packet_Schema.md`.

## Selector guarantees
Given valid datasets and scope, the selector ensures:
- No repeated nemesis across the planned battle sequence.
- No repeated friend or foe across the planned battle sequence.
- No name overlap between selected mages and any selected friend/foe/nemesis.

If the selector cannot satisfy constraints, it exits with an error, indicating a dataset or scope issue.

## Notes for narrators
- Read the selector output and follow the narration guidance in `system_prompt.md`.
- Do not improvise selection in prose; the selector is authoritative.
