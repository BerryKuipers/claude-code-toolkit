# Create - Command & Agent Scaffolding

**Arguments:** "<description>" [--dry-run] [--output-path=<path>] [--type=tool|workflow|agent]

**Success Criteria:** Valid command/agent file generated, validated against architectural principles, usage examples provided

**Description:** Scaffolding entrypoint that delegates to AgentCreatorAgent for intelligent command/agent generation following TribeVibe best practices.

---

## Purpose

Simple entrypoint command that delegates to the specialized **AgentCreatorAgent** for meta-level scaffolding of new commands and agents.

Creates new components that automatically follow:
- ✅ Hub-and-spoke architecture
- ✅ SOLID/DRY principles
- ✅ Separation of concerns
- ✅ Markdown-first approach
- ✅ TribeVibe conventions

---

## ⚠️ Important: Entrypoint Only

**This command is a simple entrypoint that delegates to AgentCreatorAgent:**
- ✅ Parses user description and options
- ✅ Delegates to AgentCreatorAgent via orchestrator
- ✅ Returns generated file content and recommendations
- ❌ Does NOT contain scaffolding logic (that's in the agent)
- ❌ Does NOT validate architecture (agent does this)

**All scaffolding intelligence lives in `.claude/agents/agent-creator.md`**

---

## Workflow

### **Step 1: Parse Arguments**

```bash
# Required: Natural language description
DESCRIPTION="$1"

# Optional: Dry-run mode (show what would be generated)
DRY_RUN="${2:-false}"

# Optional: Custom output path
OUTPUT_PATH="${3:-.claude/commands}"

# Optional: Force specific type (otherwise agent classifies)
FORCE_TYPE="${4:-auto}"

echo "🏗️ CREATE - Command & Agent Scaffolder"
echo "======================================"
echo ""
echo "Description: $DESCRIPTION"
echo "Dry-Run: $DRY_RUN"
echo "Output Path: $OUTPUT_PATH"
echo "Type: $FORCE_TYPE"
echo ""
```

**Validation:**
- Description is required and non-empty
- Output path must be valid directory (if specified)
- Type must be: tool, workflow, agent, or auto

### **Step 2: Delegate to AgentCreatorAgent**

**Use orchestrator to invoke AgentCreatorAgent:**

```bash
echo "Delegating to AgentCreatorAgent via orchestrator..."
echo ""

# Build task description
TASK="Create new component: '$DESCRIPTION'"

if [[ "$DRY_RUN" == "true" ]]; then
    TASK="$TASK (dry-run mode - show scaffold without creating files)"
fi

if [[ "$FORCE_TYPE" != "auto" ]]; then
    TASK="$TASK (forced type: $FORCE_TYPE)"
fi

# Delegate to orchestrator which routes to AgentCreatorAgent
# Orchestrator recognizes "create new component" → routes to agent-creator
```

**Delegation call:**
```
SlashCommand "/orchestrator" "task='$TASK' mode=full agent=agent-creator output_path=$OUTPUT_PATH"
```

### **Step 3: Return Results**

The AgentCreatorAgent returns comprehensive scaffolding output which this command passes through to the user.

**Expected output:**
- Classification decision (tool/workflow/agent)
- Generated file content
- File path (.claude/commands/ or .claude/agents/)
- Usage examples
- Integration test scaffold (optional)
- Architectural compliance validation
- Recommendations for integration

---

## Arguments

### `"<description>"` (required)
Natural language description of the capability needed.

**Examples:**
- `"check open PRs for dependency updates"`
- `"validate authentication system follows VSA and SOLID"`
- `"orchestrate database migration with rollback and testing"`
- `"refactor UserService to follow single responsibility"`

**Tips:**
- Be specific about what the component should do
- Include key actions (check, validate, orchestrate, refactor)
- Mention scope if relevant (system-wide, feature-specific, file-level)

### `--dry-run` (optional)
Preview the scaffolded component without creating files.

**When to use:**
- Review before committing
- Validate classification decision
- Check architectural compliance
- Iterate on description wording

**Default**: `false` (creates files)

### `--output-path=<path>` (optional)
Custom output directory for generated file.

**Default**:
- Commands: `.claude/commands/`
- Agents: `.claude/agents/`

**Use cases:**
- Testing scaffolding without polluting main directories
- Generating to review location first
- Custom organizational structure

### `--type=tool|workflow|agent` (optional)
Force specific component type (bypasses agent classification).

**When to use:**
- You know exactly what type you need
- Agent classification seems incorrect
- Testing specific scaffold templates

**Default**: `auto` (agent decides via classification logic)

⚠️ **Warning**: Forcing type may result in inappropriate structure if description doesn't match type

---

## Usage Examples

### Example 1: Basic Command Creation
```bash
/create "check open PRs for dependency updates"

# AgentCreatorAgent decides: TOOL
# Generates: .claude/commands/pr-check-deps.md
# Output: Usage examples, test scaffold, integration notes
```

### Example 2: Workflow Creation with Dry-Run
```bash
/create "validate authentication system follows VSA and SOLID" --dry-run

# AgentCreatorAgent decides: WORKFLOW
# Preview: 7-step workflow structure shown
# No files created (dry-run mode)
```

### Example 3: Agent Creation
```bash
/create "orchestrate database migration with rollback, testing, and state management"

# AgentCreatorAgent decides: AGENT
# Generates: .claude/agents/db-migration-orchestrator.md
# Includes: YAML frontmatter, phases, delegation patterns
```

### Example 4: Force Specific Type
```bash
/create "analyze code complexity metrics" --type=tool

# Forced as TOOL (even if agent would classify as workflow)
# Generates: Atomic command structure
```

### Example 5: Custom Output Path
```bash
/create "test user authentication flow" --output-path=.claude/commands/test --dry-run

# Preview generation to custom path
# Review before moving to final location
```

---

## Expected Outcomes

### ✅ **Success: Component Generated**
```
✅ COMPONENT CREATED SUCCESSFULLY

**Classification**: Tool
**File**: .claude/commands/pr-check-deps.md
**Type**: Atomic utility command

**Generated Content:**
[Full Markdown file content]

**Usage Example:**
/pr-check-deps --filter="dependencies"

**Integration Test:**
[Test scaffold provided]

**Architectural Compliance:**
✅ Hub-and-spoke: No direct calls
✅ SOLID: Single responsibility
✅ DRY: No duplication found
✅ Markdown-first: Proper structure

**Recommendations:**
1. Test with: /pr-check-deps --dry-run
2. Update command inventory: docs/command-inventory.md
3. Consider adding to /help documentation

**Next Steps:**
- Review generated file
- Run dry-run test
- Integrate with existing workflows
```

### ⚠️ **Warning: Validation Issues**
```
⚠️ COMPONENT GENERATED WITH WARNINGS

**Classification**: Workflow
**File**: .claude/commands/complex-workflow.md
**Issue**: 12 steps detected (limit: 10)

**Recommendations:**
1. Split into 2 commands: Phase 1 & Phase 2
2. Consider creating agent for complex orchestration
3. Simplify by combining related steps

**Would you like to:**
- Regenerate with split approach?
- Convert to agent instead?
- Proceed with warnings documented?
```

### ❌ **Failure: Architectural Violation**
```
❌ COMPONENT GENERATION FAILED

**Issue**: Duplication detected
**Conflict**: Requested /pr-status duplicates /pr-process functionality

**Existing Command**: /pr-process (already checks PR status)

**Recommendations:**
1. Extend /pr-process with additional checks
2. Add specialized flag: /pr-process --status-only
3. If truly distinct, clarify unique value proposition

**Alternative Descriptions to Try:**
- "check PR status with advanced filtering"
- "analyze PR merge readiness and blockers"
- "monitor PR review progress and notifications"
```

---

## Integration Points

This command is used by:
- **Developers** - Manual component creation (`/create "description"`)
- **Orchestrator** - Pre-flight scaffolding consultation
- **Refactoring Workflows** - Create replacement commands during restructuring

**AgentCreatorAgent can also be consulted directly:**
- Before major feature additions (validate approach)
- During architectural refactoring (scaffold replacements)
- For bulk command generation (CI automation)

---

## Relationship to AgentCreatorAgent

```
User: /create "check PRs for dependency updates" --dry-run
          ↓
This Command (entrypoint)
          ↓
/orchestrator (routing)
          ↓
AgentCreatorAgent (intelligence)
          ↓
Scaffolded Component + Validation
```

**Division of Responsibility:**
- **This Command:** Argument parsing, user-facing interface
- **AgentCreatorAgent:** Classification, scaffolding, validation, recommendations
- **Orchestrator:** Routing and session management

---

## Validation Checks (Performed by Agent)

AgentCreatorAgent validates:

1. **Classification Accuracy**
   - Description matches selected type
   - Complexity appropriate for classification

2. **Architectural Compliance**
   - No direct command-to-command calls
   - Hub-and-spoke pattern followed
   - Separation of concerns maintained

3. **SOLID Principles**
   - Single responsibility (focused purpose)
   - No overlapping functionality

4. **DRY Principles**
   - No duplication of existing commands
   - Reuses shared logic where possible

5. **Structural Requirements**
   - ≤10 steps for workflows
   - Proper Markdown structure
   - YAML frontmatter for agents
   - Clear scope boundaries

6. **Documentation Completeness**
   - Arguments documented
   - Success criteria defined
   - Usage examples provided
   - Integration notes included

---

## Related Commands & Agents

**Commands:**
- `/system-review` - Validates overall system health (can check new component)
- `/architect` - Reviews architectural compliance (complementary validation)
- `/test-command-architecture` - Tests command system structure

**Agents:**
- `AgentCreatorAgent` - The intelligence behind this command
- `OrchestratorAgent` - Routes creation requests
- `SystemValidatorAgent` - Validates new components in system context

---

## Safety

- ⚠️ **Dry-Run First**: Always preview before creating files in production directories
- ✅ **Read-Only Classification**: Agent analyzes but doesn't modify existing code
- ✅ **Validation Before Creation**: All architectural checks pass before file generation
- ✅ **Rollback Friendly**: Generated files are new additions (easy to delete if needed)

---

## Success Criteria

- [x] Simple entrypoint that delegates to agent
- [x] Clear argument parsing
- [x] Proper orchestrator delegation
- [x] Returns formatted scaffolding output
- [x] No embedded scaffolding logic (lives in agent)
- [x] Follows hub-and-spoke pattern
- [x] Dry-run support for preview

---

## Tips for Effective Use

### **Writing Good Descriptions**

✅ **Good Examples:**
```
"check open PRs for dependency updates matching pattern"
"validate match algorithm follows business rules"
"orchestrate user onboarding workflow with email and profile setup"
```

❌ **Poor Examples:**
```
"do something with PRs"  // Too vague
"check validate analyze test everything"  // Unclear scope
"make new command"  // No context
```

### **Choosing the Right Type**

**Let the agent decide** (recommended):
- Agent has classification framework
- Considers complexity, stateful needs, multi-delegation
- Uses TribeVibe architectural patterns

**Force type only when**:
- You have specific requirements
- Testing scaffold templates
- Agent classification needs correction

### **Iterating on Descriptions**

If classification seems wrong:
1. Use `--dry-run` to preview
2. Refine description wording
3. Emphasize key aspects (atomic vs multi-step vs stateful)
4. Try again

Example iteration:
```bash
# Attempt 1: Too vague
/create "work with PRs" --dry-run
# → Agent unsure, asks for clarification

# Attempt 2: Better scope
/create "analyze PR merge readiness with checks" --dry-run
# → Agent classifies as WORKFLOW (multi-step analysis)

# Attempt 3: Atomic focus
/create "check if PR has merge conflicts" --dry-run
# → Agent classifies as TOOL (atomic check)
```

---

## Notes

- **Entrypoint Pattern:** Command → Orchestrator → Agent (proper delegation)
- **User-Facing:** Direct invocation via `/create "description"`
- **Reusable:** Orchestrator can also consult AgentCreatorAgent directly
- **Separation:** UI (command) vs Intelligence (agent)
- **Dry-Run Friendly:** Safe experimentation before file creation

---

## Version History

- **v1.0** (2025-09-30): Initial implementation
  - Simple entrypoint delegating to AgentCreatorAgent
  - Argument parsing for description, dry-run, output-path, type
  - Hub-and-spoke delegation pattern
  - Follows system-review hybrid approach