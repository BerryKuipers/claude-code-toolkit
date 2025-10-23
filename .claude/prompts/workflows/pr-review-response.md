# PR Review Response Prompt

**Purpose**: Check on created PRs and respond to review comments (including Gemini AI reviewer feedback).

## Overview

After creating a PR, it's common to receive automated reviews from AI reviewers (like Gemini) and human reviewers. This prompt helps systematically check PR status and address all review comments.

## Workflow Steps

### Step 1: Fetch PR Details

```bash
# Get PR information
gh pr view <PR_NUMBER> --json number,title,state,author,isDraft,mergeable,reviews,comments,url

# Get PR diff
gh pr diff <PR_NUMBER>

# Get all comments (including review comments on code)
gh pr view <PR_NUMBER> --comments

# Get review comments specifically
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments
```

### Step 2: Analyze Review Comments

**For each comment/review, identify:**

1. **Comment Source**
   - AI reviewer (Gemini, GitHub Copilot, etc.)
   - Human reviewer
   - CI/CD bot

2. **Comment Type**
   - Code quality issue
   - Bug/potential issue
   - Style/formatting
   - Security concern
   - Performance suggestion
   - Question/clarification
   - Nit/minor suggestion

3. **Priority**
   - Critical (blocking merge)
   - Important (should fix)
   - Nice-to-have (optional)
   - Informational (no action)

4. **Action Required**
   - Fix code
   - Add test
   - Update documentation
   - Respond with explanation
   - Disagree with reasoning
   - No action needed

### Step 3: Response Strategy

**For AI Reviewer Comments (e.g., Gemini):**

✅ **Legitimate issues** - Fix and acknowledge
```markdown
"Good catch! Fixed in <commit-sha>. Added test to prevent regression."
```

✅ **False positives** - Explain why it's not an issue
```markdown
"This is intentional because [reason]. The [pattern] is required for [use-case]."
```

✅ **Style preferences** - Evaluate and decide
```markdown
"Applied your suggestion for consistency with the codebase."
OR
"Keeping current style as it aligns with our style guide [link]."
```

❌ **Ignore blindly** - Always evaluate AI feedback

**For Human Reviewer Comments:**

✅ **Always respond** - Show you've considered feedback
✅ **Ask clarifying questions** - If unclear
✅ **Discuss trade-offs** - If you disagree
✅ **Thank reviewers** - Acknowledge their time

## Prompt Template

```markdown
I need to check on my PR and respond to review comments.

**PR Details:**
- Repository: {owner}/{repo}
- PR Number: #{pr_number}
- PR Title: {title}
- PR URL: {url}

**Request:**
1. Fetch the PR details and all comments (including Gemini AI review)
2. Analyze each comment:
   - Categorize (code quality/bug/style/security/performance)
   - Assess validity (legitimate/false positive/opinion)
   - Determine priority (critical/important/nice-to-have)
3. For each comment, recommend action:
   - Fix code (provide specific changes)
   - Respond with explanation (draft response)
   - No action needed (explain why)
4. Identify any blocking issues that prevent merge
5. Create action plan with TodoWrite

**Expected Output:**
- Summary of all review comments
- Analysis of each comment
- Action plan with priorities
- Code fixes needed
- Draft responses to comments
```

## Analysis Template

```markdown
# PR Review Analysis: #{PR_NUMBER} - {TITLE}

**PR Status:**
- State: {open/closed/merged}
- Mergeable: {yes/no/conflict}
- Draft: {yes/no}
- Checks: {passing/failing/pending}

## Review Comments Summary

**Total Comments:** X
- Gemini AI: X comments
- Human reviewers: X comments
- CI/CD: X comments

**By Priority:**
- Critical (blocking): X
- Important: X
- Nice-to-have: X
- Informational: X

## Detailed Comment Analysis

### Comment 1: {Commenter} on {file}:{line}

**Quote:**
> {comment text}

**Analysis:**
- Type: {code quality/bug/style/security/performance}
- Validity: {legitimate/false positive/debatable}
- Priority: {critical/important/nice-to-have/info}

**Recommended Action:**
- [ ] Fix code: {specific change}
- [ ] Add test: {test description}
- [ ] Update docs: {what to update}
- [ ] Respond: {draft response}
- [ ] No action: {reason}

**Code Fix (if applicable):**
```diff
- old code
+ new code
```

**Draft Response:**
"{response text}"

---

### Comment 2: {Commenter} on {file}:{line}

[... repeat for each comment ...]

## Blocking Issues

**Critical items preventing merge:**
1. {issue description} - {action needed}
2. {issue description} - {action needed}

## Action Plan

Use TodoWrite to track:
- [ ] Fix: {issue 1} (Priority: Critical)
- [ ] Fix: {issue 2} (Priority: Important)
- [ ] Respond to: {comment 1}
- [ ] Respond to: {comment 2}
- [ ] Update tests
- [ ] Push fixes and re-request review

## Next Steps

1. Implement fixes for critical issues
2. Push commit(s) addressing feedback
3. Respond to all comments
4. Re-request review from reviewers
5. Monitor for additional feedback
```

