# API Skills Update Notes

## ✅ SOLVED: Skill Versioning Discovered!

The Anthropic Skills API **DOES support updating skills** via versioning!

### Update Mechanism

**Endpoint**: `POST /v1/skills/{skill_id}/versions`

Skills maintain the same ID but get new version numbers. This is perfect because:
- ✅ References in code don't break (skill ID stays same)
- ✅ New versions automatically become "latest"
- ✅ Can roll back to older versions if needed

### How to Update Skills

Use the `update-skills.py` script:

```bash
cd .claude/api-skills-source
python3 update-skills.py
```

The script:
1. Reads skill IDs from `SKILL_IDS` mapping
2. POSTs to `/v1/skills/{id}/versions` for each skill
3. Uploads all files from skill directory
4. Creates new version with incremented version number

### Version History

#### Session 2 Updates (2025-10-22)

**Update 1 - Gemini Fixes + Genericization**

All 4 skills updated with new versions:

| Skill | Skill ID | Old Version | New Version | Changes |
|-------|----------|-------------|-------------|---------|
| validate-typescript | `skill_01TYxAPLSwWUAJvpiBgaDcfn` | 1761123076691127 | **1761128219304907** | Generic references |
| run-comprehensive-tests | `skill_01EfbHCDmLehZ9CNKxxRBMzZ` | 1761123159646033 | **1761128220504389** | Improved error parsing |
| validate-coverage-threshold | `skill_01KvzeoAq1YbafijP1RiJSJw` | 1761123240799955 | **1761128219842138** | Text fallback parsing |
| quality-gate | `skill_016qnPYM55EUfzTjTCeL4Zng` | 1761120840799598 | **1761128221040182** | Generic references |

**Improvements Included:**
1. ✅ Fixed validate-coverage-threshold text fallback (Gemini feedback)
2. ✅ Improved run-comprehensive-tests error parsing (Gemini feedback)
3. ✅ Removed all WescoBar-specific references
4. ✅ Made skills generic and reusable

## Script Documentation

### update-skills.py

Creates new versions of existing skills.

**Features:**
- Maps skill directory names to skill IDs
- Shows current versions before updating
- Creates new versions via `/versions` endpoint
- Handles multipart file uploads
- Reports success/failure for each skill

**Usage:**
```bash
export ANTHROPIC_SKILLS_API_KEY=your-key
cd .claude/api-skills-source
python3 update-skills.py
```

**Adding New Skills:**
Update the `SKILL_IDS` mapping:
```python
SKILL_IDS = {
    "skill-name": "skill_01ABC123...",
    ...
}
```

## Best Practices

### When to Create New Versions

Create new versions when you:
- Fix bugs (like Gemini feedback)
- Add new features
- Improve error messages
- Update documentation
- Change behavior

### Version Strategy

- **Latest version** is used by default
- Can pin to specific version if needed: `skill_id@version`
- Version numbers are timestamps (auto-generated)
- No need to manually manage version numbers
