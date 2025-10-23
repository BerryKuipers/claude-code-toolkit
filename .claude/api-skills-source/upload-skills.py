#!/usr/bin/env python3
"""
Upload custom API Skills to Anthropic

This script uploads skills from .claude/api-skills-source/ to Anthropic's Skills API.
Requires ANTHROPIC_API_KEY environment variable.
"""

import os
import json
import requests
from pathlib import Path


def upload_skill(skill_dir: Path, api_key: str) -> dict:
    """
    Upload a single skill to Anthropic Skills API.

    Args:
        skill_dir: Path to skill directory containing SKILL.md and other files
        api_key: Anthropic API key

    Returns:
        API response with skill_id
    """
    # Check for required SKILL.md file
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    # Load skill metadata from SKILL.md frontmatter
    with open(skill_md) as f:
        content = f.read()
        # Parse YAML frontmatter for display title
        import re
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        display_title = skill_dir.name
        if frontmatter_match:
            yaml_content = frontmatter_match.group(1)
            for line in yaml_content.split('\n'):
                if line.startswith('name:'):
                    display_title = line.split(':', 1)[1].strip()
                    break

    # Prepare API request
    url = "https://api.anthropic.com/v1/skills"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "skills-2025-10-02"
    }

    # Collect all files in skill directory
    files_to_upload = []
    for file_path in skill_dir.rglob('*'):
        if file_path.is_file() and file_path.name != '__pycache__':
            # Calculate relative path from skill_dir
            rel_path = file_path.relative_to(skill_dir.parent)
            files_to_upload.append((file_path, rel_path))

    print(f"\n📤 Uploading skill: {display_title}")
    print(f"   Folder: {skill_dir.name}")
    print(f"   Files: {len(files_to_upload)}")

    # Prepare multipart form data with proper error handling
    files = []
    file_handles = []

    try:
        # Open all files with error handling
        for file_path, rel_path in files_to_upload:
            try:
                file_handle = open(file_path, 'rb')
                file_handles.append(file_handle)
                files.append(
                    ('files[]', (str(rel_path), file_handle, 'application/octet-stream'))
                )
            except IOError as e:
                # Close any previously opened files before failing
                for fh in file_handles:
                    fh.close()
                raise IOError(f"Failed to read file {file_path}: {e}")

        data = {
            'display_title': display_title
        }

        # Upload to API
        response = requests.post(url, headers=headers, data=data, files=files)

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Successfully uploaded!")
            print(f"   Skill ID: {result.get('id')}")
            print(f"   Version: {result.get('latest_version')}")
            return result
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            raise Exception(f"Failed to upload skill: {response.text}")

    finally:
        # Always close file handles, even on error
        for file_handle in file_handles:
            try:
                file_handle.close()
            except:
                pass  # Ignore errors during cleanup


def list_skills(api_key: str) -> list:
    """List all available skills."""
    url = "https://api.anthropic.com/v1/skills"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25,skills-2025-10-02"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("skills", [])
    else:
        raise Exception(f"Failed to list skills: {response.text}")


def main():
    """Upload all skills in api-skills-source directory."""
    # Check for API key (use custom var to avoid conflict with Claude Code)
    api_key = os.getenv("ANTHROPIC_SKILLS_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_SKILLS_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_SKILLS_API_KEY=your-key-here")
        print("\nOr add it to Claude Code web environment settings")
        print("\nNote: Use ANTHROPIC_SKILLS_API_KEY (not ANTHROPIC_API_KEY)")
        print("      to avoid conflict with Claude Code's internal authentication")
        return 1

    print("🔑 Found ANTHROPIC_SKILLS_API_KEY")

    # Find skills directory
    skills_dir = Path(__file__).parent
    if not skills_dir.exists():
        print(f"❌ Skills directory not found: {skills_dir}")
        return 1

    print(f"📁 Skills directory: {skills_dir}")

    # Find all skill directories (contain SKILL.md)
    skill_dirs = []
    for item in skills_dir.iterdir():
        if item.is_dir() and item.name != "__pycache__":
            if (item / "SKILL.md").exists():
                skill_dirs.append(item)

    if not skill_dirs:
        print("⚠️  No skills found to upload")
        print("   Each skill needs: SKILL.md file")
        return 0

    print(f"\n🎯 Found {len(skill_dirs)} skill(s) to upload:")
    for skill_dir in skill_dirs:
        print(f"   - {skill_dir.name}")

    # Upload each skill
    uploaded_skills = []
    failed_skills = []

    for skill_dir in skill_dirs:
        try:
            result = upload_skill(skill_dir, api_key)
            uploaded_skills.append({
                "name": skill_dir.name,
                "skill_id": result.get("id"),
                "version": result.get("version")
            })
        except Exception as e:
            print(f"❌ Failed to upload {skill_dir.name}: {e}")
            failed_skills.append(skill_dir.name)

    # Summary
    print("\n" + "="*60)
    print("📊 Upload Summary")
    print("="*60)
    print(f"✅ Uploaded: {len(uploaded_skills)}")
    print(f"❌ Failed: {len(failed_skills)}")

    if uploaded_skills:
        print("\n✅ Successfully uploaded skills:")
        for skill in uploaded_skills:
            print(f"   - {skill['name']}")
            print(f"     ID: {skill['skill_id']}")
            print(f"     Version: {skill['version']}")

    if failed_skills:
        print("\n❌ Failed to upload:")
        for name in failed_skills:
            print(f"   - {name}")

    # List all skills
    print("\n📋 Listing all your custom skills:")
    try:
        all_skills = list_skills(api_key)
        custom_skills = [s for s in all_skills if s.get("source") == "custom"]

        if custom_skills:
            for skill in custom_skills:
                print(f"   - {skill.get('name')} (ID: {skill.get('id')})")
        else:
            print("   No custom skills found")
    except Exception as e:
        print(f"   ⚠️  Could not list skills: {e}")

    print("="*60)

    return 0 if not failed_skills else 1


if __name__ == "__main__":
    exit(main())
