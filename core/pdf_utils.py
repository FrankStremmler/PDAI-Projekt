import os
import fitz
from PIL import Image
from io import BytesIO


def convert_pdf_to_jpg(pdf_path: str, dpi: int = 200, quality: int = 85) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    pdf_document = fitz.open(pdf_path)
    pages_images = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pixmap = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        pages_images.append(img)

    pdf_document.close()

    total_height = sum(img.height for img in pages_images)
    max_width = max(img.width for img in pages_images)

    stacked_image = Image.new("RGB", (max_width, total_height), (255, 255, 255))

    y_offset = 0
    for img in pages_images:
        x_offset = (max_width - img.width) // 2
        stacked_image.paste(img, (x_offset, y_offset))
        y_offset += img.height

    base, _ = os.path.splitext(pdf_path)
    output_path = f"{base}_converted.jpg"
    stacked_image.save(output_path, "JPEG", quality=quality)

    print(f"[PDF] Konvertiert: {pdf_path} -> {output_path} ({len(pages_images)} Seiten, {dpi} DPI)")
    return output_path


def pdf_to_jpeg_bytes(pdf_path: str, dpi: int = 200) -> list[bytes]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    doc = fitz.open(pdf_path)
    images: list[bytes] = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("jpeg"))
    doc.close()
    return images
