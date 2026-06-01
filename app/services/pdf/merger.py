import os
from pypdf import PdfWriter, PdfReader


def merge_pdfs(base_path: str, append_path: str, output_path: str) -> str:
    writer = PdfWriter()
    for path in (base_path, append_path):
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path


def get_page_count(pdf_path: str) -> int:
    return len(PdfReader(pdf_path).pages)
