# Agent Skills Quick Start

Get started with Agent Skills in 5 minutes.

## What You Have Now

✅ **4 Foundational Skills Created:**
1. `run-comprehensive-tests` - Test execution and validation
2. `create-pull-request` - PR creation with proper linking
3. `gemini-api-rate-limiting` - Gemini API best practices
4. `quality-gate` - Complete quality validation workflow

## Activation (Required)

**Skills are not active until you restart Claude Code:**

```bash
# 1. Save all your work
# 2. Exit Claude Code
# 3. Restart Claude Code
# 4. Skills are now loaded and active
```

## Testing Skills

After restart, test if skills are working:

**Test 1: Direct Reference**
```
Ask Claude: "Use the run-comprehensive-tests skill to validate all tests"

Expected: Claude will reference the skill and follow its instructions
```

**Test 2: Automatic Discovery**
```
Ask Claude: "How should I handle Gemini API rate limits?"

Expected: Claude may automatically reference the gemini-api-rate-limiting skill
```

**Test 3: Workflow Integration**
```
Ask Claude: "Run the quality gate before creating my PR"

Expected: Claude uses quality-gate skill for validation
```

## Next Steps

### Phase 1: Test Current Skills (This Week)
1. ✅ Skills created
2. ⏳ Restart Claude Code
3. ⏳ Test skill activation
4. ⏳ Use skills in conductor workflow
5. ⏳ Refine based on feedback

### Phase 2: Expand Skills (Next Week)
Add more skills:
- `commit-changes` - Atomic commit with validation
- `gemini-api-image-generation` - Complete image gen workflow
- `react-component-structure` - React best practices
- `audit-code` - Quality audit execution

### Phase 3: Full Integration (Week 3)
Update conductor agent:
- Phase 3 → Use `quality-gate` skill
- Phase 4 → Use `create-pull-request` skill
- Verify end-to-end workflow

## Documentation

- **README.md** - Complete skills overview
- **INTEGRATION-GUIDE.md** - How to integrate with agents
- **Individual skills** - See each skill's SKILL.md

## Troubleshooting

**Skills not being used?**
1. Did you restart Claude Code? (Required!)
2. Check YAML frontmatter in SKILL.md files
3. Reference skills explicitly: "Use the X skill"

**Need help?**
- See README.md for full documentation
- See INTEGRATION-GUIDE.md for agent integration
- Check individual SKILL.md files for examples

---

**Created**: 2025-10-21
**Status**: Ready for activation (restart required)
**Next**: Restart Claude Code and test
