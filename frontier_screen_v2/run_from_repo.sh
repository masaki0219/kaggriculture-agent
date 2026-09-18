#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

# Accept either:
#   1) running from the kaggriculture-agent/Kaggle repository root, or
#   2) running directly inside the frontier_screen_v2 bundle placed under it.
if [[ -f "$PWD/artifacts/bundles/current/setup_elite_candidates.py" ]]; then
  REPO_ROOT="$PWD"
elif [[ -f "$SCRIPT_DIR/../artifacts/bundles/current/setup_elite_candidates.py" ]]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  echo "ERROR: could not find repository root." >&2
  echo "Expected artifacts/bundles/current/setup_elite_candidates.py either in:" >&2
  echo "  $PWD" >&2
  echo "or" >&2
  echo "  $SCRIPT_DIR/.." >&2
  exit 2
fi

cd "$REPO_ROOT"
echo "Repository root: $REPO_ROOT"

"$PYTHON_BIN" "$SCRIPT_DIR/install.py" --repo "$REPO_ROOT"

pushd artifacts/bundles/current >/dev/null
"$PYTHON_BIN" setup_elite_candidates.py --only aurax7_v7_current
"$PYTHON_BIN" setup_elite_candidates.py --only ahmed_v44_current
"$PYTHON_BIN" setup_elite_candidates.py --only tetsu_market_v23_current
popd >/dev/null

"$PYTHON_BIN" evaluation/frontier_screen_v2/arena.py \
  --seeds "${FRONTIER_SEEDS:-8}" \
  --seed-start "${FRONTIER_SEED_START:-18000}"

echo
echo "Result: evaluation/frontier_screen_v2/results.json"
echo "Do not assign E21 yet; use family W/D/L, worst-family, and portfolio both-loss diagnostics first."
