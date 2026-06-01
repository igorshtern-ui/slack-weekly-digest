#!/bin/bash
# Dual Git push: Autodesk Git Enterprise (primary) + GitHub (mirror)

set -euo pipefail

echo "🚀 Pushing to both Git remotes..."

if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
echo "📋 Current branch: $CURRENT_BRANCH"

echo "📤 Pushing to Autodesk Git Enterprise (primary)..."
if git push autodesk "$CURRENT_BRANCH"; then
    echo "✅ Successfully pushed to Autodesk Git Enterprise"
else
    echo "❌ Failed to push to Autodesk Git Enterprise"
    echo "💡 Run: gh auth login --hostname git.autodesk.com"
    exit 1
fi

echo "📤 Pushing to GitHub (mirror)..."
if git push origin "$CURRENT_BRANCH"; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    echo "⚠️  Autodesk push succeeded; fix GitHub auth and retry: git push origin $CURRENT_BRANCH"
    exit 1
fi

echo "🎉 Successfully pushed to both remotes"
echo "🏢 Primary:  https://git.autodesk.com/shterni/slack-weekly-digest"
echo "📊 Mirror:   https://github.com/igorshtern-ui/slack-weekly-digest"
