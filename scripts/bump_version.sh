#!/usr/bin/env bash
# 版本递增脚本 — 语义: x.x.x (重大更新.补丁.修补)
#   patch: 修补, 自动递增 (x.x.x+1)
#   minor: 补丁, 功能新增 (x.x+1.0)
#   major: 重大更新 (x+1.0.0)
# 用法: bump_version.sh [patch|minor|major] [PREFIX]   (PREFIX 为空则 vX.Y.Z, 如 debug- 则 debug-vX.Y.Z)
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-yxyyds666/TB331FC-Kernel}"
BUMP="${1:-patch}"
PREFIX="${2:-}"

# 读取最新 release tag (按前缀 + 严格 x.y.z 格式过滤, 使各分支版本序列独立)
# limit 100: 新模型下所有 Release 均为同一前缀, 最新版本总在列表内
LATEST=$(gh release list --repo "$REPO" --limit 100 --json tagName -q '.[].tagName' 2>/dev/null \
  | grep -E "^${PREFIX}v?[0-9]+\.[0-9]+\.[0-9]+$" | sort -V | tail -1 || echo "")
# 首次发布固定 1.0.0, 之后按 bump 递增
if [ -z "$LATEST" ]; then
  echo "${PREFIX}1.0.0"
  exit 0
fi

# 剥离前缀与可选的 v (tag 可能为 1.0.0 / v1.0.0 / debug-1.0.0 / debug-v1.0.0)
VER="${LATEST#${PREFIX}}"
VER="${VER#v}"

IFS='.' read -r MAJOR MINOR PATCH <<< "$VER"
MAJOR=${MAJOR:-0}; MINOR=${MINOR:-0}; PATCH=${PATCH:-0}

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch|*) PATCH=$((PATCH + 1)) ;;
esac

echo "${PREFIX}$MAJOR.$MINOR.$PATCH"
