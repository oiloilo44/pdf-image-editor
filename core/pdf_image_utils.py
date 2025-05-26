from PIL import Image
from pdf2image import convert_from_path
from .config import POPLER_PATH


def pdf_to_image(pdf_path, dpi=300):
    """PDF 파일을 이미지로 변환 (첫 페이지만)"""
    images = convert_from_path(pdf_path, poppler_path=POPLER_PATH, dpi=dpi)
    return images[0]


def insert_image_to_pdf(pdf_path, insert_infos, output_path, dpi=300):
    """PDF에 여러 이미지를 삽입하여 새 PDF로 저장
    insert_infos: [{ 'path': 이미지경로, 'pos': (x, y), 'size': (w, h) }, ...]
    """
    base_img = pdf_to_image(pdf_path, dpi).convert('RGBA')
    for info in insert_infos:
        img = Image.open(info['path']).convert('RGBA').resize(info['size'], Image.LANCZOS)
        base_img.paste(img, info['pos'], img)
    base_img = base_img.convert('RGB')
    base_img.save(output_path, 'PDF', resolution=dpi) 