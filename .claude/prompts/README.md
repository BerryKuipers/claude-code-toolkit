# Claude Code Toolkit - Prompts Directory

**Central repository of reusable prompts for workflows, coordination, analysis, and templates.**

## Overview

This directory contains structured prompts that can be reused across all repositories using the toolkit. Prompts are organized by category and designed to work with agents, commands, and workflows.

## Directory Structure

```
.claude/prompts/
├── workflows/          # End-to-end workflow prompts
│   ├── issue-selection.md
│   ├── pr-review-response.md
│   └── ...
├── coordination/       # Agent coordination prompts
│   ├── parallel-agents.md
│   └── ...
├── analysis/          # Analysis and investigation prompts
│   └── ...
├── templates/         # Reusable templates
│   └── ...
└── README.md          # This file
```

## Available Prompts

### Workflows

#### issue-selection.md
**Purpose:** Intelligently select the best next GitHub issue to work on

**Use when:**
- Starting a new task
- Prioritizing backlog
- Using conductor agent to pick work

**Key features:**
- Multi-factor scoring (impact, effort, dependencies, context)
- Weighted priority calculation
- Clear decision framework
- Integration with conductor workflows

**Usage:**
```markdown
"I need to select the best next GitHub issue to work on.

Repository: my-repo
Current sprint: Sprint 23

Available issues:
[paste gh issue list output]

Please analyze and recommend the best issue using the issue-selection prompt."
```

#### pr-review-response.md
**Purpose:** Check PRs and respond to review comments (including AI reviewers like Gemini)

**Use when:**
- After creating a PR
- Receiving review comments
- Need to address feedback

**Key features:**
- Systematic comment analysis
- Priority categorization
- Action planning with TodoWrite
- Response templates
- False positive handling

**Usage:**
```markdown
"Check my PR #45 in owner/repo and analyze all review comments including Gemini feedback.

Use the pr-review-response prompt to:
1. Analyze each comment
2. Recommend actions
3. Draft responses
4. Create action plan"
```

### Coordination

#### parallel-agents.md
**Purpose:** Coordinate multiple agents running in parallel

**Use when:**
- Tasks can be decomposed into independent subtasks
- Need to maximize execution speed
- Coordinating multi-agent workflows

**Key features:**
- Dependency analysis
- Parallel execution patterns (fork-join, pipeline, broadcast, race)
- Coordination templates
- Conflict resolution strategies
- Time savings calculation

**Usage:**
```markdown
"I need to implement a feature across frontend, backend, and database.

Use the parallel-agents coordination prompt to:
1. Analyze dependencies
2. Identify parallelizable work
3. Create execution plan
4. Launch agents in parallel"
```

## How to Use Prompts

### Method 1: Reference by Name

Simply reference the prompt in your request:

```markdown
"Use the issue-selection prompt to help me choose the next GitHub issue"
```

The agent will read the prompt file and apply its framework.

### Method 2: Include Context

Provide specific context with the prompt reference:

```markdown
"Using the pr-review-response prompt, analyze PR #42 in my-repo.

Additional context:
- This is a critical bug fix
- Reviewer is concerned about performance
- Need to respond today"
```

### Method 3: Copy Template Sections

Copy specific sections from prompts into your requests:

```markdown
"Analyze these GitHub issues using this scoring framework:
[paste relevant section from issue-selection.md]

Issues to analyze:
- Issue #1: ...
- Issue #2: ..."
```

### Method 4: Integration with Agents

Agents can automatically use prompts in their workflows:

```markdown
# In conductor agent

Step 1: Select issue
- Load .claude/prompts/workflows/issue-selection.md
- Apply framework to open issues
- Get top recommendation

Step 2: Coordinate implementation
- Load .claude/prompts/coordination/parallel-agents.md
- Decompose into subtasks
- Launch parallel agents
```

## Creating New Prompts

### Prompt Structure

```markdown
# [Prompt Name]

**Purpose**: [One-line description]

## Overview
[High-level explanation]

## [Main Section 1]
[Content]

## [Main Section 2]
[Content]

## Prompt Template
[Actual prompt text to use]

## Example
[Concrete example showing usage]

## Integration
[How this prompt works with agents/commands]

## Notes
[Important considerations]
```

### Prompt Categories

**Workflows:** Complete end-to-end processes
- Issue selection
- PR review response
- Feature implementation
- Bug investigation
- Deployment workflows

**Coordination:** Multi-agent orchestration
- Parallel agent patterns
- Sequential workflows
- Resource conflict resolution
- Failure handling

**Analysis:** Investigation and evaluation
- Code quality analysis
- Performance profiling
- Security assessment
- Architecture review

**Templates:** Reusable structures
- Commit messages
- PR descriptions
- Issue templates
- Documentation outlines

### Contributing New Prompts

1. **Identify need** - What problem does this solve?
2. **Draft prompt** - Follow structure template
3. **Test prompt** - Use in real workflows
4. **Document usage** - Add examples
5. **Add to README** - Update this file

## Prompt Best Practices

### DO:
✅ Make prompts reusable across repos
✅ Include concrete examples
✅ Provide templates/frameworks
✅ Document integration points
✅ Keep prompts focused on one task
✅ Update prompts based on usage

