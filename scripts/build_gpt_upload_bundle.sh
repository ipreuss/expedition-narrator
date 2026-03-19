#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
bundle_dir="$repo_root/gpt/upload_bundle"

mkdir -p "$bundle_dir"
rm -f "$bundle_dir"/*

source_dirs=(
  "gpt/common"
  "gpt/aeons_end"
  "gpt/astro_knights"
)

for relative_dir in "${source_dirs[@]}"; do
  while IFS= read -r source_file; do
    cp "$source_file" "$bundle_dir/"
  done < <(find "$repo_root/$relative_dir" -maxdepth 1 -type f -name '*.txt' | sort)
done

cat > "$bundle_dir/UPLOAD_ORDER.txt" <<'EOF'
Upload all `.txt` files from this folder into the Custom GPT knowledge.

This bundle is built from the full contents of:
- `gpt/common/`
- `gpt/aeons_end/`
- `gpt/astro_knights/`

Do NOT upload `system_prompt.txt` as a knowledge file.
Paste its contents separately into the Custom GPT system prompt field.

The action schema is separate and still comes from:
- multi_game_expedition_selector_openapi.yaml
EOF

echo "Built GPT upload bundle in: $bundle_dir"
