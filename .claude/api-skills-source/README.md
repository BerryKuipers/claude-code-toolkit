# Custom API Skills

Reusable API Skills for development workflow automation. These skills run in Claude's secure code execution environment and are available across Claude.ai, Claude Code, and the Messages API.

**Note:** These skills are generic and can be used in any TypeScript/JavaScript project with standard tooling (npm, tsc, Vitest/Jest).

## Skills vs Filesystem Skills

### API Skills (This Directory)
- **Location:** Uploaded to Anthropic via API
- **Execution:** Run in Claude's secure Python sandbox
- **Use:** Available everywhere (API, Claude.ai, Claude Code)
- **Best for:** Deterministic validation, data processing, complex logic

### Filesystem Skills (`.claude/skills/`)
- **Location:** Git-committed in project
- **Execution:** Claude interprets markdown instructions
- **Use:** Claude Code only
- **Best for:** Workflow patterns, git operations, documentation

## Available API Skills

### Quick Reference Table

**Quality & Testing Skills:**

| Skill Name | Skill ID | Version | Purpose |
|-----------|----------|---------|---------|
| quality-gate | `skill_016qnPYM55EUfzTjTCeL4Zng` | 1761128221040182 | Comprehensive quality validation |
| validate-typescript | `skill_01TYxAPLSwWUAJvpiBgaDcfn` | 1761128219304907 | TypeScript type checking |
| validate-lint | `skill_0154reaLWo6CsYUmARtg9aCk` | 1761131108110890 | ESLint/Prettier validation |
| run-comprehensive-tests | `skill_01EfbHCDmLehZ9CNKxxRBMzZ` | 1761128220504389 | Test suite execution with coverage |
| validate-coverage-threshold | `skill_01KvzeoAq1YbafijP1RiJSJw` | 1761128219842138 | Coverage threshold validation |
| validate-build | `skill_01Ew1QtJeHnYdpwAXj2HhrNw` | 1761131108925564 | Production build validation |

**Security & Maintenance Skills:**

| Skill Name | Skill ID | Version | Purpose |
|-----------|----------|---------|---------|
| audit-dependencies | `skill_01JvZxokSnKZ7bLwLQMAvKo1` | 1761131110127629 | npm audit + outdated packages |
| validate-git-hygiene | `skill_019bRtByNMx2hjhtnL5uhowG` | 1761131109611029 | Git commit & branch validation |

**Total:** 8 API skills available

**Latest Update:** 2025-10-22 - Added 4 new skills (lint, build, dependencies, git-hygiene)

---

### quality-gate
**Status:** ✅ Uploaded
**Skill ID:** `skill_016qnPYM55EUfzTjTCeL4Zng`

**Description:** Comprehensive quality validation for TypeScript/JavaScript projects

**Checks:**
- TypeScript compilation (`tsc --noEmit`)
- Test execution with results parsing
- Coverage analysis with threshold validation
- Build validation (`npm run build`)
- Linting (`npm run lint`)

**Returns:** Structured JSON with pass/fail status and detailed results

**Use in Conductor:**
```python
# Conductor Phase 3: Quality Assurance
# Use API skill instead of filesystem skill
skill_result = use_skill("quality-gate", {
    "project_path": "/path/to/your/project",
    "coverage_threshold": 80
})

if skill_result["passed"]:
    # All checks passed, proceed to PR creation
else:
    # Quality gate failed, show detailed errors
    errors = skill_result["details"]
```

---

### validate-typescript
**Status:** ✅ Uploaded
**Skill ID:** `skill_01TYxAPLSwWUAJvpiBgaDcfn`

**Description:** Run TypeScript compiler type-checking (tsc --noEmit) to validate type safety

**Checks:**
- TypeScript compilation errors
- Error categorization (type/syntax/import)
- Affected files list

**Returns:** Structured JSON with error counts and affected files

**Example Output:**
```json
{
  "status": "success",
  "typescript": {
    "status": "passing",
    "errors": {
      "total": 0,
      "type": 0,
      "syntax": 0,
      "import": 0
    },
    "files": []
  },
  "canProceed": true
}
```

---

### run-comprehensive-tests
**Status:** ✅ Uploaded
**Skill ID:** `skill_01EfbHCDmLehZ9CNKxxRBMzZ`

