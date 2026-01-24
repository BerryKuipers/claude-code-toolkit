#!/usr/bin/env bash
set -Eeuo pipefail
LOG="${TMPDIR:-/tmp}/claude-toolkit-sync.log"
: > "$LOG"

# Detect project directory - handle being run from either:
# - ./scripts/sync-claude-toolkit.sh (project root)
# - ./.claude-toolkit/scripts/sync-claude-toolkit.sh (submodule)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "$SCRIPT_DIR" == *".claude-toolkit/scripts" ]]; then
  # Running from submodule - go up two levels
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-"$(cd "$SCRIPT_DIR/../.." && pwd)"}"
else
  # Running from project scripts/ - go up one level
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-"$(cd "$SCRIPT_DIR/.." && pwd)"}"
fi

SUBMOD_PATH="$PROJECT_DIR/.claude-toolkit"
SUBMOD_URL="https://github.com/BerryKuipers/claude-code-toolkit.git"
SRC_DIR="$SUBMOD_PATH/.claude"
DST_DIR="$PROJECT_DIR/.claude"

git config --global --add safe.directory "$PROJECT_DIR" || true
git config --global --add safe.directory "$SUBMOD_PATH" || true

echo "[sync] start $(date -Is)" | tee -a "$LOG"
echo "[sync] project=$PROJECT_DIR" | tee -a "$LOG"

need_fallback=0
if [ -d "$PROJECT_DIR/.git" ] && [ -f "$PROJECT_DIR/.gitmodules" ]; then
  echo "[sync] submodule update…" | tee -a "$LOG"
  if ! git -C "$PROJECT_DIR" submodule sync -- .claude-toolkit 2>&1 | tee -a "$LOG"; then need_fallback=1; fi
  if ! git -C "$PROJECT_DIR" submodule update --init --depth=1 .claude-toolkit 2>&1 | tee -a "$LOG"; then need_fallback=1; fi
else
  need_fallback=1
fi

if [ "$need_fallback" -eq 1 ]; then
  echo "[sync] fallback clone…" | tee -a "$LOG"
  rm -rf "$SUBMOD_PATH"
  git clone --depth=1 "$SUBMOD_URL" "$SUBMOD_PATH" 2>&1 | tee -a "$LOG"
fi

if [ ! -d "$SRC_DIR" ]; then
  echo "[sync] ERROR: $SRC_DIR missing" | tee -a "$LOG"
  exit 1
fi

mkdir -p "$DST_DIR"
for d in agents commands skills api-skills-source docs shared prompts reviews hooks rules overlays; do
  if [ -d "$SRC_DIR/$d" ]; then
    mkdir -p "$DST_DIR/$d"
    # Copy toolkit files WITHOUT deleting project-specific files
    # Only overwrites files that exist in toolkit, preserves project files (10-*, 11-*, etc.)
    cp -a "$SRC_DIR/$d"/* "$DST_DIR/$d"/ 2>/dev/null || true
    echo "[sync] merged: $d (preserved project files)" | tee -a "$LOG"
  fi
done

# Merge settings.json (toolkit hooks + project-specific settings)
if [ -f "$SRC_DIR/settings.json" ]; then
  if [ -f "$DST_DIR/settings.json" ] && command -v jq &> /dev/null; then
    # Deep merge: project settings as base, toolkit overwrites
    # This preserves project-specific keys while updating toolkit hooks
    if jq -s '.[0] * .[1]' "$DST_DIR/settings.json" "$SRC_DIR/settings.json" > "$DST_DIR/settings.json.tmp" 2>/dev/null; then
      mv "$DST_DIR/settings.json.tmp" "$DST_DIR/settings.json"
      echo "[sync] merged: settings.json (preserved project settings)" | tee -a "$LOG"
    else
      # jq merge failed - just copy toolkit version
      rm -f "$DST_DIR/settings.json.tmp"
      cp "$SRC_DIR/settings.json" "$DST_DIR/"
      echo "[sync] synced: settings.json (jq merge failed, used toolkit version)" | tee -a "$LOG"
    fi
  else
    # No existing settings or no jq - just copy
    cp "$SRC_DIR/settings.json" "$DST_DIR/"
    echo "[sync] synced: settings.json (fresh copy)" | tee -a "$LOG"
  fi
fi

# Sync templates separately (to project root templates/, not .claude/)
TEMPLATE_SRC="$SUBMOD_PATH/templates"
TEMPLATE_DST="$PROJECT_DIR/templates"
if [ -d "$TEMPLATE_SRC" ]; then
  mkdir -p "$TEMPLATE_DST"
  # Sync e2e-scripts if they exist
  if [ -d "$TEMPLATE_SRC/e2e-scripts" ]; then
    mkdir -p "$PROJECT_DIR/scripts"
    for script in "$TEMPLATE_SRC/e2e-scripts"/*.mjs; do
      if [ -f "$script" ]; then
        scriptname=$(basename "$script")
        if [ ! -f "$PROJECT_DIR/scripts/$scriptname" ]; then
          cp "$script" "$PROJECT_DIR/scripts/"
          chmod +x "$PROJECT_DIR/scripts/$scriptname"
          echo "[sync] copied new script: $scriptname" | tee -a "$LOG"
        fi
      fi
    done
  fi
  # Sync other templates
  for template_dir in github-workflows testing; do
    if [ -d "$TEMPLATE_SRC/$template_dir" ]; then
      cp -a "$TEMPLATE_SRC/$template_dir" "$TEMPLATE_DST/"
      echo "[sync] synced template: $template_dir" | tee -a "$LOG"
    fi
  done
fi

# Sync MCP broker config (if submodule exists)
BROKER_SRC="$SUBMOD_PATH/submodules/mcp-broker"
BROKER_DST="$PROJECT_DIR/.claude-toolkit/submodules/mcp-broker"
if [ -d "$BROKER_SRC" ]; then
  mkdir -p "$(dirname "$BROKER_DST")"
  if [ ! -d "$BROKER_DST" ]; then
    cp -a "$BROKER_SRC" "$BROKER_DST"
    echo "[sync] synced: mcp-broker" | tee -a "$LOG"
  fi
fi

echo "[sync] done $(date -Is)" | tee -a "$LOG"
