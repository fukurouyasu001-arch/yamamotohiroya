import os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


class ExcelWriter:
    def __init__(self, existing_file_path: str = None):
        if existing_file_path and os.path.exists(existing_file_path):
            self.workbook = load_workbook(existing_file_path)
            if self.workbook.sheetnames and self.workbook.sheetnames[0] == 'Sheet':
                self.workbook.remove(self.workbook.active)
            print(f"既存ファイルを開きました: {existing_file_path}")
        else:
            self.workbook = Workbook()
            self.workbook.remove(self.workbook.active)

    def organize_by_month(self, invoices: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize invoices by month (YYYY-MM)."""
        monthly_invoices = defaultdict(list)

        for invoice in invoices:
            try:
                date_str = invoice.get('日付', '')
                if date_str and date_str != '未記載':
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    month_key = date_obj.strftime('%Y-%m')
                else:
                    month_key = '未分類'
            except ValueError:
                month_key = '未分類'

            monthly_invoices[month_key].append(invoice)

        return monthly_invoices

    def add_month_sheet(self, month: str, invoices: List[Dict]):
        """Add a worksheet for a month with invoice data."""
        if month in self.workbook.sheetnames:
            del self.workbook[month]
            print(f"既存シート '{month}' を削除しました")

        worksheet = self.workbook.create_sheet(title=month)

        headers = ['日付', '請求元', '金額', '内容', '消費税率', 'インボイス番号']
        self._write_headers(worksheet, headers)

        for row_idx, invoice in enumerate(invoices, start=2):
            self._write_invoice_row(worksheet, row_idx, invoice, headers)

        self._format_worksheet(worksheet, len(invoices))

    def _write_headers(self, worksheet, headers):
        """Write header row."""
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for col_idx, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

    def _write_invoice_row(self, worksheet, row_idx: int, invoice: Dict, headers: List[str]):
        """Write invoice data row."""
        for col_idx, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=row_idx, column=col_idx)
            cell.value = invoice.get(header, '')

            if header == '金額':
                cell.number_format = '#,##0'

            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def _format_worksheet(self, worksheet, num_invoices: int):
        """Format worksheet with borders and auto-width columns."""
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for row in worksheet.iter_rows(min_row=1, max_row=num_invoices+1, min_col=1, max_col=6):
            for cell in row:
                cell.border = thin_border

        column_widths = {
            'A': 12,
            'B': 20,
            'C': 15,
            'D': 30,
            'E': 12,
            'F': 20
        }

        for col_letter, width in column_widths.items():
            worksheet.column_dimensions[col_letter].width = width

    def save(self, output_path: str):
        """Save workbook to file."""
        self.workbook.save(output_path)
        print(f"Excel file saved: {output_path}")

    def process_and_save(self, invoices: List[Dict], output_path: str):
        """Process invoices and save to Excel."""
        monthly_invoices = self.organize_by_month(invoices)

        for month in sorted(monthly_invoices.keys()):
            self.add_month_sheet(month, monthly_invoices[month])

        self.save(output_path)
