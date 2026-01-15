# Harden Types Command

**Arguments:** [path] [--dry-run] [--max-iterations=N]

**Description:** Incrementally improve type safety in TypeScript files by replacing string literals with enums, narrowing `any` types, and using shared types. Works in small, verified batches.

---

## Usage

```bash
/harden-types backend/src/services/auth.service.ts   # Single file
/harden-types backend/src/services/                  # Directory
/harden-types --dry-run                              # Analysis only, no changes
/harden-types backend/src --max-iterations=5         # Limit iterations
```

---

## Workflow

### Step 1: Parse Arguments

```bash
TARGET="${1:-}"
DRY_RUN=false
MAX_ITERATIONS=10

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --max-iterations=*) MAX_ITERATIONS="${arg#*=}" ;;
  esac
done

# If no target, prompt user
if [ -z "$TARGET" ]; then
  echo "Which file or directory to harden?"
  read -p "Path: " TARGET
fi
```

### Step 2: Safety Check

```bash
# Ensure git is clean (can rollback safely)
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ Warning: Uncommitted changes exist"
  echo "Recommend: git stash or commit first"
  read -p "Continue anyway? (y/n): " CONTINUE
  [ "$CONTINUE" != "y" ] && exit 1
fi
```

### Step 3: Load Type Hardening Skill

Read and apply `.claude/skills/quality/type-hardening/SKILL.md`

**Key steps from skill:**
1. Discover existing types (Prisma enums, shared types, constants)
2. Analyze target file(s) for hardening opportunities
3. Prioritize: Prisma enums → Shared types → Constants → New types
4. Apply 1-3 changes at a time
5. Verify with `tsc --noEmit` after each batch
6. Commit atomically

### Step 4: Execute Hardening Loop

```markdown
For each file in TARGET:
  1. Read file and identify opportunities
  2. If --dry-run: report opportunities only
  3. Otherwise:
     a. Apply batch of 1-3 type improvements
     b. Run: npx tsc --noEmit
     c. If pass: commit changes
     d. If fail: revert and report
  4. Continue until:
     - No more opportunities
     - Max iterations reached
     - Verification failure
```

### Step 5: Report Results

```markdown
## Type Hardening Report

**Target**: ${TARGET}
**Mode**: ${DRY_RUN ? "Dry Run" : "Applied"}
**Iterations**: ${COUNT}/${MAX_ITERATIONS}

### Files Processed
| File | Changes | Status |
|------|---------|--------|
| auth.service.ts | 5 | ✅ |
| user.service.ts | 3 | ✅ |

### Summary
- String literals replaced: 12
- Any types narrowed: 4
- Shared types used: 6
- New types created: 1

### Remaining Opportunities
[List if any remain]
```

---

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--dry-run` | Analyze only, no changes | `false` |
| `--max-iterations` | Stop after N iterations | `10` |

---

## Integration

### With /refactor

Can be invoked as a strategy:
```bash
/refactor --target=file.ts --strategy=types
```

### With Gemini Delegation

Safe to delegate to Gemini with proper guardrails:
```bash
/delegate-gemini task="Type hardening on backend/src/services/"
```

### With Quality Gate

Can be run as part of quality checks:
```bash
/audit --include-type-hardening
```

---

## Examples

### Example 1: Single File

```bash
/harden-types backend/src/services/notification.service.ts
```

Output:
```
Analyzing: notification.service.ts
Found 4 hardening opportunities:
  L23: 'info' → NotificationType
  L45: 'admin' → UserRole.admin
  L67: any → NotificationPayload
  L89: 'success' → NotificationType

Applying batch 1/2...
  ✅ L23, L89: Replaced with NotificationType
  ✅ tsc --noEmit passed
  ✅ Committed: "refactor: harden types in notification.service.ts"

Applying batch 2/2...
  ✅ L45: Replaced with UserRole.admin
  ✅ L67: Narrowed to NotificationPayload
  ✅ tsc --noEmit passed
  ✅ Committed: "refactor: harden types in notification.service.ts"

✅ Complete: 4 improvements applied
```

### Example 2: Dry Run Analysis

```bash
/harden-types backend/src/ --dry-run
```

Output:
```
=== Type Hardening Analysis (Dry Run) ===

backend/src/services/auth.service.ts
  L34: 'admin' → UserRole.admin
  L56: any → TokenPayload

backend/src/services/user.service.ts
  L12: 'active' → UserStatus.ACTIVE
  L78: any → UserProfile (specific type, not unknown)

backend/src/routes/notifications.ts
  No opportunities found ✅

Summary: 4 opportunities in 2 files
Run without --dry-run to apply changes
```

---

## Safety

- Always verifies with `tsc --noEmit` after changes
- Reverts on verification failure
- Commits atomically (one commit per successful batch)
- Preserves functionality (no logic changes)
- Checks existing types before creating new ones
- **No `unknown` cheating**: Replacing `any` with `unknown` is NOT an improvement - must narrow to a SPECIFIC type or leave as-is with a TODO comment

---

## Related

- **Skill**: `.claude/skills/quality/type-hardening/SKILL.md`
- **Agent**: `.claude/agents/refactor.md` (Pattern 6)
- **Workflow**: `.agent/workflows/harden-types.md` (project-specific)
