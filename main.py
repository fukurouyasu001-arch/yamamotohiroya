#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.ocr_processor import OCRProcessor
from src.invoice_extractor import InvoiceExtractor
from src.excel_writer import ExcelWriter


def main():
    load_dotenv()

    input_folder = "input"
    output_folder = "output"

    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    pdf_files = list(Path(input_folder).glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_folder}/ folder.")
        print("Please place PDF files in the input/ folder and try again.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process.")

    ocr_processor = OCRProcessor()
    invoice_extractor = InvoiceExtractor()
    all_invoices = []

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        try:
            ocr_text = ocr_processor.process_pdf(str(pdf_path))
            print(f"OCR completed for {pdf_path.name}")

            invoices = invoice_extractor.extract_invoice_data(ocr_text)
            print(f"Extracted {len(invoices)} invoice(s)")

            for invoice in invoices:
                if invoice_extractor.validate_invoice(invoice):
                    formatted_invoice = invoice_extractor.format_invoice_for_output(invoice)
                    all_invoices.append(formatted_invoice)

        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
            continue

    if all_invoices:
        output_path = os.path.join(output_folder, "invoices.xlsx")
        excel_writer = ExcelWriter()
        excel_writer.process_and_save(all_invoices, output_path)
        print(f"\nProcessing complete! Total invoices extracted: {len(all_invoices)}")
    else:
        print("\nNo invoices could be extracted from the PDF files.")


if __name__ == "__main__":
    main()