### DON'T:
❌ Make prompts repo-specific
❌ Include hardcoded values
❌ Create overlapping prompts
❌ Write prompts without examples
❌ Let prompts become outdated

## Prompt Maintenance

### Regular Reviews
- Monthly: Review usage and effectiveness
- Quarterly: Update based on feedback
- Yearly: Archive unused prompts

### Version Control
- Prompts are versioned with toolkit
- Changes tracked in git
- Breaking changes documented

### Feedback Loop
- Collect feedback from usage
- Identify improvement opportunities
- Iterate on prompt quality

## Common Use Cases

### Starting New Work
1. Use **issue-selection.md** to pick issue
2. Use **parallel-agents.md** to coordinate implementation
3. Create PR
4. Use **pr-review-response.md** to address feedback

### Code Review
1. Review PR with code-reviewer agent
2. Use **pr-review-response.md** to respond to comments
3. Address feedback
4. Re-request review

### Multi-Repo Operations
1. Use **parallel-agents.md** broadcast pattern
2. Coordinate operations across repos
3. Aggregate results

### Complex Features
1. Use **parallel-agents.md** to decompose
2. Fork-join pattern for parallel work
3. Pipeline pattern for staged work
4. Aggregate and integrate

## Integration with Conductor

The conductor agent is designed to use these prompts automatically:

```markdown
# Conductor workflow

1. Issue Selection (uses issue-selection.md)
   - Fetch open issues
   - Apply scoring framework
   - Select best issue

2. Task Decomposition (uses parallel-agents.md)
   - Break into subtasks
   - Analyze dependencies
   - Plan parallel execution

3. Implementation
   - Launch agents in parallel
   - Monitor progress
   - Handle failures

4. PR Creation
   - Create PR with generated description
   - Request reviews

5. PR Response (uses pr-review-response.md)
   - Monitor for comments
   - Analyze feedback
   - Address issues
   - Respond to reviewers

6. Merge and Close
   - Verify checks pass
   - Merge PR
   - Close issue
```

## Advanced Patterns

### Prompt Composition

Combine multiple prompts for complex workflows:

```markdown
"I need to:
1. Select the best issue (issue-selection prompt)
2. Implement in parallel (parallel-agents prompt)
3. Address PR feedback (pr-review-response prompt)

Please coordinate this end-to-end workflow."
```

### Conditional Prompt Usage

Use prompts based on context:

```markdown
"If issue has multiple independent subtasks:
  Use parallel-agents coordination prompt
Else:
  Use sequential implementation"
```

### Prompt Customization

Adapt prompts to project needs:

```markdown
"Use issue-selection prompt but adjust weights:
- Impact: 50% (we prioritize impact over speed)
- Effort: 20%
- Dependencies: 20%
- Context: 10%"
```

## Syncing Prompts

Prompts are automatically synced from toolkit to projects:

```bash
# Synced by SessionStart hook
git submodule update --init --remote .claude-toolkit
bash .claude-toolkit/scripts/sync-claude-toolkit.sh

# Prompts copied to:
.claude/prompts/  (from .claude-toolkit/.claude/prompts/)
```

**Note:** Prompts are synced (not excluded in .gitignore) so they're available in every project.

## Troubleshooting

### Prompt Not Found
- Check if prompts directory exists: `ls .claude/prompts/`
- Run sync script: `./scripts/sync-claude-toolkit.sh`
- Verify submodule: `git submodule status`

### Outdated Prompts
- Update toolkit: `cd .claude-toolkit && git pull`
- Re-sync: `./scripts/sync-claude-toolkit.sh`

### Prompt Not Working
- Verify prompt syntax (Markdown)
- Check examples in prompt file
- Test with simple case first
- Provide more context

## Examples

### Example 1: Issue Selection

```bash
# Fetch issues
gh issue list --repo my-repo --state open --limit 20 --json number,title,labels,body

# Request analysis
"Use the issue-selection prompt to analyze these issues and recommend the best one to work on next.

Repository: my-repo
Team focus: Performance improvements
Available time: 4 hours

Issues:
[paste output]"
```

### Example 2: Parallel Implementation

```markdown
"I need to add authentication to the app.

Use parallel-agents coordination prompt to:
1. Implement JWT middleware (backend)
2. Create login form (frontend)
3. Add users table (database)

These are independent and can run in parallel."
```

### Example 3: PR Review Response

```bash
# After PR created and reviewed
"Check PR #45 in my-repo and use pr-review-response prompt to:
1. Fetch all comments (including Gemini reviews)
2. Analyze and prioritize
3. Create action plan with TodoWrite
4. Draft responses for each comment"
```

## Future Prompts

**Planned additions:**
- Bug investigation workflows
- Performance optimization prompts
- Security audit frameworks
- Documentation generation
- Deployment coordination
- Rollback procedures
- Incident response
- Technical debt assessment

## Contributing

To contribute new prompts:

1. Create prompt file in appropriate directory
2. Follow structure template
3. Add usage examples
4. Update this README
5. Test in real workflows
6. Submit PR to toolkit repo

## Support

For prompt-related questions:
- Check examples in prompt files
- Review this README
- Test with small examples
- Ask for clarification in requests

## Notes

- Prompts are toolkit content (synced, not git-ignored)
- Prompts work across all repos using toolkit
- Regular updates improve prompt quality
- Feedback drives prompt evolution
- Prompts enable consistent workflows