**Description:** Execute comprehensive test suite with coverage reporting and failure analysis

**Checks:**
- Unit tests
- Integration tests
- Test coverage metrics
- Failure details

**Returns:** Structured JSON with test results and coverage

**Example Output:**
```json
{
  "status": "pass",
  "summary": {
    "total": 45,
    "passed": 45,
    "failed": 0,
    "coverage": 87.5,
    "duration": "12.3s"
  },
  "failures": [],
  "canProceed": true
}
```

---

### validate-coverage-threshold
**Status:** ✅ Uploaded
**Skill ID:** `skill_01KvzeoAq1YbafijP1RiJSJw`

**Description:** Validate test coverage meets minimum thresholds

**Checks:**
- Overall coverage percentage
- Statement coverage
- Branch coverage
- Function coverage
- Uncovered files

**Returns:** Structured JSON with coverage validation results

**Example Output:**
```json
{
  "status": "success",
  "coverage": {
    "overall": 87.5,
    "statements": 88.2,
    "branches": 84.1,
    "functions": 89.3
  },
  "thresholds": {
    "overall": 80,
    "statements": 80,
    "branches": 75,
    "functions": 80
  },
  "passed": true,
  "failures": [],
  "canProceed": true
}
```

## Setup

### 1. Add Your Anthropic API Key

**IMPORTANT:** Use `ANTHROPIC_SKILLS_API_KEY` (not `ANTHROPIC_API_KEY`) to avoid conflict with Claude Code's internal authentication.

Add to Claude Code web environment:
```bash
ANTHROPIC_SKILLS_API_KEY=your-api-key-here
```

Or export in terminal:
```bash
export ANTHROPIC_SKILLS_API_KEY=sk-ant-...
```

Get your API key from: https://console.anthropic.com/settings/keys

### 2. Install Dependencies

```bash
pip install requests
```

### 3. Upload Skills

```bash
cd .claude/api-skills-source
python upload-skills.py
```

**Expected output:**
```
🔑 Found ANTHROPIC_SKILLS_API_KEY
📁 Skills directory: /path/to/project/.claude/api-skills-source
🎯 Found 1 skill(s) to upload:
   - quality-gate

📤 Uploading skill: quality-gate
   Description: Comprehensive quality validation for TypeScript/JavaScript projects...
   Code size: 12847 bytes
✅ Successfully uploaded!
   Skill ID: skill_abc123...
   Version: 1.0.0

========================================
📊 Upload Summary
========================================
✅ Uploaded: 1
❌ Failed: 0

✅ Successfully uploaded skills:
   - quality-gate
     ID: skill_abc123...
     Version: 1.0.0
```

### 4. Verify Upload

List all your skills:
```bash
curl https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_SKILLS_API_KEY" \
  -H "anthropic-version: 2025-01-22"
```

## Updating Existing Skills

To update skills with bug fixes or improvements, use the `update-skills.py` script:

```bash
cd .claude/api-skills-source
python3 update-skills.py
```

This creates new versions of existing skills while keeping the same skill IDs. The script:
- Maps skill directory names to their IDs (in `SKILL_IDS` dict)
- Shows current versions before updating
- POSTs to `/v1/skills/{id}/versions` to create new versions
- Reports success with new version numbers

**Benefits:**
- ✅ Skill IDs stay the same (references don't break)
- ✅ New versions automatically become "latest"
- ✅ Can roll back to older versions if needed

**See `UPDATE_NOTES.md` for full version history and details.**

## Using API Skills

### In Messages API

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    tools=[
        {
            "type": "code_execution_20250825"
        },
        {
            "type": "skill",
            "skill_id": "skill_abc123...",  # Your uploaded skill ID
        }
    ],
    messages=[{
        "role": "user",
        "content": "Run quality gate on my TypeScript project"
    }]
)
```

### In Claude Code (Automatic)

Once uploaded, Claude Code automatically detects and uses API skills when relevant:

```
User: "Run quality checks on the project"
Claude: [Automatically uses quality-gate API skill]
        [Returns structured results]
```

### In Conductor Workflow

Update `.claude/agents/conductor.md` to reference API skill:

```markdown
**Phase 3: Quality Assurance**

Use `quality-gate` API skill:
- Runs all quality checks in parallel
- Returns structured JSON with results
- Faster and more reliable than filesystem skill

