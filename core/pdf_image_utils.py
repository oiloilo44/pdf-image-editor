from PIL import Image
from pdf2image import convert_from_path
from .config import POPLER_PATH
import PyPDF2
import io


def pdf_to_image(pdf_path, dpi=300, page=0):
    """PDF 파일을 이미지로 변환
    
    Args:
        pdf_path: PDF 파일 경로
        dpi: 해상도
        page: 특정 페이지만 반환할 경우 페이지 번호 (0부터 시작), -1이면 모든 페이지 반환
    
    Returns:
        page >= 0 이면 해당 페이지의 이미지, page < 0 이면 모든 페이지의 이미지 리스트
    """
    images = convert_from_path(pdf_path, poppler_path=POPLER_PATH, dpi=dpi)
    if page >= 0 and page < len(images):
        return images[page]
    return images


def get_pdf_page_count(pdf_path):
    """PDF 파일의 전체 페이지 수를 반환"""
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        return len(pdf.pages)


def insert_image_to_pdf(pdf_path, insert_infos, output_path, dpi=300, all_pages=False):
    """PDF에 여러 이미지를 삽입하여 새 PDF로 저장
    
    Args:
        pdf_path: PDF 파일 경로
        insert_infos: [{ 'path': 이미지경로, 'pos': (x, y), 'size': (w, h) }, ...]
        output_path: 출력 PDF 파일 경로
        dpi: 해상도
        all_pages: True이면 모든 페이지에 이미지 삽입, False이면 첫 페이지에만 삽입
    """
    if not all_pages:
        # 기존 방식: 첫 페이지에만 이미지 삽입
        base_img = pdf_to_image(pdf_path, dpi, 0).convert('RGBA')
        for info in insert_infos:
            img = Image.open(info['path']).convert('RGBA').resize(info['size'], Image.LANCZOS)
            base_img.paste(img, info['pos'], img)
        base_img = base_img.convert('RGB')
        base_img.save(output_path, 'PDF', resolution=dpi)
    else:
        # 모든 페이지에 이미지 삽입
        images = pdf_to_image(pdf_path, dpi, -1)
        output_images = []
        
        for base_img in images:
            base_img = base_img.convert('RGBA')
            for info in insert_infos:
                img = Image.open(info['path']).convert('RGBA').resize(info['size'], Image.LANCZOS)
                base_img.paste(img, info['pos'], img)
            output_images.append(base_img.convert('RGB'))
        
        # 첫 번째 이미지를 저장하고 나머지 이미지를 append
        if output_images:
            output_images[0].save(output_path, 'PDF', resolution=dpi, 
                                save_all=True, append_images=output_images[1:]) 