# Gemini Delegation - Credit-Saving Workflow

Optional workflow for delegating high-volume, low-risk work to Gemini to save Cloud credits.

## Quick Start

```bash
# Propose delegation for a task
/delegate-gemini add JSDoc to all exported functions in src/utils/

# Verify Gemini's results when you return
/delegate-gemini --verify-only
```

## How It Works

1. **You request** delegation via `/delegate-gemini`
2. **Cloud agent triages** work using a 5-dimension rubric (0-25 score)
3. **You approve** or decline (delegation is NEVER automatic)
4. **Cloud generates** a Handoff Pack (scoped Gemini prompt)
5. **You run Gemini** with the pack
6. **You paste back** Gemini's completion report
7. **Cloud verifies** results and either accepts or generates fix-up prompt

## When to Use

### Good Candidates (Score 18+)
- Repetitive changes across many files
- Adding documentation/comments
- Boilerplate generation (CRUD, test stubs)
- Format/lint fixes
- Type definition generation
- Test case expansion

### Keep in Cloud (Score <13)
- Architecture decisions
- Complex business logic
- Security-sensitive code
- Cross-cutting refactors
- API contract changes

## Triage Rubric

| Dimension | 5 (Best) | 1 (Worst) |
|-----------|----------|-----------|
| Repetitiveness | Same pattern across files | Unique per-file logic |
| Risk Level | Format/style only | Business logic changes |
| Verifiability | Lint/typecheck catches all | Manual review required |
| Pattern Clarity | Clear with examples | Ambiguous |
| Scope Isolation | Single folder | Cross-cutting |

**Score Thresholds:**
- 18+ = Good candidate
- 13-17 = Consider carefully
- <13 = Keep in Cloud

## Key Principles

1. **Always optional** - You decide whether to delegate
2. **Always requires approval** - Cloud proposes, you confirm
3. **Scoped narrowly** - Better to under-scope than over-scope
4. **Verified after** - Cloud checks Gemini's work
5. **Fix-up loop** - If verification fails, get targeted fix prompt

## Files Added

```
.claude/
  agents/
    gemini-delegation.md    # Core delegation orchestrator
  commands/
    delegate-gemini.md      # User entry point
  skills/
    gemini-workflows/
      handoff-pack/
        SKILL.md            # Handoff Pack generator
```

## Integration

The orchestrator agent can suggest delegation when detecting high-volume repetitive work. This is always advisory - you must approve.

## See Also

- `/delegate-gemini --help` - Command usage
- `.claude/agents/gemini-delegation.md` - Full agent docs
- `.claude/skills/gemini-workflows/handoff-pack/SKILL.md` - Pack generator
