#!/usr/bin/env bash
set -e

# Simple helper to add, commit and push the main project files to your GitHub remote.
# Usage: ./push_to_github.sh "commit message"

FILES="app.py timba_core.py cli.py requirements.txt README.md"

echo "Files to add: $FILES"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo. Initialize and add a remote first."; exit 1; }

echo "Staging files..."
git add $FILES || true

MSG="${1:-Update: integrate changes}" 
if git diff --cached --quiet; then
  echo "No staged changes to commit. Skipping commit."
else
  git commit -m "$MSG"
fi

if git remote | grep -q origin; then
  echo "Origin remote found: $(git remote get-url origin)"
else
  read -p "No 'origin' remote found. Enter GitHub repo URL (ssh or https): " REPO_URL
  if [ -z "$REPO_URL" ]; then
    echo "No remote provided. Aborting."
    exit 1
  fi
  git remote add origin "$REPO_URL"
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $BRANCH"

echo "Pushing branch $BRANCH to origin (will set upstream)..."
git push -u origin "$BRANCH"

echo "Push complete. If GitHub requires a PAT for HTTPS, configure credentials or use SSH keys."
