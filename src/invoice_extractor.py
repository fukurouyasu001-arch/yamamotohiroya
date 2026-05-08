import re
from datetime import datetime
from typing import Dict, List, Optional
from anthropic import Anthropic


class InvoiceExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key)

    def extract_invoice_data(self, ocr_text: str) -> List[Dict]:
        """
        Extract invoice data from OCR text using Claude.
        Returns list of invoices with fields: 日付, 請求元, 金額, 内容, 消費税率, インボイス番号
        """
        prompt = """
以下のOCRテキストから請求書情報を抽出してください。

抽出対象フィールド（存在しない場合は「未記載」と記載）:
1. 日付 (YYYY-MM-DD形式, 不明な場合は最も近い日付を推測)
2. 請求元 (会社名または個人名)
3. 金額 (数値のみ, カンマなし)
4. 内容 (商品・サービスの説明)
5. 消費税率 (8% または 10%)
6. インボイス番号 (T+13桁の数字, 存在しない場合は「未記載」)

複数の請求書が含まれる場合は、すべて抽出してください。

JSON形式で以下の形式で返してください:
[
  {
    "日付": "YYYY-MM-DD",
    "請求元": "...",
    "金額": "...",
    "内容": "...",
    "消費税率": "...",
    "インボイス番号": "..."
  }
]

OCRテキスト:
{ocr_text}
"""

        message = self.client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = message.content[0].text

        invoices = self._parse_json_response(response_text)
        return invoices

    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """Parse JSON response from Claude."""
        try:
            import json
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group(0)
                invoices = json.loads(json_str)
                return invoices
        except (json.JSONDecodeError, AttributeError):
            pass

        return []

    def validate_invoice(self, invoice: Dict) -> bool:
        """Validate extracted invoice data."""
        required_fields = ['日付', '請求元', '金額', '内容', '消費税率', 'インボイス番号']
        return all(field in invoice for field in required_fields)

    def format_invoice_for_output(self, invoice: Dict) -> Dict:
        """Format invoice data for Excel output."""
        return {
            '日付': invoice.get('日付', ''),
            '請求元': invoice.get('請求元', ''),
            '金額': self._parse_amount(invoice.get('金額', '0')),
            '内容': invoice.get('内容', ''),
            '消費税率': invoice.get('消費税率', ''),
            'インボイス番号': invoice.get('インボイス番号', '')
        }

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float."""
        try:
            amount_str = str(amount_str).replace(',', '').replace('円', '').strip()
            return float(amount_str)
        except ValueError:
            return 0.0
