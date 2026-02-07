#!/usr/bin/env bash
set -Eeuo pipefail
LOG="${TMPDIR:-/tmp}/claude-toolkit-sync.log"
: > "$LOG"

# ─── Tier definitions ────────────────────────────────────────────────
# CORE: always synced to consuming projects (minimal footprint)
# WORKFLOW: autonomous loops, mega-workflows, gemini delegation
# INFRA: infrastructure, DNS, VPS, deploy verification
# DEBUG: meta-validators, architecture tests, debug tools
# ALL: everything in the toolkit

CORE_HOOKS=(
  session-start.sh
  load-overlay.sh
  post-tool-quality-gate.sh
  validate-code-quality.sh
)

CORE_AGENTS=(
  orchestrator.md
  conductor.md
  implementation.md
  build-error-resolver.md
  code-reviewer.md
  architect.md
  refactor.md
  researcher.md
)

CORE_COMMANDS=(
  help.md
  conductor.md
  orchestrator.md
  architect.md
  audit.md
  refactor.md
  review-pr.md
  pr-process.md
  deploy.md
  create-command-or-agent.md
  create-test.md
  issue-pickup.md
  issue-create.md
  test-all.md
  start-workflow.md
  fix-vulns.md
  update-deps.md
  harden-types.md
)
# wrappers/bk-* are always included in core
CORE_COMMAND_DIRS=(wrappers)

CORE_SKILL_DIRS=(
  quality
  git-workflows
  testing/run-comprehensive-tests
  scaffold
  infrastructure
)

WORKFLOW_COMMANDS=(
  loop.md
  loop-stop.md
  ralph-loop.md
  reflect.md
  reflect-enable.md
  reflect-disable.md
  promote-learnings.md
  start-mega-workflow.md
  init-harness.md
  harness-start.md
  codex-triage.md
  parallel-worktree.md
  delegate-gemini.md
  sync-gemini.md
)
WORKFLOW_AGENTS=(
  mega-workflow.md
  gemini-delegation.md
  context-memory.md
)
WORKFLOW_SKILL_DIRS=(
  gemini-api
  gemini-workflows
  state-management
  meta/continuous-learning
)

INFRA_COMMANDS=(
  dns.md
  vps.md
  verify-deploy.md
  capture-pages.md
)
INFRA_AGENTS=(
  infrastructure.md
  page-capture.md
)
INFRA_SKILL_DIRS=(
  infrastructure/dns
  infrastructure/vps
)

DEBUG_COMMANDS=(
  system-discovery.md
  system-review.md
  test-agent-system.md
  test-command-architecture.md
  test-delegation-flow.md
  test-slash-command-composition.md
  command-analyzer.md
  architecture-tester.md
  debug-integration-summary.md
  manual-debug-test-guide.md
  state-management.md
)
DEBUG_AGENTS=(
  agent-creator.md
  system-validator.md
  meta-agent-example.md
)

SPECIALIZED_COMMANDS=(
  fix-e2e-tests.md
  pick-next-pr.md
  sync-tests.md
  design-review.md
  test-ui.md
  test-user-flow.md
)
SPECIALIZED_AGENTS=(
  database.md
  security-pentest.md
  dependency-manager.md
  e2e-test-maintainer.md
  integration-validator.md
  audit.md
  browser-testing.md
  ui-frontend-agent.md
  design.md
  qa-triage.md
)
SPECIALIZED_SKILL_DIRS=(
  github-integration
  memory
  meta/skill-creator
  security
  styling
  overlay-loader
  testing/tdd-workflow
  quality/type-hardening
  quality/record-quality-baseline
  quality/validate-coverage-threshold
)

