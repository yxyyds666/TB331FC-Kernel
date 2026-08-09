#!/usr/bin/env bash
# 版本递增脚本 — 语义: x.x.x (重大更新.补丁.修补)
#   patch: 修补, 自动递增 (x.x.x+1)
#   minor: 补丁, 功能新增 (x.x+1.0)
#   major: 重大更新 (x+1.0.0)
# 用法: bump_version.sh [patch|minor|major]   (默认 patch)
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-yxyyds666/TB331FC-Kernel}"
BUMP="${1:-patch}"

# 读取最新 release tag
LATEST=$(gh release list --repo "$REPO" --limit 1 --json tagName -q '.[0].tagName' 2>/dev/null || echo "")
# 首次发布固定 1.0.0, 之后按 bump 递增
if [ -z "$LATEST" ]; then
  echo "1.0.0"
  exit 0
fi

if [[ "$LATEST" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  VER="${LATEST#v}"
else
  VER="1.0.0"
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$VER"
MAJOR=${MAJOR:-0}; MINOR=${MINOR:-0}; PATCH=${PATCH:-0}

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch|*) PATCH=$((PATCH + 1)) ;;
esac

echo "$MAJOR.$MINOR.$PATCH"
