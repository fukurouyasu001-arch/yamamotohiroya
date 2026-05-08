#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== 依存パッケージ確認・インストール ==="
pip install -r requirements.txt -q

echo "=== サーバー起動 ==="
echo "URL: http://localhost:8000"
echo "API ドキュメント: http://localhost:8000/docs"
echo "終了するには Ctrl+C を押してください"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
