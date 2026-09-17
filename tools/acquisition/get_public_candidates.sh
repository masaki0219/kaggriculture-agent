#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
E11="$REPO_ROOT/artifacts/bundles/current/public_agents/elite/prvsiyan_frontier/raw/main.py"
OUTROOT="$REPO_ROOT/candidates/public_latest"

declare -a NAMES=(
  "farming_score_v3"
  "adaptive_route_v2"
  "shape_shop_top10"
)

declare -a KERNELS=(
  "lynnsakurai/farming-score-v3-replay-revised"
  "reyhanksatria/adaptive-route-agent-v2"
  "indarkarhana/shape-the-shop-work-the-pasture-top-10"
)

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

if ! command -v kaggle >/dev/null 2>&1; then
  echo "❌ kaggle CLI が見つかりません。"
  echo "   pip install kaggle"
  exit 1
fi

mkdir -p "$OUTROOT"

if [ -f "$E11" ]; then
  E11_SHA="$(sha256_file "$E11")"
else
  E11_SHA="02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79"
fi

echo "=== Kaggriculture 公開上位候補を一括取得 ==="
echo "E11 SHA: $E11_SHA"
echo

for i in "${!KERNELS[@]}"; do
  NAME="${NAMES[$i]}"
  KERNEL="${KERNELS[$i]}"
  DIR="$OUTROOT/$NAME"
  RAW="$DIR/raw"
  EXTRACT="$DIR/extracted"

  rm -rf "$DIR"
  mkdir -p "$RAW" "$EXTRACT"

  echo "[$((i+1))/${#KERNELS[@]}] $NAME"
  echo "  $KERNEL"

  if ! kaggle kernels output "$KERNEL" -p "$RAW" -o >/dev/null 2>&1; then
    echo "  ❌ 取得失敗"
    echo
    continue
  fi

  ARCHIVE="$(find "$RAW" -type f -name 'submission.tar.gz' | head -n 1 || true)"
  if [ -z "$ARCHIVE" ]; then
    ARCHIVE="$(find "$RAW" -type f -name '*.tar.gz' | head -n 1 || true)"
  fi

  if [ -n "$ARCHIVE" ]; then
    if tar -xzf "$ARCHIVE" -C "$EXTRACT" >/dev/null 2>&1; then
      :
    else
      echo "  ⚠️ tar.gz を展開できませんでした"
    fi
  fi

  MAIN="$(find "$EXTRACT" "$RAW" -type f -name 'main.py' | head -n 1 || true)"

  if [ -z "$MAIN" ]; then
    # Some notebooks emit a single .py under another name.
    PYFILE="$(find "$RAW" -type f -name '*.py' | head -n 1 || true)"
    if [ -n "$PYFILE" ]; then
      cp "$PYFILE" "$DIR/main.py"
      MAIN="$DIR/main.py"
    fi
  else
    cp "$MAIN" "$DIR/main.py"
    MAIN="$DIR/main.py"
  fi

  if [ -z "${MAIN:-}" ] || [ ! -f "$MAIN" ]; then
    echo "  ❌ main.py を自動発見できません"
    echo "  取得ファイル:"
    find "$RAW" -maxdepth 2 -type f -print | sed 's/^/    /'
    echo
    continue
  fi

  SHA="$(sha256_file "$MAIN")"
  echo "  ✅ main.py 保存: $MAIN"
  echo "  SHA: $SHA"

  if [ "$SHA" = "$E11_SHA" ]; then
    echo "  = E11と同一"
  else
    echo "  ≠ E11（比較候補）"
  fi
  echo
done

echo "=== 完了 ==="
echo "候補は $OUTROOT/ 以下にあります。"
echo
echo "この出力をそのままChatGPTに貼ってください。"
echo "次は存在した候補だけをE11と自動対戦させる1コマンドを作ります。"
