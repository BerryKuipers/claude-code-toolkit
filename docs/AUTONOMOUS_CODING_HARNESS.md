# Autonomous Coding Harness

The autonomous-coding harness enables structured, feature-driven coding sessions where Claude works through a defined set of features systematically.

## Overview

Based on [Anthropic's autonomous-coding quickstart pattern](https://github.com/anthropics/anthropic-quickstarts), this harness provides:

- **Feature List** (`feature_list.json`) - Defines features to implement
- **Progress Tracking** (`claude-progress.txt`) - Logs session activity
- **App Specification** (`app_spec.txt`) - Describes the project for context
- **Session Hooks** - Auto-update progress on session start/stop

## Quick Start

### 1. Initialize the Harness

```bash
# From your project root
bash .claude-toolkit/templates/harness/init.sh
```

This creates `.claude/harness/` with template files.

### 2. Configure Your Feature List

Edit `.claude/harness/feature_list.json`:

```json
{
  "project": {
    "name": "My Project",
    "description": "What this project does"
  },
  "features": [
    {
      "id": "auth-001",
      "name": "User Authentication",
      "description": "Implement login/logout with JWT tokens",
      "status": "pending",
      "priority": "critical",
      "dependencies": [],
      "acceptance_criteria": [
        "Users can register with email/password",
        "Users can login and receive JWT",
        "Protected routes require valid token"
      ],
      "files_affected": [
        "src/auth/",
        "src/middleware/auth.ts"
      ]
    }
  ],
  "metadata": {
    "version": "1.0.0",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "total_features": 1,
    "completed_features": 0
  }
}
```

### 3. Describe Your Application

Edit `.claude/harness/app_spec.txt` to describe:

- Project architecture
- Coding conventions
- Constraints and rules
- Important context files

### 4. Enable Harness Hooks

Copy the harness settings or merge with your existing settings:

```bash
cp .claude-toolkit/templates/harness/settings-harness.json .claude/settings.json
```

Or add the harness hooks to your existing settings.json.

### 5. Start a Session

```bash
claude
```

Claude will automatically:
1. Read the feature list on session start
2. Log progress to `claude-progress.txt`
3. Update feature statuses as work progresses

## Feature Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Done and verified |
| `blocked` | Waiting on dependencies or issues |
| `deferred` | Postponed for later |

## Files Reference

### feature_list.json

The main feature tracking file. Features should have:

- **id**: Unique identifier (e.g., `auth-001`)
- **name**: Short descriptive name
- **description**: Detailed requirements
- **status**: Current state
- **priority**: `critical`, `high`, `medium`, `low`
- **dependencies**: Array of feature IDs this depends on
- **acceptance_criteria**: What must be true when complete
- **files_affected**: Expected files to modify

### claude-progress.txt

Auto-updated session log. Contains:

- Session start/end timestamps
- Current feature being worked on
- Progress statistics
- Activity log entries

### app_spec.txt

Static project description including:

- Technology stack
- Architecture overview
- Coding conventions
- Project constraints

## Integration with Memory System

The harness integrates with the dev-memory system:

1. **SessionStart**: Processes pending memory updates, logs session start
2. **Stop**: Saves progress, processes memory updates

Both systems work together to maintain context across sessions.

## Best Practices

### Feature Granularity

Break large features into smaller, manageable units:

```json
// Good - specific and measurable
{
  "id": "auth-001",
  "name": "JWT Token Generation",
  "acceptance_criteria": [
    "Generate valid JWT on login",
    "Include user ID and role in payload",
    "Token expires in 24 hours"
  ]
}

// Bad - too vague
{
  "id": "auth",
  "name": "Authentication",
  "acceptance_criteria": ["Users can authenticate"]
}
```

### Dependencies

Use dependencies to ensure proper order:

```json
{
  "features": [
    {
      "id": "db-setup",
      "name": "Database Schema",
      "dependencies": []
    },
    {
      "id": "user-model",
      "name": "User Model",
      "dependencies": ["db-setup"]
    },
    {
      "id": "auth",
      "name": "Authentication",
      "dependencies": ["user-model"]
    }
  ]
}
```

### Progress Commits

For long sessions, Claude can commit progress:

```bash
# After completing a feature
git add .
git commit -m "feat: Complete feature auth-001 - JWT Token Generation"
```

## Troubleshooting

### Harness not initializing

Check that the harness directory exists:

```bash
ls -la .claude/harness/
```

If missing, run `init.sh` again.

### Progress not updating

Ensure hooks are properly configured in `.claude/settings.json` and use the `bash -c "..."` wrapper for Windows compatibility.

### Feature list not loading

Validate JSON syntax:

```bash
jq . .claude/harness/feature_list.json
```

## Related Documentation

- [Memory System](./dev_memory/README.md) - Session memory persistence
- [Hooks System](../templates/settings-with-hooks.json) - Claude Code hooks
- [Anthropic Quickstart](https://github.com/anthropics/anthropic-quickstarts) - Original pattern
