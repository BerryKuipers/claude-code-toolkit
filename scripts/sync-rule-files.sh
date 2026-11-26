#!/usr/bin/env bash
set -euo pipefail

SOURCE_CLAUDE_DIR="${1:?source .claude directory required}"
TARGET_CLAUDE_DIR="${2:?target .claude directory required}"
MANIFEST="$(cd "$(dirname "$0")" && pwd)/retired-rule-hashes.sha256"

file_digest() {
  local digest
  if command -v sha256sum >/dev/null 2>&1; then
    digest="$(sha256sum "$1")"
  elif command -v shasum >/dev/null 2>&1; then
    digest="$(shasum -a 256 "$1")"
  else
    echo "[sync] SHA-256 support is required to preserve customized rules." >&2
    return 1
  fi
  echo "${digest%% *}"
}

mkdir -p "$TARGET_CLAUDE_DIR/rules"
STATE="$TARGET_CLAUDE_DIR/.toolkit-rule-hashes.sha256"
if [ -L "$STATE" ]; then
  echo "[sync] Refusing a linked rule ownership manifest: $STATE" >&2
  exit 1
fi
NEXT_STATE="$(mktemp "$STATE.XXXXXX")"
trap 'rm -f "$NEXT_STATE"' EXIT
for rule in "$SOURCE_CLAUDE_DIR/rules/"*.md; do
  [ -f "$rule" ] || continue
  filename="$(basename "$rule")"
  target="$TARGET_CLAUDE_DIR/rules/$filename"
  source_hash="$(file_digest "$rule")"
  previous_hash=''
  if [ -f "$STATE" ]; then
    previous_hash="$(awk -v name="$filename" '$2 == name { print $1; exit }' "$STATE")"
  fi
  if [ -L "$target" ] || { [ -e "$target" ] && [ ! -f "$target" ]; }; then
    echo "[sync] Kept non-regular native rule: $filename"
    [ -z "$previous_hash" ] || echo "$previous_hash $filename" >> "$NEXT_STATE"
    continue
  fi
  if [ -f "$target" ]; then
    target_hash="$(file_digest "$target")"
    if [ "$target_hash" != "$source_hash" ] && [ "$target_hash" != "$previous_hash" ]; then
      echo "[sync] Kept customized native rule; reconcile with toolkit source: $filename"
      [ -z "$previous_hash" ] || echo "$previous_hash $filename" >> "$NEXT_STATE"
      continue
    fi
  fi
  cp -a "$rule" "$target"
  echo "$source_hash $filename" >> "$NEXT_STATE"
done
mv "$NEXT_STATE" "$STATE"

while read -r lf_hash crlf_hash filename; do
  [ -n "$filename" ] || continue
  if [[ "$filename" == */* || "$filename" != *.mdc ]]; then
    echo "[sync] Invalid retired-rule manifest entry: $filename" >&2
    exit 1
  fi
  legacy="$TARGET_CLAUDE_DIR/rules/$filename"
  [ -e "$legacy" ] || [ -L "$legacy" ] || continue
  if [ -L "$legacy" ] || [ ! -f "$legacy" ]; then
    echo "[sync] Kept non-regular legacy rule: $filename"
    continue
  fi
  digest="$(file_digest "$legacy")"
  if [ "$digest" != "$lf_hash" ] && [ "$digest" != "$crlf_hash" ]; then
    echo "[sync] Kept customized legacy rule; reconcile with native Markdown rules: $filename"
    continue
  fi
  archive="$TARGET_CLAUDE_DIR/reference/retired-toolkit-rules/$filename"
  mkdir -p "$(dirname "$archive")"
  if [ -L "$archive" ] || { [ -e "$archive" ] && ! cmp -s "$legacy" "$archive"; }; then
    echo "[sync] Kept legacy rule; archive already contains different content: $filename"
    continue
  fi
  mv "$legacy" "$archive"
  echo "[sync] Archived unchanged legacy rule: $filename"
done < "$MANIFEST"
