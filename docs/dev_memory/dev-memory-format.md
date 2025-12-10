# Dev Memory Data Format

This document defines the JSONL-based data format for the developer memory system.

## Overview

The dev memory system uses **append-only JSONL files** to track development events and sessions across commits. This lightweight format is:

- **Human-readable:** Plain text JSON, one object per line
- **Append-only:** Never rewritten, only appended (git-friendly)
- **Simple:** No database, no indexes, just files
- **Portable:** Works across all platforms, easy to sync via git
- **Queryable:** Standard JSON tools (jq, grep, etc.) can parse

## File Structure

Each target repository (after sync) will have:

```
<repo>/
└── ai_memory/
    ├── events.jsonl           # Development events (commits, features, fixes)
    ├── sessions.jsonl         # Coding sessions
    ├── SESSION_BRIEFING.md    # Generated session briefing (optional)
    └── .gitkeep               # Ensures directory exists
```

### Important Rules

1. **JSONL format:** One valid JSON object per line, no trailing commas
2. **Append-only:** Never delete or modify existing lines
3. **No sorting assumption:** Lines may not be in chronological order
4. **Compact:** Minimize whitespace within JSON objects
5. **UTF-8 encoding:** All files must be UTF-8

## Event Format (`events.jsonl`)

Each line in `events.jsonl` represents a single development event.

### Schema

```typescript
interface DevEvent {
  // Required fields
  id: string;                    // Unique event ID: "evt-YYYYMMDD-NNN"
  timestamp: string;             // ISO 8601: "2025-12-10T21:13:00Z"
  repo: string;                  // Repository name (not full path)
  branch: string;                // Git branch name
  type: EventType;               // Event category
  title: string;                 // One-line summary (< 100 chars)
  summary: string;               // Detailed description (< 500 chars)

  // Optional fields
  commit_hash?: string;          // Git commit SHA (short form)
  related_issues?: string[];     // GitHub issue IDs: ["#352", "#366"]
  related_prs?: string[];        // GitHub PR IDs: ["#374"]
  epic_id?: string;              // Epic identifier: "epic-context-pipeline-v2"
  open_questions?: string[];     // Unresolved questions
  next_steps?: string[];         // Action items
  parent_event_ids?: string[];   // Chain of related events
  tags?: string[];               // Free-form tags for categorization
  files_changed?: number;        // Count of files modified
  confidence?: 'high' | 'medium' | 'low';  // Confidence in extracted info
}

type EventType =
  | 'feature_implemented'
  | 'bug_fixed'
  | 'refactor'
  | 'decision'
  | 'test_added'
  | 'docs_updated'
  | 'dependency_updated'
  | 'breaking_change';
```

### Event Types

| Type | Use For | Example |
|------|---------|---------|
| `feature_implemented` | New functionality added | "Add dark mode toggle to settings" |
| `bug_fixed` | Bug resolution | "Fix race condition in auth middleware" |
| `refactor` | Code restructuring without feature changes | "Extract user service layer from routes" |
| `decision` | Architectural or design decision | "Chose Prisma over TypeORM for ORM" |
| `test_added` | Test coverage improvements | "Add E2E tests for checkout flow" |
| `docs_updated` | Documentation changes | "Update API docs for v2 endpoints" |
| `dependency_updated` | Package/library changes | "Upgrade Next.js to 14.0.3" |
| `breaking_change` | API or behavior changes requiring migration | "Change user auth API to require 2FA" |

### Example Events

#### Feature Implementation
```json
{"id":"evt-20251210-001","timestamp":"2025-12-10T21:13:00Z","repo":"WescoBar-Universe-Storyteller","branch":"feature/context-pipeline-v2","type":"feature_implemented","title":"Context pipeline Phase 3 – prompt routing per use case","summary":"Implemented context slice routing per use case with config-driven providers. Supports fallback provider selection and multi-provider ranking.","commit_hash":"a3b2c1d","related_issues":["#352","#366"],"related_prs":["#374"],"epic_id":"epic-context-pipeline-v2","open_questions":["Refine scoring heuristics for multi-provider ranking?"],"next_steps":["Add tests for fallback provider selection","Wire into video prompt pipeline later"],"tags":["backend","architecture"],"files_changed":12,"confidence":"high"}
```

#### Bug Fix
```json
{"id":"evt-20251210-002","timestamp":"2025-12-10T22:05:00Z","repo":"WescoBar-Universe-Storyteller","branch":"bugfix/issue-305","type":"bug_fixed","title":"Fix memory leak in context compaction","summary":"Compaction was holding references to old context slices. Added explicit cleanup and WeakMap for cache. Reduced memory usage by ~40% under heavy load.","commit_hash":"e4f5g6h","related_issues":["#305"],"tags":["performance","bugfix"],"files_changed":3,"confidence":"high"}
```

