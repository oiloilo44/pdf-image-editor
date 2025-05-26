import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk

class ImageManager:
    def __init__(self, parent, img_listbox, canvas):
        self.parent = parent
        self.img_listbox = img_listbox
        self.canvas = canvas
        
        # 삽입된 이미지 정보
        self.inserted_images = []   # [{'path', 'pos', 'size', 'img', 'tk'}]
        self.selected_image_idx = None
        
        # 드래그 & 리사이징 상태 변수
        self.resizing = False
        self.moving = False
        self.resize_handle_size = 10
        self.moving_offset = (0, 0)

    def insert_image(self, pdf_list):
        """이미지 파일을 불러와 삽입"""
        if not pdf_list:
            messagebox.showerror('오류', 'PDF를 먼저 불러오세요.')
            return
            
        path = filedialog.askopenfilename(
            filetypes=[('Image Files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif')]
        )
        if not path:
            return
            
        img = Image.open(path).convert('RGBA')
        size = [min(100, img.width), min(100, img.height)]
        tk_img = ImageTk.PhotoImage(img.resize(size, Image.LANCZOS))
        pos = [50, 50]
        
        self.inserted_images.append({
            'path': path, 
            'pos': pos, 
            'size': size, 
            'img': img, 
            'tk': tk_img
        })
        
        self.img_listbox.insert(tk.END, os.path.basename(path))
        self.selected_image_idx = len(self.inserted_images) - 1
        
        return self.inserted_images, self.selected_image_idx
    
    def on_image_select(self, event):
        """이미지 목록에서 항목 선택 시 호출됨"""
        idxs = self.img_listbox.curselection()
        if idxs:
            self.selected_image_idx = idxs[0]
            return self.selected_image_idx
    
    def show_image_context_menu(self, event, img_context_menu):
        """이미지 리스트박스에서 우클릭 시 컨텍스트 메뉴 표시"""
        try:
            # 클릭된 위치의 항목 선택
            clicked_index = self.img_listbox.nearest(event.y)
            if clicked_index >= 0 and clicked_index < len(self.inserted_images):  # 유효한 인덱스인 경우
                self.img_listbox.selection_clear(0, tk.END)
                self.img_listbox.selection_set(clicked_index)
                self.img_listbox.activate(clicked_index)
                self.selected_image_idx = clicked_index
                img_context_menu.tk_popup(event.x_root, event.y_root)
                return self.selected_image_idx
        finally:
            img_context_menu.grab_release()
    
    def delete_image(self):
        """선택된 이미지 항목 삭제"""
        if self.selected_image_idx is None:
            return
            
        idx = self.selected_image_idx
        
        # 목록에서 삭제
        self.inserted_images.pop(idx)
        self.img_listbox.delete(idx)
        
        # 현재 선택된 이미지 재조정
        if self.inserted_images:
            # 가능하면 같은 인덱스, 아니면 마지막 항목 선택
            self.selected_image_idx = min(idx, len(self.inserted_images) - 1)
            self.img_listbox.selection_set(self.selected_image_idx)
        else:
            self.selected_image_idx = None
        
        return self.inserted_images, self.selected_image_idx
    
    def on_canvas_press(self, event, pdf_image):
        """캔버스 클릭 이벤트 처리"""
        if pdf_image is None:
            return
            
        # 삽입 이미지 역순(위에 그려진 것 우선)으로 클릭 판정
        for idx in reversed(range(len(self.inserted_images))):
            img = self.inserted_images[idx]
            x, y = img['pos']
            w, h = img['size']
            
            # 리사이즈 핸들 클릭
            if (x + w - self.resize_handle_size <= event.x <= x + w and
                y + h - self.resize_handle_size <= event.y <= y + h):
                self.selected_image_idx = idx
                self.resizing = True
                return self.selected_image_idx, self.resizing, self.moving
                
            # 이미지 내부 클릭(이동)
            elif x <= event.x <= x + w and y <= event.y <= y + h:
                self.selected_image_idx = idx
                self.moving = True
                self.moving_offset = (event.x - x, event.y - y)
                return self.selected_image_idx, self.resizing, self.moving, self.moving_offset
                
        self.selected_image_idx = None
        self.resizing = False
        self.moving = False
        return self.selected_image_idx, self.resizing, self.moving
    
    def on_canvas_drag(self, event):
        """캔버스 드래그 이벤트 처리"""
        if self.selected_image_idx is None:
            return
            
        img = self.inserted_images[self.selected_image_idx]
        
        if self.resizing:
            new_w = max(20, event.x - img['pos'][0])
            new_h = max(20, event.y - img['pos'][1])
            img['size'] = [new_w, new_h]
            img['tk'] = ImageTk.PhotoImage(img['img'].resize(img['size'], Image.LANCZOS))
            
        elif self.moving:
            offset_x, offset_y = getattr(self, 'moving_offset', (0, 0))
            new_x = event.x - offset_x
            new_y = event.y - offset_y
            img['pos'][0] = new_x
            img['pos'][1] = new_y
            
        return self.inserted_images
    
    def on_canvas_release(self, event):
        """캔버스 마우스 버튼 해제 이벤트 처리"""
        self.resizing = False
        self.moving = False
        return self.resizing, self.moving 