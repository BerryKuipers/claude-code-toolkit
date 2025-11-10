#!/usr/bin/env python3
"""
Update existing API Skills with new versions

This script creates new versions of existing skills by POSTing to the
/v1/skills/{skill_id}/versions endpoint.

Requires ANTHROPIC_SKILLS_API_KEY environment variable and a mapping
of skill names to their IDs.
"""

import os
import json
import requests
from pathlib import Path
import re


# Map skill directory names to their Skill IDs
SKILL_IDS = {
    # Session 1 & 2 skills
    "validate-typescript": "skill_01TYxAPLSwWUAJvpiBgaDcfn",
    "run-comprehensive-tests": "skill_01EfbHCDmLehZ9CNKxxRBMzZ",
    "validate-coverage-threshold": "skill_01KvzeoAq1YbafijP1RiJSJw",
    "quality-gate": "skill_016qnPYM55EUfzTjTCeL4Zng",
    # Session 2 additional skills
    "validate-lint": "skill_0154reaLWo6CsYUmARtg9aCk",
    "validate-build": "skill_01Ew1QtJeHnYdpwAXj2HhrNw",
    "validate-git-hygiene": "skill_019bRtByNMx2hjhtnL5uhowG",
    "audit-dependencies": "skill_01JvZxokSnKZ7bLwLQMAvKo1"
}


def get_skill_display_title(skill_dir: Path) -> str:
    """Extract display title from SKILL.md frontmatter"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return skill_dir.name

    with open(skill_md) as f:
        content = f.read()
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            yaml_content = frontmatter_match.group(1)
            for line in yaml_content.split('\n'):
                if line.startswith('name:'):
                    return line.split(':', 1)[1].strip()

    return skill_dir.name


def update_skill_version(skill_dir: Path, skill_id: str, api_key: str) -> dict:
    """
    Create a new version of an existing skill.

    Args:
        skill_dir: Path to skill directory containing SKILL.md and other files
        skill_id: Existing skill ID (e.g., skill_01TYxAPLSwWUAJvpiBgaDcfn)
        api_key: Anthropic API key

    Returns:
        API response with new version info
    """
    # Check for required SKILL.md file
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    display_title = get_skill_display_title(skill_dir)

    # Prepare API request for version creation
    url = f"https://api.anthropic.com/v1/skills/{skill_id}/versions"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "skills-2025-10-02"
    }

    # Collect all files in skill directory
    files_to_upload = []
    for file_path in skill_dir.rglob('*'):
        if file_path.is_file() and file_path.name != '__pycache__':
            # Calculate relative path from skill_dir parent
            rel_path = file_path.relative_to(skill_dir.parent)
            files_to_upload.append((file_path, rel_path))

    print(f"\n📤 Updating skill: {display_title}")
    print(f"   Skill ID: {skill_id}")
    print(f"   Folder: {skill_dir.name}")
    print(f"   Files: {len(files_to_upload)}")

    # Prepare multipart form data
    files = []
    file_handles = []

    try:
        # Open all files
        for file_path, rel_path in files_to_upload:
            try:
                file_handle = open(file_path, 'rb')
                file_handles.append(file_handle)
                files.append(
                    ('files[]', (str(rel_path), file_handle, 'application/octet-stream'))
                )
            except IOError as e:
                for fh in file_handles:
                    fh.close()
                raise IOError(f"Failed to read file {file_path}: {e}")

        data = {
            'display_title': display_title
        }

        # POST to versions endpoint to create new version
        response = requests.post(url, headers=headers, data=data, files=files)

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ New version created!")
            print(f"   Version ID: {result.get('id')}")
            print(f"   Version Number: {result.get('version')}")
            return result
        else:
            print(f"❌ Update failed: {response.status_code}")
            print(f"   Error: {response.text}")
            raise Exception(f"Failed to update skill: {response.text}")

    finally:
        # Always close file handles
        for file_handle in file_handles:
            try:
                file_handle.close()
            except:
                pass


def get_skill_info(skill_id: str, api_key: str) -> dict:
    """Get current skill information"""
    url = f"https://api.anthropic.com/v1/skills/{skill_id}"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "skills-2025-10-02"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get skill info: {response.text}")


def main():
    """Update all skills with new versions."""
    api_key = os.getenv("ANTHROPIC_SKILLS_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_SKILLS_API_KEY environment variable not set")
        return 1

    print("🔑 Found ANTHROPIC_SKILLS_API_KEY")

    # Find skills directory
    skills_dir = Path(__file__).parent
    print(f"📁 Skills directory: {skills_dir}")

    # Find skill directories that have IDs
    skill_dirs = []
    for item in skills_dir.iterdir():
        if item.is_dir() and item.name != "__pycache__":
            if (item / "SKILL.md").exists() and item.name in SKILL_IDS:
                skill_dirs.append(item)

    if not skill_dirs:
        print("⚠️  No known skills found to update")
        print("   Skills with IDs:")
        for name, skill_id in SKILL_IDS.items():
            print(f"   - {name}: {skill_id}")
        return 0

    print(f"\n🎯 Found {len(skill_dirs)} skill(s) to update:")
    for skill_dir in skill_dirs:
        skill_id = SKILL_IDS[skill_dir.name]
        print(f"   - {skill_dir.name} ({skill_id})")

    # Show current versions
    print("\n📋 Current versions:")
    for skill_dir in skill_dirs:
        skill_id = SKILL_IDS[skill_dir.name]
        try:
            info = get_skill_info(skill_id, api_key)
            print(f"   - {skill_dir.name}: v{info.get('latest_version')}")
        except Exception as e:
            print(f"   - {skill_dir.name}: Error fetching version")

    # Update each skill
    updated_skills = []
    failed_skills = []

    for skill_dir in skill_dirs:
        skill_id = SKILL_IDS[skill_dir.name]
        try:
            result = update_skill_version(skill_dir, skill_id, api_key)
            updated_skills.append({
                "name": skill_dir.name,
                "skill_id": skill_id,
                "version": result.get("version"),
                "version_id": result.get("id")
            })
        except Exception as e:
            print(f"❌ Failed to update {skill_dir.name}: {e}")
            failed_skills.append(skill_dir.name)

    # Summary
    print("\n" + "="*60)
    print("📊 Update Summary")
    print("="*60)
    print(f"✅ Updated: {len(updated_skills)}")
    print(f"❌ Failed: {len(failed_skills)}")

    if updated_skills:
        print("\n✅ Successfully updated skills:")
        for skill in updated_skills:
            print(f"   - {skill['name']}")
            print(f"     Skill ID: {skill['skill_id']} (unchanged)")
            print(f"     New Version: {skill['version']}")
            print(f"     Version ID: {skill['version_id']}")

    if failed_skills:
        print("\n❌ Failed to update:")
        for name in failed_skills:
            print(f"   - {name}")

    print("="*60)

    return 0 if not failed_skills else 1


if __name__ == "__main__":
    exit(main())
