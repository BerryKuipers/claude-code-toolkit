---
skill-name: conductor
skill-description: Conductor Command - Complete Workflow Orchestration
---

# Conductor Skill

This skill invokes the conductor command for complete workflow orchestration.

**When invoked, load and follow the full conductor instructions from:**
`.claude/commands/conductor.md`

The conductor orchestrates complete feature development cycles:
- Issue pickup → Architecture → Implementation → Testing → PR creation

## Usage

```
/conductor                    # Full workflow from issue
/conductor issue=123          # Specific issue
/conductor --quality-gate     # Validation only
```

## IMPORTANT: Load Full Instructions

This is a thin skill wrapper. For complete conductor behavior and rules:

1. Read `.claude/commands/conductor.md`
2. Follow ALL instructions in that file
3. Pay special attention to:
   - AUTONOMOUS MODE detection
   - Task tool delegation requirements
   - Execution boundary rules
