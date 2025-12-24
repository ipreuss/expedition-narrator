# Aeon’s End — Background and Selection Rules

This document governs how content is selected, interpreted, and constrained
when generating an expedition.

---

## 1. Content Sources

All selections are made from YAML datasets using Python-based randomization:
- Settings (per wave)
- Mages
- Nemeses
- Friends
- Foes

Randomization happens before narration begins.

---

## 2. Reading Before Writing (Mandatory)

Before any narration step, the model must:
- Read all background text for:
  - the chosen setting
  - the selected mages
  - the active nemesis
  - the current friend and foe (if any)

Background knowledge informs:
- tone
- relationships
- plausible motivations
- behavior and risk tolerance

---

## 3. Wave Settings

### Setting Selection
- Each expedition uses exactly one setting.
- A setting represents a specific historical moment, mood, and world state.

### Interpretation Rule
- Setting descriptions are inspirational, not prescriptive.
- Do not reuse phrases, imagery, or sensory anchors verbatim.
- Vary locations and manifestations to avoid repetition.

---

## 4. Character Availability & Uniqueness

### Multiple Forms
- Some characters may exist as mage, friend, foe, or nemesis.
- Only one form may appear in a single expedition.

Any collision (duplicate across forms) makes the expedition packet invalid; do not use it. The selector already retries internally and is designed to prevent these collisions.

### Mage Structure
- Each mage is always associated with at least one source box.
- Shared information may exist across versions.
- Source box must be specified in the Handoff.

### Story Notes
- Mage story notes describe past experiences.
- Use them sparingly to influence behavior or decisions,
  never as exposition dumps.

---

## 5. Friends & Foes

### Availability
- Friends and Foes are available if their wave is included in content scope.
- They do not need to match the setting’s wave.

### Balance
- If Friends or Foes are available, both must be included.
- Some waves may include neither.

### Rotation Rule
- Each battle uses a different Friend and Foe.
- No repetition until all available options are exhausted.
- Reuse requires narrative justification.

---

## 6. Special Cases

### Outcasts / Wave 5
- The expedition may protect Gravehold or Xaxos.
- If Xaxos is chosen:
  - Xaxos may act and speak as a narrative presence.
  - “Protect: Xaxos” must appear in the Handoff.

---

## 7. Nemesis Progression

- The Nemesis does not change until progression conditions are met.
- Losses up to two times cause rematches.
- Advancement occurs on win or third loss only.

---

## 8. Randomization Discipline

- All selections are performed via Python.
- The narrative adapts to results; it never influences selection.
- Re-rolls occur only to resolve invalid combinations.

---

## 9. Location Variability

- Vary physical locations across the expedition:
  settlements, ruins, underground spaces, surface journeys, void zones.
- Do not anchor an entire expedition to a single locale unless required by setting.
