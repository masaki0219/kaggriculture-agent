#!/usr/bin/env bash
set -euo pipefail

KERNEL="prvsiyan/kaggriculture-frontier-the-moon-counts-melons"
WORK=".prvsiyan_latest"
E11="kaggriculture_elite_bundle_PATCHED_v2/public_agents/elite/prvsiyan_frontier/raw/main.py"
FALLBACK_E11_SHA="02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79"

echo "=== Kaggriculture: Prvsiyan最新版チェック ==="

if ! command -v kaggle >/dev/null 2>&1; then
  echo "❌ kaggle CLI が見つかりません。"
  echo "   先に: pip install kaggle"
  exit 1
fi

rm -rf "$WORK"
mkdir -p "$WORK/output" "$WORK/extracted"

echo "1/3 最新Notebook出力を取得中..."
kaggle kernels output "$KERNEL" -p "$WORK/output" -o >/dev/null

ARCHIVE="$(find "$WORK/output" -type f -name 'submission.tar.gz' | head -n 1 || true)"
if [ -z "$ARCHIVE" ]; then
  ARCHIVE="$(find "$WORK/output" -type f -name '*.tar.gz' | head -n 1 || true)"
fi

if [ -z "$ARCHIVE" ]; then
  echo "❌ submission.tar.gz が見つかりませんでした。"
  echo "取得されたファイル:"
  find "$WORK/output" -maxdepth 3 -type f -print
  exit 1
fi

echo "2/3 展開中..."
tar -xzf "$ARCHIVE" -C "$WORK/extracted"

LATEST_MAIN="$(find "$WORK/extracted" -type f -name 'main.py' | head -n 1 || true)"
if [ -z "$LATEST_MAIN" ]; then
  echo "❌ main.py が見つかりませんでした。"
  find "$WORK/extracted" -maxdepth 3 -type f -print
  exit 1
fi

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

LATEST_SHA="$(sha256_file "$LATEST_MAIN")"

if [ -f "$E11" ]; then
  E11_SHA="$(sha256_file "$E11")"
else
  E11_SHA="$FALLBACK_E11_SHA"
fi

echo "3/3 E11と比較..."
echo
echo "E11    : $E11_SHA"
echo "最新   : $LATEST_SHA"
echo

if [ "$LATEST_SHA" = "$E11_SHA" ]; then
  echo "✅ 同じです。E11が最新版と一致しています。"
  echo "👉 何もしなくてOK。E11を維持してください。"
  rm -rf "$WORK"
  exit 0
fi

mkdir -p "candidates/prvsiyan_latest"
cp "$LATEST_MAIN" "candidates/prvsiyan_latest/main.py"

echo "🆕 違います。新しい候補です。"
echo "👉 candidates/prvsiyan_latest/main.py に保存しました。"
echo
echo "次は E11 vs この候補の勝敗比較です。"
echo "この画面の出力をChatGPTに貼れば、次の1コマンドをこちらで出します。"