#### Decision
```json
{"id":"evt-20251208-003","timestamp":"2025-12-08T14:30:00Z","repo":"claude-code-toolkit","branch":"main","type":"decision","title":"Chose JSONL format for dev memory","summary":"Selected append-only JSONL over SQLite for dev memory storage. Reasons: (1) Git-friendly plain text, (2) No schema migrations needed, (3) Simple tooling (jq, grep), (4) Cross-platform. Trade-off: No indexes, but memory files expected to stay small (<1MB).","tags":["architecture","decision","dev-memory"],"open_questions":["Monitor file size growth - add rotation if >10MB?"],"confidence":"high"}
```

#### Refactor
```json
{"id":"evt-20251209-004","timestamp":"2025-12-09T16:45:00Z","repo":"TribeVibe","branch":"refactor/extract-repository-layer","type":"refactor","title":"Extract repository layer from services","summary":"Moved all Prisma queries from UserService to UserRepository. Services now depend on repository interfaces instead of direct DB access. Follows clean architecture principles from .claude/rules/03-backend-persistence.mdc","commit_hash":"i7j8k9l","tags":["refactoring","clean-architecture"],"files_changed":18,"next_steps":["Add repository layer for Products and Orders"],"confidence":"high"}
```

### Field Guidelines

**ID Format:**
- `evt-YYYYMMDD-NNN` where NNN is incremented per day
- Example: `evt-20251210-001`, `evt-20251210-002`
- Use UTC date for timestamp

**Timestamp:**
- ISO 8601 format with UTC timezone
- Example: `2025-12-10T21:13:00Z`
- Extract from git commit timestamp when possible

**Repo:**
- Repository name only, not full path
- Example: `WescoBar-Universe-Storyteller` not `/home/user/WescoBar-Universe-Storyteller`

**Branch:**
- Git branch name as-is
- Example: `feature/context-pipeline-v2`

**Title:**
- One-line summary, under 100 characters
- Should be scannable in timeline views
- Use action verbs: "Add", "Fix", "Refactor", "Update"

**Summary:**
- Detailed description, under 500 characters
- Explain what changed and why
- Include technical details
- Mention key decisions or trade-offs

**Related Issues/PRs:**
- Array of strings with `#` prefix
- Example: `["#352", "#366"]`
- Extract from commit message when present

**Open Questions:**
- Array of strings, each < 150 characters
- Use when uncertainty remains
- Example: `["Should we cache this per-user or globally?"]`

**Next Steps:**
- Array of action items
- Example: `["Add E2E tests", "Update documentation"]`

**Tags:**
- Free-form categorization
- Useful for filtering: `backend`, `frontend`, `performance`, `security`

**Confidence:**
- `high`: Extracted from explicit commit message or diff
- `medium`: Inferred from commit message keywords
- `low`: Guessed from file paths/changes

## Session Format (`sessions.jsonl`)

Each line represents a coding session (group of related commits).

### Schema

```typescript
interface DevSession {
  // Required fields
  id: string;                    // Unique session ID: "sess-YYYYMMDD-HHMMSS"
  timestamp_start: string;       // ISO 8601 start time
  timestamp_end: string;         // ISO 8601 end time
  repo: string;                  // Repository name
  branch: string;                // Primary branch worked on
  agent: string;                 // "Claude Code", "Manual", etc.
  summary: string;               // Session summary (< 500 chars)

  // Optional fields
  created_events: string[];      // Event IDs created in this session
  commits?: string[];            // Commit hashes (short form)
  epic_id?: string;              // Epic this session contributed to
  notes?: string[];              // Freeform notes
  stats?: {                      // Session statistics
    files_changed?: number;
    lines_added?: number;
    lines_removed?: number;
    commits_count?: number;
  };
  tags?: string[];               // Session categorization
}
```

### Example Sessions

#### Feature Implementation Session
```json
{"id":"sess-20251210-200500","timestamp_start":"2025-12-10T20:05:00Z","timestamp_end":"2025-12-10T22:15:00Z","repo":"WescoBar-Universe-Storyteller","branch":"feature/context-pipeline-v2","agent":"Claude Code","summary":"Phase 4 of the context pipeline finished. Closed #352 and #305. Implemented provider routing and fixed memory leak. Left TODO: scoring heuristics + UI wiring.","created_events":["evt-20251210-001","evt-20251210-002"],"commits":["a3b2c1d","e4f5g6h"],"epic_id":"epic-context-pipeline-v2","notes":["Compaction behavior still feels aggressive under heavy logs","Need to revisit provider scoring algorithm"],"stats":{"files_changed":15,"commits_count":2},"tags":["feature","bugfix"]}
```

