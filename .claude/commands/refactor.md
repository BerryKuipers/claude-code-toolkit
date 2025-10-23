# Refactor Command

**Arguments:** [--target=file|directory] [--strategy=extract|simplify|rename] [--test-first]

**Description:** User-facing command that delegates to the refactor agent for safe code refactoring. Thin wrapper with CLI interface.

---

## ⚠️ Important: Thin Wrapper

**This command delegates all work to:** `.claude/agents/refactor.md`

---

## Usage

```bash
/refactor --target=ServiceFile.ts --strategy=extract
/refactor --target=src/utils --test-first
```

---

## Workflow

### Step 1: Parse Arguments
```bash
TARGET=""
STRATEGY="simplify"
TEST_FIRST=false

for arg in "$@"; do
  case $arg in
    --target=*) TARGET="${arg#*=}" ;;
    --strategy=*) STRATEGY="${arg#*=}" ;;
    --test-first) TEST_FIRST=true ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "❌ --target is required"
  exit 1
fi
```

### Step 2: Delegate to Refactor Agent

```markdown
"I need safe refactoring from the refactor specialist.

Refactor Request:
- **Target**: $TARGET
- **Strategy**: $STRATEGY (extract-method / simplify / rename / modernize)
- **Test First**: $TEST_FIRST (validate tests pass before refactoring)
- **Project Root**: $(pwd)

Approach:
1. Analyze target code structure
2. Run tests if --test-first (ensure passing before changes)
3. Apply refactoring strategy safely
4. Validate tests still pass after changes
5. Ensure no behavior changes
6. Provide diff and summary

Safety Requirements:
- Preserve all functionality
- Keep tests passing
- Atomic changes only
- Rollback on test failure"
```

### Step 3: Display Results
```bash
echo "✅ Refactoring complete - review changes above"
```

---

## Notes

**Agent-First Architecture:**
- This command = User interface
- `.claude/agents/refactor.md` = Worker (does actual refactoring)
- All refactoring logic lives in the agent

**Generated**: 2025-10-23 (Modernized thin wrapper)