## Example Scenario: Gemini Review

```markdown
# PR Review Analysis: #45 - Add user preferences API

**PR Status:**
- State: open
- Mergeable: yes
- Draft: no
- Checks: passing

## Review Comments Summary

**Total Comments:** 5
- Gemini AI: 4 comments
- Human reviewers: 1 comment
- CI/CD: 0 comments

**By Priority:**
- Critical (blocking): 1
- Important: 2
- Nice-to-have: 2
- Informational: 0

## Detailed Comment Analysis

### Comment 1: Gemini-AI-Bot on src/api/preferences.ts:45

**Quote:**
> ⚠️ Potential SQL injection vulnerability: User input is directly interpolated into SQL query without parameterization.

**Analysis:**
- Type: Security
- Validity: Legitimate (critical issue)
- Priority: Critical (blocking merge)

**Recommended Action:**
- [x] Fix code: Use parameterized query instead of string interpolation
- [x] Add test: SQL injection test case
- [ ] Respond: Acknowledge and confirm fix

**Code Fix:**
```diff
- const query = `SELECT * FROM preferences WHERE user_id = '${userId}'`;
+ const query = 'SELECT * FROM preferences WHERE user_id = ?';
+ const results = await db.query(query, [userId]);
```

**Draft Response:**
"Excellent catch! This was a serious vulnerability. Fixed in abc123 using parameterized queries. Added test to verify SQL injection prevention."

---

### Comment 2: Gemini-AI-Bot on src/api/preferences.ts:67

**Quote:**
> 💡 Consider adding error handling for database connection failures.

**Analysis:**
- Type: Code quality
- Validity: Legitimate (good suggestion)
- Priority: Important

**Recommended Action:**
- [x] Fix code: Add try-catch with proper error response
- [ ] Respond: Thank and confirm added

**Code Fix:**
```diff
+ try {
    const result = await db.update('preferences', data);
    return res.json(result);
+ } catch (error) {
+   logger.error('Database error:', error);
+   return res.status(500).json({ error: 'Failed to update preferences' });
+ }
```

**Draft Response:**
"Good point! Added comprehensive error handling with logging."

---

### Comment 3: Gemini-AI-Bot on src/api/preferences.ts:23

**Quote:**
> 📝 Consider using TypeScript interface for preferences object instead of 'any' type.

**Analysis:**
- Type: Code quality
- Validity: Legitimate (type safety)
- Priority: Important

**Recommended Action:**
- [x] Fix code: Define PreferencesDto interface
- [ ] Respond: Acknowledge

**Code Fix:**
```typescript
interface PreferencesDto {
  theme: 'light' | 'dark';
  notifications: boolean;
  language: string;
}

function updatePreferences(data: PreferencesDto) {
  // now type-safe
}
```

**Draft Response:**
"Agreed, added PreferencesDto interface for type safety."

---

### Comment 4: Gemini-AI-Bot on tests/api/preferences.test.ts:12

**Quote:**
> ℹ️ Test coverage looks good. Consider adding edge case for invalid language codes.

**Analysis:**
- Type: Testing
- Validity: Good suggestion
- Priority: Nice-to-have

**Recommended Action:**
- [x] Add test: Invalid language code test case
- [ ] Respond: Thank and confirm

**Code Fix:**
```typescript
it('should reject invalid language codes', async () => {
  const response = await request(app)
    .put('/api/preferences')
    .send({ language: 'invalid-xx-XX' });

  expect(response.status).toBe(400);
  expect(response.body.error).toContain('Invalid language code');
});
```

**Draft Response:**
"Great suggestion! Added test for invalid language codes."

---

### Comment 5: john-reviewer on src/api/preferences.ts:34

**Quote:**
> Why are we storing language as a string instead of using an enum? Would be more type-safe.

**Analysis:**
- Type: Design question
- Validity: Valid concern, but current approach has reasons
- Priority: Nice-to-have

**Recommended Action:**
- [ ] Fix code: Not fixing (explain reasoning)
- [x] Respond: Explain rationale with context

**Draft Response:**
"Good question! We're storing as string to support dynamic language packs that can be added without code changes. The validation happens in the language service layer where we check against available locales. If we used an enum, we'd need to redeploy every time we add a language. Open to discussion if you feel strongly about this!"

---

## Blocking Issues

**Critical items preventing merge:**
1. SQL injection vulnerability (Comment 1) - FIXED in abc123

## Action Plan

TodoWrite tracking:
- [x] Fix: SQL injection vulnerability (Priority: Critical)
- [x] Add: Error handling for DB operations (Priority: Important)
- [x] Add: TypeScript interface for preferences (Priority: Important)
- [x] Add: Test for invalid language codes (Priority: Nice-to-have)
- [ ] Respond to all comments
- [ ] Push fixes commit
- [ ] Re-request review

## Next Steps

1. ✅ Implemented all fixes
2. Push commit: "fix: Address review feedback - SQL injection, error handling, type safety"
3. Respond to each comment individually
4. Re-request review from Gemini and @john-reviewer
5. Monitor for approval
```

