#!/usr/bin/env sh
set -e

LAYOUT="${1:-specguard-default}"
DEST="$HOME/.local/share/specguard/plugins/${LAYOUT}"

VERSION=$(curl -s https://api.github.com/repos/saberhaha/specguard/releases/latest \
  | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')

if [ -z "$VERSION" ]; then
  echo "Error: failed to fetch latest version from GitHub API" >&2
  exit 1
fi

mkdir -p "$DEST"

curl -L "https://github.com/saberhaha/specguard/releases/latest/download/specguard-claude-${LAYOUT}-v${VERSION}.tar.gz" \
  | tar -xz -C "$DEST"

echo ""
echo "specguard ${LAYOUT} v${VERSION} 已安装到 ${DEST}"
echo ""
echo "在目标项目（git 仓库）���运行 init："
echo "  claude --plugin-dir ${DEST} -p '/specguard:init --ai claude --spec none'"
echo ""
echo "随时运行治理检查："
echo "  claude --plugin-dir ${DEST} -p '/specguard:check'"