#### Refactoring Session
```json
{"id":"sess-20251209-164500","timestamp_start":"2025-12-09T16:45:00Z","timestamp_end":"2025-12-09T18:30:00Z","repo":"TribeVibe","branch":"refactor/extract-repository-layer","agent":"Claude Code","summary":"Extracted repository layer from services following clean architecture rules. Moved all Prisma queries to dedicated repositories. Services now depend on interfaces.","created_events":["evt-20251209-004"],"commits":["i7j8k9l"],"notes":["Next: add repository layer for Products and Orders","Consider adding integration tests for repositories"],"stats":{"files_changed":18,"commits_count":1},"tags":["refactoring","architecture"]}
```

### Field Guidelines

**ID Format:**
- `sess-YYYYMMDD-HHMMSS` using session start time
- Example: `sess-20251210-200500`

**Timestamps:**
- Start: When session began (first commit or earlier)
- End: When session ended (last commit or explicit end)
- Both in ISO 8601 UTC format

**Agent:**
- `Claude Code` when assisted by Claude
- `Manual` when developer worked alone
- Can be other tools: `GitHub Copilot`, `Cursor`, etc.

**Summary:**
- High-level overview of session accomplishments
- Mention closed issues/PRs
- Note incomplete work or follow-ups

**Created Events:**
- Array of event IDs generated during session
- Links session to detailed events

**Notes:**
- Free-form observations
- Technical debt identified
- Ideas for future work

## File Management

### Appending Events

```bash
# Append a new event
echo '{"id":"evt-20251210-001","timestamp":"2025-12-10T21:13:00Z",...}' >> ai_memory/events.jsonl
```

### Reading Events

```bash
# Read all events
cat ai_memory/events.jsonl

# Parse with jq
cat ai_memory/events.jsonl | jq -r '.title'

# Filter by type
cat ai_memory/events.jsonl | jq 'select(.type == "feature_implemented")'

# Get recent events (last 10 lines)
tail -n 10 ai_memory/events.jsonl

# Sort by timestamp (requires loading into memory)
cat ai_memory/events.jsonl | jq -s 'sort_by(.timestamp) | .[]'
```

### File Size Management

**Expected growth:**
- ~500 bytes per event (with all optional fields)
- ~100 commits/month ≈ 50KB/month
- ~600KB/year per repo

**Rotation strategy (if needed):**
- When file exceeds 10MB, consider rotation
- Archive to `events-YYYY.jsonl.gz`
- Keep recent year uncompressed

**NOT implemented initially** - monitor and add if needed

## Validation

### Event Validation Rules

1. `id` must match pattern `evt-YYYYMMDD-\d{3}`
2. `timestamp` must be valid ISO 8601
3. `type` must be one of defined EventType values
4. `title` must be 1-100 characters
5. `summary` must be 1-500 characters
6. `related_issues` and `related_prs` must have `#` prefix
7. All string arrays must contain non-empty strings

### Session Validation Rules

1. `id` must match pattern `sess-YYYYMMDD-HHMMSS`
2. `timestamp_end` must be >= `timestamp_start`
3. `created_events` must reference valid event IDs
4. `commits` must be valid git SHA format (if present)

### Parsing Safety

When reading JSONL files:
1. Parse each line independently (don't load entire file as JSON array)
2. Skip malformed lines with warning (don't crash)
3. Validate required fields before processing
4. Handle missing optional fields gracefully

## Best Practices

### For Writers (dev_memory_update skill)

1. **Extract from commit data:** Use commit message, diff, branch name
2. **Infer type conservatively:** If unsure, use `feature_implemented`
3. **Limit per commit:** Max 3 events per commit (typically 1)
4. **Add confidence level:** Be transparent about inference quality
5. **Link issues/PRs:** Extract from commit message patterns
6. **Set timestamps from git:** Use commit author date, not current time
7. **Keep summaries concise:** Under 500 chars, focus on "why" not just "what"

### For Readers (dev_memory_briefing skill)

1. **Sort by timestamp:** JSONL files aren't guaranteed sorted
2. **Filter by repo/branch:** Focus on relevant events
3. **Group by epic_id:** Show related events together
4. **Limit results:** Default to last 20 events, make configurable
5. **Handle missing files:** Gracefully create empty briefing if no events exist
6. **Parse safely:** Skip malformed lines, log warnings

### For Projects Using Dev Memory

1. **Commit JSONL files:** Track memory in git for history
2. **Review periodically:** Ensure quality of extracted events
3. **Adjust thresholds:** Tune maxEventsPerCommit in config
4. **Add manual events:** Developers can append events manually for decisions
5. **Archive old data:** Compress events older than 1 year if file grows large

## Migration & Compatibility

### V1 Format (Current)

This is the initial format. No migrations needed.

### Future Versions

If schema changes:
1. Add version field: `"schema_version": "1.0"`
2. Write migration script to add version to existing events
3. Support reading multiple versions
4. Clearly document breaking changes

### Backward Compatibility

When adding new fields:
- Always optional
- Readers must handle missing fields
- Never change meaning of existing required fields
