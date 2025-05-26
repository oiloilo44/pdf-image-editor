import tkinter as tk
from PIL import ImageTk

class CanvasManager:
    def __init__(self, canvas):
        self.canvas = canvas
        self.resize_handle_size = 10
    
    def _redraw_canvas(self, pdf_image_tk, inserted_images, selected_image_idx):
        """캔버스에 모든 요소 다시 그리기"""
        self.canvas.delete('all')
        
        # PDF 배경 이미지
        if pdf_image_tk:
            self.canvas.create_image(0, 0, anchor='nw', image=pdf_image_tk, tags='pdf_bg')
        
        # 삽입된 이미지들
        for idx, img in enumerate(inserted_images):
            x, y = img['pos']
            w, h = img['size']
            
            self.canvas.create_image(x, y, anchor='nw', image=img['tk'], tags='inserted')
            
            # 선택된 이미지는 파란색, 아닌 것은 회색 테두리
            border_color = '#4a86e8' if idx == selected_image_idx else '#aaaaaa'
            border_width = 2 if idx == selected_image_idx else 1
            
            self.canvas.create_rectangle(
                x, y, x+w, y+h, 
                outline=border_color, 
                width=border_width
            )
            
            # 리사이즈 핸들 (선택된 이미지만)
            if idx == selected_image_idx:
                self.canvas.create_rectangle(
                    x+w-self.resize_handle_size, y+h-self.resize_handle_size, 
                    x+w, y+h, 
                    fill=border_color
                )
    
    def on_canvas_press(self, event, image_manager, pdf_image):
        """캔버스 클릭 이벤트 처리"""
        return image_manager.on_canvas_press(event, pdf_image)
    
    def on_canvas_drag(self, event, image_manager):
        """캔버스 드래그 이벤트 처리"""
        inserted_images = image_manager.on_canvas_drag(event)
        return inserted_images
    
    def on_canvas_release(self, event, image_manager):
        """캔버스 마우스 버튼 해제 이벤트 처리"""
        return image_manager.on_canvas_release(event) 