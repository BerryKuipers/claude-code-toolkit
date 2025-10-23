# Sync with Gemini AI Studio

Streamline the workflow for syncing code changes between Claude Code and Gemini AI Studio.

## Usage

You are Claude Code assistant. When the user invokes this command, execute the appropriate sync workflow.

**User says:**
- `/sync-gemini` or `/sync-gemini to-studio` - Prepare main branch for Gemini to commit changes
- `/sync-gemini from-studio` - Import and review changes from AI Studio
- `/sync-gemini status` - Check sync status and recommendations

---

## Workflow 1: TO AI STUDIO (Default)

**Purpose:** Push Claude Code's work to main so Gemini can add features on top.

**Execute autonomously:**

1. **Pre-flight Checks**
   - Verify not on main branch (should be on development)
   - Check for uncommitted changes - fail if any exist
   - Fetch latest from origin
   - Verify development is up to date with remote

2. **Merge Development → Main**
   ```bash
   git checkout main
   git merge development
   ```
   - If merge fails, report conflicts and stop
   - Prefer fast-forward merges

3. **Push to Remote**
   ```bash
   git push origin main
   ```

4. **Return to Development**
   ```bash
   git checkout development
   ```

5. **Report Success**
   ```
   ✅ Main branch synced successfully!

   📋 NEXT STEPS IN GEMINI AI STUDIO:
   1. Open your project in AI Studio
   2. **IMPORTANT: Manually pull/sync the main branch** (AI Studio doesn't auto-pull!)
   3. Verify you're on 'main' branch with latest commits
   4. Make your frontend changes
   5. Commit changes to 'main'
   6. Come back and run: /sync-gemini from-studio

   📊 Current commits:
   Main: <commit-hash> - <message>
   Dev:  <commit-hash> - <message>
   ```

---

## Workflow 2: FROM AI STUDIO

**Purpose:** Import Gemini's changes from AI Studio into development branch.

**Execute autonomously:**

1. **Fetch Latest**
   ```bash
   git fetch origin main
   ```

2. **Check for Changes**
   - Compare local main with origin/main
   - If no changes, report "No new changes from AI Studio"

3. **Show What Changed**
   ```bash
   git log main..origin/main --oneline
   git diff --stat main origin/main
   ```

4. **Review Files Changed**
   - List modified files
   - Check if any are infrastructure files (warn if so)
   - Check if package.json changed (note to run npm install)

5. **Auto-Merge Strategy**
   Since we didn't touch frontend files, merge should be safe:
   ```bash
   git checkout main
   git merge origin/main --ff-only  # Fast-forward only
   git checkout development
   git merge main  # Merge into development
   ```

6. **Post-Merge Actions**
   - Run `npm install` if package.json changed
   - Report success with list of changed files
   - Suggest testing with `npm run dev`

---

## Workflow 3: STATUS CHECK

**Purpose:** Show current sync state and recommend actions.

**Execute autonomously:**

1. **Fetch Latest**
   ```bash
   git fetch origin
   ```

2. **Compare Branches**
   - Development local vs remote
   - Main local vs remote
   - Development vs Main (who's ahead?)

3. **Report Status**
   ```
   📊 SYNC STATUS:

   Current branch: <branch-name>

   Development: ✅ In sync / ⚠️ Out of sync
   Main:        ✅ In sync / ⚠️ Out of sync

   Development is X commits ahead of main
   OR
   Main is X commits ahead of development (from AI Studio)

   💡 RECOMMENDATION:
   - Run /sync-gemini to-studio (if dev ahead)
   - Run /sync-gemini from-studio (if main ahead)
   - All in sync! 🎉
   ```

---

## Safety Checks

**Before any merge:**
- ✅ Check for uncommitted changes
- ✅ Verify branches are up to date with remote
- ✅ Confirm fast-forward merge is possible
- ✅ Check we're not on main when starting

**Error Handling:**

If merge conflicts occur:
```
❌ Merge conflict detected!

Conflicting files:
<list files>

To resolve manually:
1. Fix conflicts in files above
2. git add <files>
3. git commit
4. Run /sync-gemini again

To abort: git merge --abort
```

---

## Implementation Logic

**Key Decision Points:**

1. **Direction Detection:**
   - `to-studio` = merge dev→main, push
   - `from-studio` = fetch, merge main→dev
   - `status` = report only, no changes

2. **Conflict Avoidance:**
   - Use fast-forward merges when possible
   - Check file overlap before merging
   - Warn if infrastructure files changed in AI Studio

3. **Automatic vs Manual:**
   - to-studio: Fully automatic (we control dev)
   - from-studio: Automatic if no conflicts (Gemini controls main)
   - status: Read-only, always safe

---

## Usage Examples

**Example 1: After working in Claude Code**
```
User: /sync-gemini
Claude: *executes to-studio workflow*
Claude: ✅ Main synced! Now commit your changes in AI Studio.
```

**Example 2: After Gemini made changes**
```
User: /sync-gemini from-studio
Claude: *fetches, shows changes*
Claude: Found 3 new commits in AI Studio
        - Updated CharacterCard.tsx
        - Added new StoryTimeline component
        - Fixed image loading bug
Claude: *auto-merges into development*
Claude: ✅ Changes imported! Remember to run: npm install
```

**Example 3: Check status**
```
User: /sync-gemini status
Claude: 📊 Development is 2 commits ahead of main
        💡 Run: /sync-gemini to-studio
```

---

## Related Workflows

- After sync to-studio: Work in AI Studio
- After sync from-studio: Test with `npm run dev`
- Before either sync: Commit your changes
- If conflicts: Resolve manually, then re-run

---

## Notes for Claude Code Assistant

When executing this command:

1. **Be autonomous** - Don't ask for confirmation at each step
2. **Be clear** - Show what's happening as you work
3. **Be safe** - Stop if anything looks risky
4. **Be helpful** - Provide next steps in output
5. **Use git commands** - Don't manually edit files
6. **Report thoroughly** - Show commit hashes and messages

This command bridges two AI development environments - handle with care!
