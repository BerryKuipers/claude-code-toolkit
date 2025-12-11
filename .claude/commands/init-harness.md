# Initialize Autonomous Coding Harness

Initialize the autonomous-coding harness for feature-driven development sessions.

## What This Does

1. Creates `.claude/harness/` directory with:
   - `feature_list.json` - Define features to implement
   - `claude-progress.txt` - Session progress tracking
   - `app_spec.txt` - Project context description
   - Session hooks for automatic progress updates

2. Copies harness scripts from toolkit templates

## Instructions

Run the harness initialization script:

```bash
bash .claude-toolkit/templates/harness/init.sh
```

After initialization:
1. Edit `.claude/harness/app_spec.txt` to describe your project
2. Edit `.claude/harness/feature_list.json` to define features
3. Start coding - progress is tracked automatically

## Next Steps

After running the init script, help the user:
1. Show them the created files
2. Offer to help populate `feature_list.json` with their planned features
3. Offer to help fill in `app_spec.txt` based on the codebase

## Documentation

See: `.claude-toolkit/docs/AUTONOMOUS_CODING_HARNESS.md`
