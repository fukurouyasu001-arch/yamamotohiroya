# 請求書OCR処理システム - 開発ガイド

## プロジェクト概要

このプロジェクトは、PDFの請求書・領収書を自動でOCR処理し、構造化データとしてExcelファイルに月単位で整理するシステムです。

## 技術スタック

- **言語**: Python 3.8+
- **OCR**: Google Cloud Vision API
- **データ抽出**: Anthropic Claude API
- **Excel出力**: openpyxl
- **PDF処理**: pdf2image, Pillow

## ディレクトリ構成

```
.
├── main.py                      # エントリーポイント
├── requirements.txt             # Python依存パッケージ
├── .env.example                 # 環境変数テンプレート
├── README.md                    # ユーザー向けドキュメント
├── CLAUDE.md                    # このファイル
├── input/                       # 入力PDF格納フォルダ
├── output/                      # 出力Excel格納フォルダ
└── src/
    ├── __init__.py
    ├── ocr_processor.py         # PDF → OCR処理
    ├── invoice_extractor.py     # OCRテキスト → 構造化データ
    └── excel_writer.py          # Excel生成・フォーマッティング
```

## セットアップ手順

1. リポジトリをクローン
2. Python仮想環境を作成: `python -m venv venv`
3. 仮想環境を有効化: `source venv/bin/activate` (Linux/Mac) または `venv\Scripts\activate` (Windows)
4. 依存パッケージをインストール: `pip install -r requirements.txt`
5. `.env.example`をコピーして`.env`を作成
6. Google Cloud Vision APIキーと Anthropic APIキーを設定

## 開発ガイドライン

### コードスタイル

- PEP 8に従う
- 関数の型ヒントを使用
- docstringは簡潔に

### モジュール責務

**ocr_processor.py**
- PDF をImageオブジェクトに変換
- Google Cloud Vision API を使用してOCR実行
- テキストの抽出と返却

**invoice_extractor.py**
- OCRテキストをClaudeに送信
- JSONレスポンスをパース
- 抽出データの検証とフォーマット
- 金額などの数値の正規化

**excel_writer.py**
- 抽出データを月ごとに分類
- Excelワークブックの生成
- ヘッダー、フォーマット、列幅の設定
- ファイルの保存

### 環境変数

| 変数 | 説明 | 例 |
|------|------|-----|
| `GOOGLE_APPLICATION_CREDENTIALS` | Google Cloud認証キーのパス | `path/to/key.json` |
| `ANTHROPIC_API_KEY` | Anthropic APIキー | `sk-...` |

### 拡張時の注意点

- **複数ページ対応**: 各PDFページを個別に処理して結合している
- **多言語対応**: Google Cloud Vision APIは自動で言語検出する
- **エラーハンドリング**: 各モジュールでtry-exceptを使用して個別処理を継続
- **パフォーマンス**: 大量ファイル処理時は並列処理の導入を検討

## テスト方法

```bash
# サンプルPDF で動作確認
cp sample.pdf input/
python main.py
```

## 今後の拡張予定

- [ ] 複数ファイルの並列処理
- [ ] Webインターフェース（FastAPI）
- [ ] Google Driveとの連携
- [ ] データベース保存オプション
- [ ] より詳細な請求書分類
- [ ] 税務レポート自動生成

## トラブルシューティング

### APIキーエラー

Google Cloud認証:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

Anthropic API:
```bash
export ANTHROPIC_API_KEY="your-key"
```

### 依存パッケージのアップデート

```bash
pip install -r requirements.txt --upgrade
```

## デバッグモード

詳細ログを有効にする場合は、各モジュールの `print` 文を有効にしてください。

## パフォーマンス考慮事項

- OCR処理（1ページあたり1-3秒）
- Claude APIレスポンス（1請求書あたり1-2秒）
- 大量ファイル処理時はバッチ処理を推奨

## セキュリティ

- `.env`ファイルに認証キーを保存（Gitにコミットしない）
- `*.json`（Google Cloud credentials）もGitにコミットしない
- 本番環境ではシークレット管理ツール（例：AWS Secrets Manager）の使用を推奨

## 参考リンク

- [Google Cloud Vision API ドキュメント](https://cloud.google.com/vision/docs)
- [Anthropic Claude API ドキュメント](https://docs.anthropic.com)
- [openpyxl ドキュメント](https://openpyxl.readthedocs.io)
