# Start Full Workflow Command

Complete feature development workflow using conductor agent for issue-to-PR automation.

## Instructions

**Issue to work on:** $ARGUMENTS (if no arguments, conductor will auto-select)

This command delegates the ENTIRE workflow to the conductor agent, which will:
1. **Phase 1**: Select issue and validate architecture (architect agent)
2. **Phase 2**: Implement feature (design agent + implementation agent)
3. **Phase 3**: Quality assurance (audit agent + refactor agent if needed)
4. **Phase 4**: Create pull request
5. **Phase 5**: Gemini review and apply suggestions
6. **Phase 6**: Final validation and report

## How It Works

The conductor agent will autonomously:
- Pick optimal issue from backlog (or use specified issue)
- Create feature branch
- Delegate to architect agent for architecture validation
- Delegate to design agent for UI/UX changes
- Delegate to implementation agent for feature development
- Run comprehensive quality gates (tests, build, audit)
- Delegate to refactor agent if quality < 8.0
- Create PR with proper issue linking
- Request Gemini review
- Apply Gemini suggestions
- Generate final workflow report

## Usage Examples

```bash
# Auto-select best issue and run full workflow
/start-workflow

# Work on specific issue
/start-workflow issue=137

# Work on issue with priority override
/start-workflow issue=123 priority=critical

# Resume existing workflow
/start-workflow resume
```

## Delegation to Conductor

I need the conductor agent to run the complete feature development workflow.

Issue context: ${ARGUMENTS:-"Auto-select optimal issue from backlog"}

The conductor should:
- Show comprehensive todo list at start (all 6 phases + agents involved)
- Delegate to ALL appropriate specialized agents:
  - architect agent (architecture validation)
  - researcher agent (if research needed)
  - design agent (if UI/UX changes)
  - implementation agent (feature development)
  - audit agent (quality checks)
  - refactor agent (if quality < 8.0)
  - debugger agent (if tests fail)
- Create PR with proper "Fixes #ISSUE_NUMBER" format
- Work autonomously through all phases without stopping
- Only ask questions if genuinely blocked

Expected outcome: Complete implementation from issue analysis to merged PR, with all quality gates passing and proper agent delegation demonstrated.
