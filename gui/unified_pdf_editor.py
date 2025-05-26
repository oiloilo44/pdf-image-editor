import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, ttk, Menu
from PIL import Image, ImageTk
import os
import subprocess
from core import pdf_image_utils

class UnifiedPDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title('PDF 이미지 삽입 도구')
        self.root.configure(bg='#f0f0f0')
        
        # 데이터 관리
        self.pdf_list = []          # 모든 PDF 파일 경로 목록
        self.current_pdf_idx = None # 현재 선택된 PDF 인덱스
        self.pdf_image = None       # 현재 PDF 이미지
        self.pdf_image_tk = None    # 현재 PDF 이미지의 Tkinter 버전
        self.pdf_original = None    # 원본 크기의 PDF 이미지
        
        # 삽입된 이미지 정보
        self.inserted_images = []   # [{'path', 'pos', 'size', 'img', 'tk'}]
        self.selected_image_idx = None
        
        # 드래그 & 리사이징 상태 변수
        self.resizing = False
        self.moving = False
        self.resize_handle_size = 10
        
        # UI 구성
        self._build_ui()
    
    def _build_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # 상단 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text='PDF 불러오기', command=self.load_pdfs).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='이미지 불러오기', command=self.insert_image).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='일괄 저장', command=self.batch_save).pack(side='left', padx=5)
        
        self.status_label = ttk.Label(btn_frame, text='PDF를 먼저 불러오세요')
        self.status_label.pack(side='left', padx=10)
        
        # 메인 컨텐츠 프레임
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 좌측: PDF 목록
        left_frame = ttk.LabelFrame(content_frame, text='PDF 목록')
        left_frame.pack(side='left', fill='y', padx=(0, 10), pady=5)
        
        # PDF 리스트박스와 스크롤바를 포함할 프레임
        pdf_list_frame = ttk.Frame(left_frame)
        pdf_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 스크롤바 먼저 생성 및 배치
        pdf_scrollbar = ttk.Scrollbar(pdf_list_frame)
        pdf_scrollbar.pack(side='right', fill='y')
        
        # 리스트박스 생성 및 스크롤바 연결
        self.pdf_listbox = Listbox(pdf_list_frame, width=30, yscrollcommand=pdf_scrollbar.set)
        self.pdf_listbox.pack(side='left', fill='both', expand=True)
        self.pdf_listbox.bind('<<ListboxSelect>>', self.on_pdf_select)
        self.pdf_listbox.bind('<Button-3>', self.show_pdf_context_menu)
        
        # PDF 컨텍스트 메뉴 생성
        self.pdf_context_menu = Menu(self.root, tearoff=0)
        self.pdf_context_menu.add_command(label="삭제", command=self.delete_pdf)
        
        # 스크롤바에 리스트박스 연결
        pdf_scrollbar.config(command=self.pdf_listbox.yview)
        
        # 중앙: 이미지 목록
        middle_frame = ttk.LabelFrame(content_frame, text='삽입된 이미지 목록')
        middle_frame.pack(side='left', fill='y', padx=(0, 10), pady=5)
        
        # 이미지 리스트박스와 스크롤바를 포함할 프레임
        img_list_frame = ttk.Frame(middle_frame)
        img_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 스크롤바 먼저 생성 및 배치
        img_scrollbar = ttk.Scrollbar(img_list_frame)
        img_scrollbar.pack(side='right', fill='y')
        
        # 리스트박스 생성 및 스크롤바 연결
        self.img_listbox = Listbox(img_list_frame, width=30, yscrollcommand=img_scrollbar.set)
        self.img_listbox.pack(side='left', fill='both', expand=True)
        self.img_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        self.img_listbox.bind('<Button-3>', self.show_image_context_menu)
        
        # 이미지 컨텍스트 메뉴 생성
        self.img_context_menu = Menu(self.root, tearoff=0)
        self.img_context_menu.add_command(label="삭제", command=self.delete_image)
        
        # 스크롤바에 리스트박스 연결
        img_scrollbar.config(command=self.img_listbox.yview)
        
        # 우측: PDF 미리보기 캔버스
        right_frame = ttk.LabelFrame(content_frame, text='PDF 미리보기')
        right_frame.pack(side='left', fill='both', expand=True, padx=0, pady=5)
        
        # 캔버스 프레임
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, width=800, height=600, bg='#e0e0e0', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # 캔버스 이벤트 바인딩
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

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
    
    def on_pdf_select(self, event):
        """PDF 목록에서 항목 선택 시 호출됨"""
        idxs = self.pdf_listbox.curselection()
        if not idxs:
            return
            
        self.current_pdf_idx = idxs[0]
        self._load_current_pdf()
    
    def show_pdf_context_menu(self, event):
        """PDF 리스트박스에서 우클릭 시 컨텍스트 메뉴 표시"""
        try:
            # 클릭된 위치의 항목 선택
            clicked_index = self.pdf_listbox.nearest(event.y)
            if clicked_index >= 0:  # 유효한 인덱스인 경우
                self.pdf_listbox.selection_clear(0, tk.END)
                self.pdf_listbox.selection_set(clicked_index)
                self.pdf_listbox.activate(clicked_index)
                self.pdf_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.pdf_context_menu.grab_release()
    
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
    
    def _load_current_pdf(self):
        """현재 선택된 PDF를 로드하고 미리보기 표시"""
        if self.current_pdf_idx is None or self.current_pdf_idx >= len(self.pdf_list):
            return
            
        pdf_path = self.pdf_list[self.current_pdf_idx]
        self.pdf_original = pdf_image_utils.pdf_to_image(pdf_path, dpi=100)
        
        # 디스플레이 해상도의 85%로 제한
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
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
        self._redraw_canvas()
        self.status_label.config(text=f'PDF 로드됨: {os.path.basename(pdf_path)}')
    
    def insert_image(self):
        """이미지 파일을 불러와 삽입"""
        if not self.pdf_list:
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
        self._redraw_canvas()
    
    def on_image_select(self, event):
        """이미지 목록에서 항목 선택 시 호출됨"""
        idxs = self.img_listbox.curselection()
        if idxs:
            self.selected_image_idx = idxs[0]
            self._redraw_canvas()
    
    def show_image_context_menu(self, event):
        """이미지 리스트박스에서 우클릭 시 컨텍스트 메뉴 표시"""
        try:
            # 클릭된 위치의 항목 선택
            clicked_index = self.img_listbox.nearest(event.y)
            if clicked_index >= 0 and clicked_index < len(self.inserted_images):  # 유효한 인덱스인 경우
                self.img_listbox.selection_clear(0, tk.END)
                self.img_listbox.selection_set(clicked_index)
                self.img_listbox.activate(clicked_index)
                self.selected_image_idx = clicked_index
                self._redraw_canvas()
                self.img_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.img_context_menu.grab_release()
    
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
        
        self._redraw_canvas()
    
    def on_canvas_press(self, event):
        """캔버스 클릭 이벤트 처리"""
        if self.pdf_image is None:
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
                self._redraw_canvas()
                return
                
            # 이미지 내부 클릭(이동)
            elif x <= event.x <= x + w and y <= event.y <= y + h:
                self.selected_image_idx = idx
                self.moving = True
                self.moving_offset = (event.x - x, event.y - y)
                self._redraw_canvas()
                return
                
        self.selected_image_idx = None
        self.resizing = False
        self.moving = False
        self._redraw_canvas()
    
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
            self._redraw_canvas()
            
        elif self.moving:
            offset_x, offset_y = getattr(self, 'moving_offset', (0, 0))
            new_x = event.x - offset_x
            new_y = event.y - offset_y
            img['pos'][0] = new_x
            img['pos'][1] = new_y
            self._redraw_canvas()
    
    def on_canvas_release(self, event):
        """캔버스 마우스 버튼 해제 이벤트 처리"""
        self.resizing = False
        self.moving = False
    
    def _redraw_canvas(self):
        """캔버스에 모든 요소 다시 그리기"""
        self.canvas.delete('all')
        
        # PDF 배경 이미지
        if self.pdf_image_tk:
            self.canvas.create_image(0, 0, anchor='nw', image=self.pdf_image_tk, tags='pdf_bg')
        
        # 삽입된 이미지들
        for idx, img in enumerate(self.inserted_images):
            x, y = img['pos']
            w, h = img['size']
            
            self.canvas.create_image(x, y, anchor='nw', image=img['tk'], tags='inserted')
            
            # 선택된 이미지는 파란색, 아닌 것은 회색 테두리
            border_color = '#4a86e8' if idx == self.selected_image_idx else '#aaaaaa'
            border_width = 2 if idx == self.selected_image_idx else 1
            
            self.canvas.create_rectangle(
                x, y, x+w, y+h, 
                outline=border_color, 
                width=border_width
            )
            
            # 리사이즈 핸들 (선택된 이미지만)
            if idx == self.selected_image_idx:
                self.canvas.create_rectangle(
                    x+w-self.resize_handle_size, y+h-self.resize_handle_size, 
                    x+w, y+h, 
                    fill=border_color
                )
    
    def batch_save(self):
        """모든 PDF에 삽입된 이미지 적용 후 일괄 저장"""
        if not self.pdf_list:
            messagebox.showerror('오류', 'PDF 파일을 먼저 불러오세요.')
            return
            
        if not self.inserted_images:
            messagebox.showerror('오류', '삽입할 이미지가 없습니다.')
            return
        
        # 저장 폴더 선택
        save_dir = filedialog.askdirectory(title='저장할 폴더 선택')
        if not save_dir:
            return
        
        # 현재 미리보기 해상도와 실제 PDF 해상도 비율 계산
        pdf_path = self.pdf_list[self.current_pdf_idx]
        base_img = pdf_image_utils.pdf_to_image(pdf_path, dpi=300)
        base_w, base_h = base_img.size
        preview_w, preview_h = self.pdf_image.width, self.pdf_image.height
        scale_x = base_w / preview_w
        scale_y = base_h / preview_h
        
        # 삽입 정보 생성
        insert_infos = []
        for img in self.inserted_images:
            x = int(img['pos'][0] * scale_x)
            y = int(img['pos'][1] * scale_y)
            w = int(img['size'][0] * scale_x)
            h = int(img['size'][1] * scale_y)
            insert_infos.append({
                'path': img['path'], 
                'pos': (x, y), 
                'size': (w, h)
            })
        
        # 진행 상황 표시 대화상자 생성
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title('저장 진행 중')
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        progress_dialog.resizable(False, False)
        progress_dialog.geometry("400x150")
        
        # 대화상자 중앙 위치 설정
        progress_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + self.root.winfo_width() // 2 - 200,
            self.root.winfo_rooty() + self.root.winfo_height() // 2 - 75
        ))
        
        # 메인 프레임
        progress_frame = ttk.Frame(progress_dialog, padding=15)
        progress_frame.pack(fill='both', expand=True)
        
        # 진행 상태 레이블
        progress_label = ttk.Label(
            progress_frame, 
            text=f'PDF 저장 준비 중...',
            justify='center'
        )
        progress_label.pack(pady=(0, 10))
        
        # 현재 파일 레이블
        current_file_label = ttk.Label(
            progress_frame, 
            text='',
            justify='center'
        )
        current_file_label.pack(pady=(0, 10))
        
        # 진행 바
        progress_bar = ttk.Progressbar(
            progress_frame, 
            orient='horizontal', 
            length=350, 
            mode='determinate'
        )
        progress_bar.pack(fill='x', pady=(0, 10))
        
        # 취소 버튼
        cancel_button = ttk.Button(
            progress_frame, 
            text='취소', 
            command=progress_dialog.destroy
        )
        cancel_button.pack()
        
        # 대화상자 업데이트 및 초기화
        progress_dialog.update()
        total_pdfs = len(self.pdf_list)
        progress_bar['maximum'] = total_pdfs
        
        # 각 PDF에 이미지 삽입 후 저장
        success_count = 0
        for index, pdf_path in enumerate(self.pdf_list):
            base_name = os.path.basename(pdf_path)
            save_path = os.path.join(save_dir, base_name.replace('.pdf', '_edited.pdf'))
            
            # 진행 상태 업데이트
            progress_label.config(text=f'PDF 저장 중... ({index+1}/{total_pdfs})')
            current_file_label.config(text=f'현재 파일: {base_name}')
            progress_bar['value'] = index
            progress_dialog.update()
            
            try:
                pdf_image_utils.insert_image_to_pdf(pdf_path, insert_infos, save_path, dpi=300)
                success_count += 1
            except Exception as e:
                messagebox.showerror('오류', f'{base_name} 저장 중 오류 발생: {str(e)}')
            
            # 사용자가 대화상자를 닫았는지 확인
            if not progress_dialog.winfo_exists():
                break
        
        # 진행 대화상자 닫기
        if progress_dialog.winfo_exists():
            progress_dialog.destroy()
        
        self.status_label.config(text=f'PDF {success_count}개 저장 완료')
        
        # 커스텀 메시지 박스 생성
        self._show_completion_dialog(save_dir, success_count)

    def _show_completion_dialog(self, save_dir, success_count):
        """저장 완료 다이얼로그를 표시하고 폴더 열기 버튼을 제공합니다."""
        dialog = tk.Toplevel(self.root)
        dialog.title('저장 완료')
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # 다이얼로그 중앙 위치 설정
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + self.root.winfo_width() // 2 - 150,
            self.root.winfo_rooty() + self.root.winfo_height() // 2 - 50
        ))
        
        # 메인 프레임
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill='both', expand=True)
        
        # 정보 레이블 - 왼쪽 정렬
        ttk.Label(
            main_frame, 
            text=f'전체 {len(self.pdf_list)}개 중 {success_count}개 저장 완료\n저장 폴더: {save_dir}',
            justify='left'
        ).pack(anchor='w', padx=10, pady=10)
        
        # 버튼 프레임 - 오른쪽 정렬
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        # 확인 버튼 - 오른쪽에 배치
        ttk.Button(
            btn_frame, 
            text='확인', 
            command=dialog.destroy
        ).pack(side='right', padx=(10, 0))
        
        # 폴더 열기 버튼 - 확인 버튼 왼쪽에 배치
        ttk.Button(
            btn_frame, 
            text='폴더 열기', 
            command=lambda: self._open_folder(save_dir)
        ).pack(side='right', padx=(0, 5))
        
        # ESC로 닫기
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # 대화상자를 모달로 표시
        dialog.wait_window()
    
    def _open_folder(self, folder_path):
        """OS에 맞게 폴더 열기"""
        if os.name == 'nt':  # Windows
            os.startfile(folder_path)
        elif os.name == 'posix':  # macOS 또는 Linux
            try:
                # macOS
                subprocess.call(['open', folder_path])
            except:
                try:
                    # Linux
                    subprocess.call(['xdg-open', folder_path])
                except:
                    messagebox.showerror('오류', '폴더를 열 수 없습니다.')

    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()

if __name__ == '__main__':
    root = tk.Tk()
    app = UnifiedPDFEditor(root)
    app.run() 