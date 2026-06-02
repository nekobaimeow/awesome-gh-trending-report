#!/bin/bash
# publish.sh — commit all report changes, update indexes, and push to GitHub.
# Run from repo root. Called by cron jobs after generating reports.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# 1. Regenerate README indexes (includes tag cloud)
python3 src/update-index.py

# 2. Stage everything (new reports + updated READMEs)
git add -A

# 3. Commit (skip if nothing changed)
if git diff --cached --quiet; then
    echo "📭 Nothing to commit — repo is up to date."
    exit 0
fi

# Generate a meaningful commit message from what changed
CHANGED=$(git diff --cached --name-only | head -5 | tr '\n' ' ')
COMMIT_MSG="auto: $(date -u +'%Y-%m-%d %H:%M UTC') — ${CHANGED:0:200}"
git commit -m "$COMMIT_MSG"

# 4. Push
git push origin main 2>&1

echo "🚀 Published successfully."
