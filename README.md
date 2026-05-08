# 請求書OCR処理システム

会社の請求書・領収書をPDFからOCR処理して、月単位で整理したExcelファイルを自動生成します。

## 機能

- **PDF → OCR処理**: Google Cloud Vision APIで高精度なテキスト抽出
- **AI抽出**: Claude APIで構造化データを自動抽出
- **月単位整理**: 日付ごとに自動でシート分け
- **Excel出力**: 月ごとにシート分けされたExcelファイルを生成

## 抽出される情報

- 日付 (YYYY-MM-DD形式)
- 請求元 (会社名・個人名)
- 金額 (数値)
- 内容 (商品・サービス説明)
- 消費税率 (8% / 10%)
- インボイス番号 (適格請求書番号)

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Vision APIの設定

1. Google Cloudコンソールで新しいプロジェクトを作成
2. Vision APIを有効化
3. サービスアカウントキーをJSON形式でダウンロード
4. キーのパスを`.env`ファイルに設定

```bash
cp .env.example .env
# .envファイルを編集
# GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-cloud-key.json
```

### 3. Anthropic API Keyの設定

1. https://console.anthropic.com から API Keyを取得
2. `.env`ファイルに設定

```
ANTHROPIC_API_KEY=your-api-key-here
```

## 使用方法

### 1. PDFファイルの準備

`input/` フォルダにPDFファイルを置きます

```
input/
  ├── invoice_2026_04.pdf
  ├── invoice_2026_05.pdf
  └── receipt_2026_05.pdf
```

### 2. 処理実行

```bash
python main.py
```

### 3. 出力確認

処理完了後、`output/invoices.xlsx` に以下のような形式でExcelファイルが生成されます:

- **シート構成**: `2026-04`, `2026-05`, `未分類` など月ごとにシート分け
- **各シートの列**: 日付 | 請求元 | 金額 | 内容 | 消費税率 | インボイス番号

## ファイル構成

```
.
├── main.py                    # メインスクリプト
├── requirements.txt           # 依存ライブラリ
├── .env.example              # 環境変数テンプレート
├── README.md                 # このファイル
├── input/                    # 処理対象のPDFを配置
├── output/                   # 出力ファイルが保存される
└── src/
    ├── __init__.py
    ├── ocr_processor.py      # PDF → OCR処理
    ├── invoice_extractor.py  # テキスト → 構造化データ抽出
    └── excel_writer.py       # Excel出力
```

## トラブルシューティング

### Google Cloud Vision APIエラー

```
Error: 403 Permission denied: User is not authorized
```

**解決方法:**
- サービスアカウントキーのパスが正しいか確認
- `GOOGLE_APPLICATION_CREDENTIALS` 環境変数が正しく設定されているか確認

### Anthropic API エラー

```
Error: 401 Unauthorized
```

**解決方法:**
- APIキーが正しいか確認
- `.env`ファイルで `ANTHROPIC_API_KEY` が正しく設定されているか確認

### PDFが見つからない

```
No PDF files found in input/ folder.
```

**解決方法:**
- `input/` フォルダが存在するか確認
- PDFファイルが `.pdf` の小文字拡張子になっているか確認

## パフォーマンス最適化

大量の請求書を処理する場合:

1. **バッチ処理**: `main.py`を複数回実行（月ごとに分割）
2. **キャッシング**: 同じPDFの再処理を避ける
3. **並列処理**: 複数のPDFを同時処理（将来の改善予定）

## 注意事項

- OCR精度はPDFの品質に依存します
- スキャンされた請求書は認識精度が高いです
- デジタルPDFでも抽出精度は十分です
- 手書き部分は認識精度が低下する可能性があります

## ライセンス

MIT License

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
