#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
mkdir -p public_agents

clone_if_missing () {
  local url="$1"
  local dst="$2"
  if [ -d "$dst/.git" ]; then
    echo "[OK] $dst already exists"
  else
    echo "[CLONE] $url -> $dst"
    git clone "$url" "$dst"
  fi
}

clone_if_missing "https://github.com/straf10/Kaggriculture.git" "public_agents/straf10"
clone_if_missing "https://github.com/hbharath327/kaggriculture.git" "public_agents/hbharath"

echo
echo "Bulk candidate setup complete."
echo "Existing repos expected too:"
echo "  public_agents/qeinstein"
echo "  public_agents/gzmcr"
echo "  public_agents/lonespear"
