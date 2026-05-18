#!/bin/bash
# Ollama インストール・モデルダウンロード・動作確認スクリプト
# 費用: 無料（Ollama 本体 + オープンモデル）
# 動作環境: Linux / macOS（CPU のみでも動作）

set -e

echo "=== Ollama セットアップ ==="
echo ""

# ── 1. Ollama インストール ──────────────────────────────────
if command -v ollama &>/dev/null; then
  echo "[済] Ollama はすでにインストール済み: $(ollama --version 2>/dev/null || echo '不明')"
else
  echo "[1/3] Ollama をインストールします..."
  curl -fsSL https://ollama.com/install.sh | sh
  echo "  -> インストール完了"
fi

# ── 2. Ollama サーバー起動確認 ──────────────────────────────
echo ""
echo "[2/3] Ollama サーバーを起動します..."
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
  ollama serve &>/tmp/ollama.log &
  sleep 3
  echo "  -> サーバー起動完了 (http://localhost:11434)"
else
  echo "[済] Ollama サーバーはすでに起動中"
fi

# ── 3. モデルダウンロード ────────────────────────────────────
echo ""
echo "[3/3] モデルをダウンロードします..."
echo ""

MODEL="${1:-llama3.2:3b}"   # 引数で変更可能

echo "モデル選択肢:"
echo "  llama3.2:3b  … 約 2GB・CPU 動作・高速（デフォルト・PoC 推奨）"
echo "  qwen2.5:7b   … 約 4GB・日本語精度高め（GPU 推奨）"
echo "  gemma2:9b    … 約 5GB・バランス型（GPU 推奨）"
echo ""
echo "ダウンロード対象: ${MODEL}"
echo "(別モデルを使う場合: bash setup_ollama.sh qwen2.5:7b)"
echo ""

ollama pull "${MODEL}"

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. .env ファイルを作成:"
echo "     cp .env.example .env"
echo "     # ANALYZER_ENGINE=llm に変更"
echo ""
echo "  2. エンジン状態を確認:"
echo "     curl http://localhost:8000/health/engine"
echo ""
echo "  3. アプリを起動:"
echo "     bash start.sh"
