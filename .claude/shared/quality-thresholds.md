# Quality Thresholds Reference

Standard thresholds used across all toolkit agents for consistent quality assessment.

## Code Complexity

| Metric | Threshold | Severity |
|--------|-----------|----------|
| Function length | > 50 lines | Warning |
| Function length | > 100 lines | Critical |
| File length | > 500 lines | Warning |
| File length | > 800 lines | Critical |
| Nesting depth | > 3 levels | Warning |
| Nesting depth | > 4 levels | Critical |
| Cyclomatic complexity | > 10 | Warning |
| Cyclomatic complexity | > 15 | Critical |

## Test Coverage

| Level | Threshold | Status |
|-------|-----------|--------|
| Excellent | ≥ 90% | ✅ |
| Good | ≥ 80% | ✅ |
| Acceptable | ≥ 70% | ⚠️ |
| Poor | < 70% | ❌ |

**Target**: 80% minimum for all new code.

## Build & Type Safety

| Check | Requirement |
|-------|-------------|
| TypeScript strict | Enabled |
| No `any` types | Unless justified |
| No `@ts-ignore` | Unless documented |
| Build exits 0 | Required |
| No warnings | Recommended |

## Dependencies

| Metric | Threshold | Action |
|--------|-----------|--------|
| Critical vulnerabilities | 0 | Block deployment |
| High vulnerabilities | 0 | Fix before merge |
| Outdated (major) | Track | Plan upgrade |
| Unused dependencies | 0 | Remove |

## Performance

| Metric | Warning | Critical |
|--------|---------|----------|
| Bundle size increase | > 10% | > 25% |
| API response time | > 500ms | > 2000ms |
| N+1 query patterns | Any | - |
| Missing indexes | Detected | - |

## Code Review

| Finding Severity | Merge Allowed? |
|------------------|----------------|
| Critical | ❌ No |
| High | ❌ No |
| Medium | ⚠️ Conditional |
| Low | ✅ Yes |

## Diff Size Guidelines

| Operation | Expected Lines |
|-----------|----------------|
| Bug fix | 5-30 |
| Small feature | 50-150 |
| Medium feature | 150-500 |
| Large feature | 500+ (split recommended) |
| Refactor (single) | 10-50 |
| Build error fix | 5-20 |

## Usage in Agents

Reference these thresholds in agent prompts:

```markdown
See `.claude/shared/quality-thresholds.md` for standard thresholds.

Quick reference:
- Functions > 50 lines = complex
- Files > 800 lines = too large
- Nesting > 4 levels = too deep
- Coverage < 80% = insufficient
```

## Override via Project Rules

Projects can override these defaults in `.claude/rules/` or overlay configs:

```yaml
# .claude/overlays/project/config.yml
thresholds:
  test_coverage_min: 70  # Override default 80%
  max_file_size_lines: 600  # Override default 800
```