If all checks pass:
  → Proceed to Phase 4 (PR Creation)
Else:
  → Show detailed error report
  → Offer to fix issues
```

## Creating New API Skills

### 1. Create Skill Directory

```bash
mkdir .claude/api-skills-source/my-new-skill
cd .claude/api-skills-source/my-new-skill
```

### 2. Create skill.py

```python
#!/usr/bin/env python3
"""
My Custom Skill

Description of what this skill does.
"""

def my_skill_function(param1: str, param2: int = 10) -> dict:
    """
    Main entry point for the skill.

    Args:
        param1: Description
        param2: Description with default

    Returns:
        Dictionary with results
    """
    # Your logic here
    result = {"status": "success", "data": param1}
    return result


# Entry point for Claude Code Execution
if __name__ == "__main__":
    import sys
    import json

    # Parse arguments
    param1 = sys.argv[1] if len(sys.argv) > 1 else "default"
    param2 = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    # Run skill
    result = my_skill_function(param1, param2)

    # Output JSON
    print(json.dumps(result, indent=2))
```

### 3. Create skill-definition.json

```json
{
  "name": "my-new-skill",
  "description": "Short description of what this skill does (< 1024 chars)",
  "code_language": "python",
  "entry_point": "my_skill_function",
  "parameters": {
    "param1": {
      "type": "string",
      "description": "First parameter"
    },
    "param2": {
      "type": "integer",
      "description": "Second parameter",
      "default": 10
    }
  },
  "returns": {
    "type": "object",
    "description": "Result object with status and data"
  },
  "version": "1.0.0",
  "tags": ["custom", "quality", "validation"]
}
```

### 4. Upload

```bash
cd .claude/api-skills-source
python upload-skills.py
```

## Skill Versioning

Update skill version in `skill-definition.json`, then re-upload:

```json
{
  "version": "1.1.0"
}
```

Upload script creates new version automatically. Users can pin to specific version or use latest.

## Best Practices

### 1. Use API Skills For:
- ✅ Deterministic validation (TypeScript, tests, coverage)
- ✅ Data processing and parsing
- ✅ Complex calculations
- ✅ External API integration
- ✅ Anything that needs consistent, reliable results

### 2. Keep Filesystem Skills For:
- ✅ Workflow patterns and orchestration
- ✅ Git operations (create branch, commit, PR)
- ✅ Documentation and examples
- ✅ Quick edits (markdown easier than Python)

### 3. Code Quality:
- ✅ Include proper error handling
- ✅ Return structured JSON
- ✅ Add helpful print statements (visible during execution)
- ✅ Document parameters and returns
- ✅ Keep skills focused (single responsibility)

### 4. Testing:
- ✅ Test locally before upload:
  ```bash
  cd .claude/api-skills-source/quality-gate
  python skill.py /path/to/project 80
  ```

## Troubleshooting

### "ANTHROPIC_SKILLS_API_KEY environment variable not set"

Add API key:
```bash
export ANTHROPIC_SKILLS_API_KEY=sk-ant-...
```

Or add to Claude Code web environment settings.

### "Failed to upload skill: 401 Unauthorized"

API key is invalid. Get new key from: https://console.anthropic.com/settings/keys

### "Failed to upload skill: 400 Bad Request"

Check skill-definition.json format. Ensure:
- `name` is valid (lowercase, hyphens)
- `description` is < 1024 chars
- `code_language` is "python"
- Parameters are properly typed

### Skill not appearing in Claude Code

- Skills are loaded at Claude Code startup
- Restart Claude Code after upload
- Verify upload succeeded: `python upload-skills.py` shows skill ID

## Future Skills (Planned)

### github-integration
- Direct GitHub API calls (no gh CLI dependency)
- Better error handling
- Structured issue/PR data

### typescript-validator
- Advanced TypeScript error parsing
- Suggestions for fixes
- Integration with LSP

### coverage-analyzer
- Detailed coverage reports
- Identify untested code paths
- Coverage trends over time

### gemini-rate-limiter
- Actual rate limiting implementation
- Queue management
- Retry logic

## Resources

- [Anthropic Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- [Code Execution Tool](https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution-tool)
- [Skills API Guide](https://docs.claude.com/en/api/skills-guide)
- [Claude Console](https://console.anthropic.com)
