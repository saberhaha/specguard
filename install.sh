#!/usr/bin/env sh
set -e

VERSION=$(curl -s https://api.github.com/repos/saberhaha/specguard/releases/latest \
  | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')

if [ -z "$VERSION" ]; then
  echo "Error: failed to fetch latest version from GitHub API" >&2
  exit 1
fi

TMPDIR=$(mktemp -d)

curl -L "https://github.com/saberhaha/specguard/releases/latest/download/specguard-${VERSION}.tar.gz" \
  | tar -xz -C "$TMPDIR"

pip install --quiet "$TMPDIR/specguard-${VERSION}"
rm -rf "$TMPDIR"

echo ""
echo "specguard v${VERSION} 已安装。"
echo ""
echo "在目标项目（git 仓库）里初始化治理脚手架："
echo "  specguard init"
echo ""
echo "随时运行治理检查："
echo "  specguard check"
