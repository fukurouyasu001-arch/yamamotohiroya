import os
from pathlib import Path
from pdf2image import convert_from_path
from google.cloud import vision
from PIL import Image
import io


class OCRProcessor:
    def __init__(self):
        self.vision_client = vision.ImageAnnotatorClient()

    def pdf_to_images(self, pdf_path: str) -> list:
        """Convert PDF to images."""
        images = convert_from_path(pdf_path, dpi=300)
        return images

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using Google Cloud Vision API."""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        image_obj = vision.Image(content=img_byte_arr.getvalue())
        response = self.vision_client.document_text_detection(image=image_obj)

        extracted_text = response.full_text_annotation.text
        return extracted_text

    def process_pdf(self, pdf_path: str) -> str:
        """Process PDF and extract all text."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        images = self.pdf_to_images(pdf_path)
        all_text = ""

        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            text = self.extract_text_from_image(image)
            all_text += f"\n--- Page {i+1} ---\n{text}"

        return all_text