## Response Templates

### For Valid Issues

```markdown
"Excellent catch! Fixed in {commit-sha}. {Brief explanation of fix}"
```

### For Good Suggestions

```markdown
"Great suggestion! Implemented in {commit-sha}."
```

### For False Positives

```markdown
"Thanks for reviewing! This is actually intentional because {reason}. {Additional context}"
```

### For Debatable Suggestions

```markdown
"Interesting point! I chose {current-approach} because {reason}.

Trade-offs:
- Current: {pros/cons}
- Suggested: {pros/cons}

Open to changing if you feel the suggested approach is better for {specific-reason}."
```

### For Questions

```markdown
"Good question! {Answer with context}. Let me know if you need more details."
```

## Integration with Conductor

```markdown
# Conductor workflow after creating PR

Step 1: Create PR (already done)

Step 2: Check PR status (use this prompt)
"Check my PR #{number} in {repo} and analyze all review comments including Gemini feedback"

Step 3: Address feedback
- Fix critical issues immediately
- Create todo list for other fixes
- Draft responses

Step 4: Push fixes
- Commit with clear message referencing comments
- Push to PR branch

Step 5: Respond to comments
- Post responses to each comment
- Re-request review

Step 6: Monitor until merged
```

## Automation Opportunities

**Could be automated:**
- Fetching PR details
- Categorizing comment types
- Identifying blocking vs non-blocking
- Generating todo list

**Should be manual:**
- Deciding whether to accept suggestion
- Implementing fixes (with agent help)
- Responding to reviewers (personalized)

## Best Practices

### DO:
✅ Respond to every comment (shows respect)
✅ Fix legitimate issues promptly
✅ Explain reasoning when disagreeing
✅ Thank reviewers for their time
✅ Be open to feedback
✅ Ask clarifying questions
✅ Update tests when fixing bugs

### DON'T:
❌ Ignore AI reviewer comments (they're often valid)
❌ Be defensive or dismissive
❌ Fix without understanding why
❌ Leave comments unresolved
❌ Merge without addressing blocking issues
❌ Argue over style (follow project conventions)

## Common Gemini Feedback Categories

### Security
- SQL injection
- XSS vulnerabilities
- Authentication bypasses
- Data exposure

**Action:** Always fix immediately

### Code Quality
- Missing error handling
- Poor naming
- Complex functions
- Duplicated code

**Action:** Evaluate and fix high-impact issues

### Type Safety
- Using 'any' type
- Missing null checks
- Type assertions

**Action:** Fix for better maintainability

### Testing
- Missing test cases
- Uncovered edge cases
- Test quality

**Action:** Add important test coverage

### Performance
- N+1 queries
- Unnecessary loops
- Memory leaks

**Action:** Profile and fix if significant

### Style/Convention
- Formatting
- Naming conventions
- Code organization

**Action:** Follow project standards

## False Positive Handling

**When AI reviewer is wrong:**

1. **Verify** - Double-check the AI is actually wrong
2. **Explain** - Respond with clear reasoning
3. **Provide context** - Share domain knowledge AI lacks
4. **Request clarification** - Tag human reviewer if needed

Example:
```markdown
"Thanks for the review! This pattern might look unusual, but it's required for {specific-framework/library} compatibility. See {docs-link}. The {alternative-approach} suggested would break {specific-behavior}."
```

## Continuous Improvement

**Learn from reviews:**
- Common issues → Add to pre-commit checks
- Repeated feedback → Update coding guidelines
- Security patterns → Add to security checklist
- Performance issues → Add profiling to CI

## Notes

- This prompt works with any AI reviewer (Gemini, Copilot, etc.)
- Always evaluate AI feedback critically
- Human reviewers take priority over AI
- Use reviews as learning opportunities
- Keep responses professional and constructive