# ─── Parse arguments ─────────────────────────────────────────────────
TIER="core"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)       TIER="all"; shift ;;
    --tier)      TIER="$2"; shift 2 ;;
    --tier=*)    TIER="${1#--tier=}"; shift ;;
    --list)      # List available tiers and exit
      echo "Available tiers:"
      echo "  core       - Essential agents, commands, skills (default)"
      echo "  workflow   - core + autonomous loops, gemini, mega-workflows"
      echo "  infra      - core + infrastructure, DNS, VPS, deploy"
      echo "  debug      - core + meta-validators, architecture tests"
      echo "  specialized - core + DB, security, e2e, browser, design agents"
      echo "  all        - Everything in the toolkit"
      exit 0 ;;
    -h|--help)
      echo "Usage: sync-claude-toolkit.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --tier TIER   Sync tier: core|workflow|infra|debug|specialized|all (default: core)"
      echo "  --all         Shorthand for --tier all"
      echo "  --list        List available tiers"
      echo "  -h, --help    Show this help"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ─── Detect project directory ────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "$SCRIPT_DIR" == *".claude-toolkit/scripts" ]]; then
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-"$(cd "$SCRIPT_DIR/../.." && pwd)"}"
else
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-"$(cd "$SCRIPT_DIR/.." && pwd)"}"
fi

SUBMOD_PATH="$PROJECT_DIR/.claude-toolkit"
SUBMOD_URL="https://github.com/BerryKuipers/claude-code-toolkit.git"
SRC_DIR="$SUBMOD_PATH/.claude"
DST_DIR="$PROJECT_DIR/.claude"

git config --global --add safe.directory "$PROJECT_DIR" || true
git config --global --add safe.directory "$SUBMOD_PATH" || true

echo "[sync] start $(date -Is) tier=$TIER" | tee -a "$LOG"
echo "[sync] project=$PROJECT_DIR" | tee -a "$LOG"

# ─── Submodule update ────────────────────────────────────────────────
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

# ─── Build allowed-file lists for cleanup ─────────────────────────────
# These accumulate everything that SHOULD exist for the selected tier.
# After syncing, we remove toolkit-origin files NOT in these lists.
ALLOWED_HOOKS=("${CORE_HOOKS[@]}")
ALLOWED_AGENTS=("${CORE_AGENTS[@]}")
ALLOWED_COMMANDS=("${CORE_COMMANDS[@]}")
ALLOWED_COMMAND_DIRS=("${CORE_COMMAND_DIRS[@]}")
ALLOWED_SKILL_DIRS=("${CORE_SKILL_DIRS[@]}")

if [ "$TIER" = "all" ]; then
  # all = no cleanup needed, everything is allowed
  CLEANUP_ENABLED=0
else
  CLEANUP_ENABLED=1
  case "$TIER" in
    workflow)
      ALLOWED_COMMANDS+=("${WORKFLOW_COMMANDS[@]}")
      ALLOWED_AGENTS+=("${WORKFLOW_AGENTS[@]}")
      ALLOWED_SKILL_DIRS+=("${WORKFLOW_SKILL_DIRS[@]}")
      ;;
    infra)
      ALLOWED_COMMANDS+=("${INFRA_COMMANDS[@]}")
      ALLOWED_AGENTS+=("${INFRA_AGENTS[@]}")
      ALLOWED_SKILL_DIRS+=("${INFRA_SKILL_DIRS[@]}")
      ;;
    debug)
      ALLOWED_COMMANDS+=("${DEBUG_COMMANDS[@]}")
      ALLOWED_AGENTS+=("${DEBUG_AGENTS[@]}")
      ALLOWED_COMMAND_DIRS+=(docs)
      ;;
    specialized)
      ALLOWED_COMMANDS+=("${SPECIALIZED_COMMANDS[@]}")
      ALLOWED_AGENTS+=("${SPECIALIZED_AGENTS[@]}")
      ALLOWED_SKILL_DIRS+=("${SPECIALIZED_SKILL_DIRS[@]}")
      ;;
  esac
fi

