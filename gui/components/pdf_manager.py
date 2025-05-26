import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
from core import pdf_image_utils

class PDFManager:
    def __init__(self, parent, pdf_listbox, canvas, status_label):
        self.parent = parent
        self.pdf_listbox = pdf_listbox
        self.canvas = canvas
        self.status_label = status_label
        
        # 데이터 관리
        self.pdf_list = []          # 모든 PDF 파일 경로 목록
        self.current_pdf_idx = None # 현재 선택된 PDF 인덱스
        self.pdf_image = None       # 현재 PDF 이미지
        self.pdf_image_tk = None    # 현재 PDF 이미지의 Tkinter 버전
        self.pdf_original = None    # 원본 크기의 PDF 이미지

    def load_pdfs(self):
        """PDF 파일들을 불러옵니다 (복수 선택 가능)"""
        files = filedialog.askopenfilenames(filetypes=[('PDF Files', '*.pdf')])
        if not files:
            return
            
        # 목록 초기화 및 추가
        self.pdf_list = list(files)
        self.pdf_listbox.delete(0, tk.END)
        
        for pdf in self.pdf_list:
            self.pdf_listbox.insert(tk.END, os.path.basename(pdf))
            
        self.status_label.config(text=f'PDF {len(self.pdf_list)}개 불러옴')
        
        # 첫 번째 PDF 자동 선택
        if self.pdf_list:
            self.current_pdf_idx = 0
            self._load_current_pdf()
            
        return self.pdf_list, self.pdf_image, self.pdf_image_tk
    
    def on_pdf_select(self, event):
        """PDF 목록에서 항목 선택 시 호출됨"""
        idxs = self.pdf_listbox.curselection()
        if not idxs:
            return
            
        self.current_pdf_idx = idxs[0]
        self._load_current_pdf()
        
        return self.pdf_image, self.pdf_image_tk
    
    def show_pdf_context_menu(self, event, pdf_context_menu):
        """PDF 리스트박스에서 우클릭 시 컨텍스트 메뉴 표시"""
        try:
            # 클릭된 위치의 항목 선택
            clicked_index = self.pdf_listbox.nearest(event.y)
            if clicked_index >= 0:  # 유효한 인덱스인 경우
                self.pdf_listbox.selection_clear(0, tk.END)
                self.pdf_listbox.selection_set(clicked_index)
                self.pdf_listbox.activate(clicked_index)
                pdf_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            pdf_context_menu.grab_release()
    
    def delete_pdf(self):
        """선택된 PDF 항목 삭제"""
        selected = self.pdf_listbox.curselection()
        if not selected:
            return
            
        idx = selected[0]
        
        # 목록에서 삭제
        self.pdf_list.pop(idx)
        self.pdf_listbox.delete(idx)
        
        # 현재 선택된 PDF 재조정
        if self.pdf_list:
            if idx == self.current_pdf_idx:  # 삭제된 항목이 현재 선택된 항목이었다면
                # 가능하면 같은 인덱스, 아니면 마지막 항목 선택
                self.current_pdf_idx = min(idx, len(self.pdf_list) - 1)
                self.pdf_listbox.selection_set(self.current_pdf_idx)
                self._load_current_pdf()
            elif idx < self.current_pdf_idx:  # 삭제된 항목이 현재 선택된 항목보다 앞에 있었다면
                self.current_pdf_idx -= 1  # 인덱스 조정
        else:
            # PDF가 더 이상 없으면 캔버스 초기화
            self.current_pdf_idx = None
            self.pdf_image = None
            self.pdf_image_tk = None
            self.canvas.delete('all')
            self.status_label.config(text='PDF를 먼저 불러오세요')
            
        return self.pdf_image, self.pdf_image_tk, self.current_pdf_idx
    
    def _load_current_pdf(self):
        """현재 선택된 PDF를 로드하고 미리보기 표시"""
        if self.current_pdf_idx is None or self.current_pdf_idx >= len(self.pdf_list):
            return
            
        pdf_path = self.pdf_list[self.current_pdf_idx]
        self.pdf_original = pdf_image_utils.pdf_to_image(pdf_path, dpi=100)
        
        # 디스플레이 해상도의 85%로 제한
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        max_width = int(screen_width * 0.85)
        max_height = int(screen_height * 0.85)
        
        # 원본 이미지 크기
        img_width, img_height = self.pdf_original.size
        
        # 비율 유지하면서 크기 조정
        scale_ratio = min(max_width / img_width, max_height / img_height)
        if scale_ratio < 1:  # 이미지가 최대 크기보다 크면 축소
            new_width = int(img_width * scale_ratio)
            new_height = int(img_height * scale_ratio)
            self.pdf_image = self.pdf_original.resize((new_width, new_height), Image.LANCZOS)
        else:
            self.pdf_image = self.pdf_original.copy()
        
        self.pdf_image_tk = ImageTk.PhotoImage(self.pdf_image)
        
        self.canvas.config(width=self.pdf_image.width, height=self.pdf_image.height)
        self.status_label.config(text=f'PDF 로드됨: {os.path.basename(pdf_path)}')
        
        return self.pdf_image, self.pdf_image_tk 