# ─── Helper: check if value is in array ───────────────────────────────
in_array() {
  local needle="$1"
  shift
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

# ─── Helper: copy specific files from src to dst ─────────────────────
sync_files() {
  local src_subdir="$1"
  shift
  local files=("$@")
  local src="$SRC_DIR/$src_subdir"
  local dst="$DST_DIR/$src_subdir"

  if [ ! -d "$src" ]; then return; fi
  mkdir -p "$dst"

  local count=0
  for f in "${files[@]}"; do
    if [ -f "$src/$f" ]; then
      cp -a "$src/$f" "$dst/$f"
      ((count++))
    fi
  done
  echo "[sync] $src_subdir: $count files" | tee -a "$LOG"
}

# Helper: copy entire subdirectory
sync_dir() {
  local src_subdir="$1"
  local src="$SRC_DIR/$src_subdir"
  local dst="$DST_DIR/$src_subdir"

  if [ ! -d "$src" ]; then return; fi
  mkdir -p "$dst"
  cp -a "$src"/* "$dst"/ 2>/dev/null || true
  echo "[sync] $src_subdir: full dir" | tee -a "$LOG"
}

# Helper: copy skill directories (nested structure)
sync_skill_dirs() {
  local dirs=("$@")
  for skill_dir in "${dirs[@]}"; do
    local src="$SRC_DIR/skills/$skill_dir"
    local dst="$DST_DIR/skills/$skill_dir"
    if [ -d "$src" ]; then
      mkdir -p "$dst"
      cp -a "$src"/* "$dst"/ 2>/dev/null || true
      echo "[sync] skills/$skill_dir" | tee -a "$LOG"
    fi
  done
}

# Helper: copy command subdirectories (e.g. wrappers/, docs/)
sync_command_dirs() {
  local dirs=("$@")
  for cmd_dir in "${dirs[@]}"; do
    local src="$SRC_DIR/commands/$cmd_dir"
    local dst="$DST_DIR/commands/$cmd_dir"
    if [ -d "$src" ]; then
      mkdir -p "$dst"
      cp -a "$src"/* "$dst"/ 2>/dev/null || true
      echo "[sync] commands/$cmd_dir" | tee -a "$LOG"
    fi
  done
}

# ─── Always sync: rules, settings, CLAUDE.md ─────────────────────────
mkdir -p "$DST_DIR"

# Rules are small and always needed
if [ -d "$SRC_DIR/rules" ]; then
  sync_dir "rules"
fi

# Overlays are project-specific config
if [ -d "$SRC_DIR/overlays" ]; then
  sync_dir "overlays"
fi

# Settings.json merge
if [ -f "$SRC_DIR/settings.json" ]; then
  if [ -f "$DST_DIR/settings.json" ] && command -v jq &> /dev/null; then
    if jq -s '.[0] * .[1]' "$DST_DIR/settings.json" "$SRC_DIR/settings.json" > "$DST_DIR/settings.json.tmp" 2>/dev/null; then
      mv "$DST_DIR/settings.json.tmp" "$DST_DIR/settings.json"
      echo "[sync] merged: settings.json" | tee -a "$LOG"
    else
      rm -f "$DST_DIR/settings.json.tmp"
      cp "$SRC_DIR/settings.json" "$DST_DIR/"
      echo "[sync] synced: settings.json (fresh)" | tee -a "$LOG"
    fi
  else
    cp "$SRC_DIR/settings.json" "$DST_DIR/"
    echo "[sync] synced: settings.json (fresh)" | tee -a "$LOG"
  fi
fi

# CLAUDE.md from toolkit
if [ -f "$SRC_DIR/CLAUDE.md" ]; then
  cp "$SRC_DIR/CLAUDE.md" "$DST_DIR/CLAUDE.md"
  echo "[sync] synced: CLAUDE.md" | tee -a "$LOG"
fi

# ─── Tier: ALL (legacy behavior) ─────────────────────────────────────
if [ "$TIER" = "all" ]; then
  echo "[sync] tier=all: syncing everything" | tee -a "$LOG"
  for d in agents commands skills hooks; do
    if [ -d "$SRC_DIR/$d" ]; then
      sync_dir "$d"
    fi
  done
  # Also sync underscore commands and docs
  for d in api-skills-source docs shared prompts reviews; do
    if [ -d "$SRC_DIR/$d" ]; then
      sync_dir "$d"
    fi
  done
else
  # ─── Tier: CORE (always) ─────────────────────────────────────────
  echo "[sync] tier=core" | tee -a "$LOG"
  sync_files "hooks" "${CORE_HOOKS[@]}"
  sync_files "agents" "${CORE_AGENTS[@]}"
  sync_files "commands" "${CORE_COMMANDS[@]}"
  sync_command_dirs "${CORE_COMMAND_DIRS[@]}"
  sync_skill_dirs "${CORE_SKILL_DIRS[@]}"

  # Copy top-level skill docs (non-directory files like README, QUICKSTART etc)
  mkdir -p "$DST_DIR/skills"
  for f in "$SRC_DIR/skills"/*.md; do
    [ -f "$f" ] && cp -a "$f" "$DST_DIR/skills/" 2>/dev/null || true
  done

  # ─── Additional tiers ─────────────────────────────────────────────
  case "$TIER" in
    workflow)
      echo "[sync] +tier=workflow" | tee -a "$LOG"
      sync_files "commands" "${WORKFLOW_COMMANDS[@]}"
      sync_files "agents" "${WORKFLOW_AGENTS[@]}"
      sync_skill_dirs "${WORKFLOW_SKILL_DIRS[@]}"
      ;;
    infra)
      echo "[sync] +tier=infra" | tee -a "$LOG"
      sync_files "commands" "${INFRA_COMMANDS[@]}"
      sync_files "agents" "${INFRA_AGENTS[@]}"
      sync_skill_dirs "${INFRA_SKILL_DIRS[@]}"
      ;;
    debug)
      echo "[sync] +tier=debug" | tee -a "$LOG"
      sync_files "commands" "${DEBUG_COMMANDS[@]}"
      sync_files "agents" "${DEBUG_AGENTS[@]}"
      # Sync underscore commands (internal docs)
      for f in "$SRC_DIR/commands"/_*.md; do
        [ -f "$f" ] && cp -a "$f" "$DST_DIR/commands/" 2>/dev/null || true
      done
      sync_command_dirs "docs"
      ;;
    specialized)
      echo "[sync] +tier=specialized" | tee -a "$LOG"
      sync_files "commands" "${SPECIALIZED_COMMANDS[@]}"
      sync_files "agents" "${SPECIALIZED_AGENTS[@]}"
      sync_skill_dirs "${SPECIALIZED_SKILL_DIRS[@]}"
      ;;
    core) ;; # Already handled above
    *)
      echo "[sync] WARNING: unknown tier '$TIER', using core only" | tee -a "$LOG"
      ;;
  esac
fi

# ─── Cleanup: remove stale toolkit files not in current tier ──────────
# Only delete files that ALSO exist in toolkit source (project-specific files are safe)
if [ "$CLEANUP_ENABLED" -eq 1 ]; then
  echo "[cleanup] removing toolkit files outside tier=$TIER" | tee -a "$LOG"

  # Cleanup flat files (hooks, agents, top-level commands)
  cleanup_flat_files() {
    local subdir="$1"
    shift
    local allowed=("$@")
    local src="$SRC_DIR/$subdir"
    local dst="$DST_DIR/$subdir"

    [ -d "$dst" ] && [ -d "$src" ] || return
    local removed=0
    for dst_file in "$dst"/*.md "$dst"/*.sh "$dst"/*.ps1; do
      [ -f "$dst_file" ] || continue
      local base
      base=$(basename "$dst_file")
      # Only remove if it exists in toolkit source (= came from toolkit)
      if [ -f "$src/$base" ]; then
        if ! in_array "$base" "${allowed[@]}"; then
          rm -f "$dst_file"
          ((removed++))
        fi
      fi
      # Files NOT in toolkit source are project-specific -> keep
    done
    if [ "$removed" -gt 0 ]; then
      echo "[cleanup] $subdir: removed $removed stale toolkit files" | tee -a "$LOG"
    fi
  }

  cleanup_flat_files "hooks" "${ALLOWED_HOOKS[@]}"
  cleanup_flat_files "agents" "${ALLOWED_AGENTS[@]}"
  cleanup_flat_files "commands" "${ALLOWED_COMMANDS[@]}"

  # Cleanup command subdirectories (wrappers/, docs/, etc.)
  # Remove toolkit-origin subdirs NOT in ALLOWED_COMMAND_DIRS
  if [ -d "$DST_DIR/commands" ] && [ -d "$SRC_DIR/commands" ]; then
    for dst_subdir in "$DST_DIR/commands"/*/; do
      [ -d "$dst_subdir" ] || continue
      _dirname=$(basename "$dst_subdir")
      if [ -d "$SRC_DIR/commands/$_dirname" ]; then
        if ! in_array "$_dirname" "${ALLOWED_COMMAND_DIRS[@]}"; then
          rm -rf "$dst_subdir"
          echo "[cleanup] commands/$_dirname: removed (not in tier)" | tee -a "$LOG"
        fi
      fi
    done
  fi

  # Cleanup underscore commands (_*.md) - only allowed in debug tier
  if [ "$TIER" != "debug" ]; then
    if [ -d "$DST_DIR/commands" ] && [ -d "$SRC_DIR/commands" ]; then
      _underscore_removed=0
      for dst_file in "$DST_DIR/commands"/_*.md; do
        [ -f "$dst_file" ] || continue
        _base=$(basename "$dst_file")
        if [ -f "$SRC_DIR/commands/$_base" ]; then
          rm -f "$dst_file"
          ((_underscore_removed++))
        fi
      done
      if [ "$_underscore_removed" -gt 0 ]; then
        echo "[cleanup] commands/_*: removed $_underscore_removed internal docs" | tee -a "$LOG"
      fi
    fi
  fi

  # Cleanup skill directories - remove toolkit-origin skill dirs not in tier
  if [ -d "$DST_DIR/skills" ] && [ -d "$SRC_DIR/skills" ]; then
    while IFS= read -r -d '' _src_skill_dir; do
      _rel_path="${_src_skill_dir#"$SRC_DIR/skills/"}"
      _dst_skill_dir="$DST_DIR/skills/$_rel_path"

      if [ -d "$_dst_skill_dir" ]; then
        if ! in_array "$_rel_path" "${ALLOWED_SKILL_DIRS[@]}"; then
          # Don't remove parent if a child is allowed (e.g. keep quality/ if quality/validate-build is allowed)
          _is_parent=0
          for _allowed_dir in "${ALLOWED_SKILL_DIRS[@]}"; do
            if [[ "$_allowed_dir" == "$_rel_path"/* ]]; then
              _is_parent=1
              break
            fi
          done
          if [ "$_is_parent" -eq 0 ]; then
            rm -rf "$_dst_skill_dir"
            echo "[cleanup] skills/$_rel_path: removed (not in tier)" | tee -a "$LOG"
          fi
        fi
      fi
    done < <(find "$SRC_DIR/skills" -mindepth 1 -maxdepth 2 -type d -print0 2>/dev/null)
  fi

  echo "[cleanup] done" | tee -a "$LOG"
fi

# ─── Templates (always sync) ─────────────────────────────────────────
TEMPLATE_SRC="$SUBMOD_PATH/templates"
TEMPLATE_DST="$PROJECT_DIR/templates"
if [ -d "$TEMPLATE_SRC" ]; then
  mkdir -p "$TEMPLATE_DST"
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
  for template_dir in github-workflows testing; do
    if [ -d "$TEMPLATE_SRC/$template_dir" ]; then
      cp -a "$TEMPLATE_SRC/$template_dir" "$TEMPLATE_DST/"
      echo "[sync] synced template: $template_dir" | tee -a "$LOG"
    fi
  done
fi

# ─── MCP broker config ───────────────────────────────────────────────
BROKER_SRC="$SUBMOD_PATH/submodules/mcp-broker"
BROKER_DST="$PROJECT_DIR/.claude-toolkit/submodules/mcp-broker"
if [ -d "$BROKER_SRC" ]; then
  mkdir -p "$(dirname "$BROKER_DST")"
  if [ ! -d "$BROKER_DST" ]; then
    cp -a "$BROKER_SRC" "$BROKER_DST"
    echo "[sync] synced: mcp-broker" | tee -a "$LOG"
  fi
fi

echo "[sync] done $(date -Is) tier=$TIER" | tee -a "$LOG"
