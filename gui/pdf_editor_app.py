import tkinter as tk
from tkinter import ttk, Menu
from gui.components import PDFManager, ImageManager, CanvasManager, SaveManager

class PDFEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('PDF 이미지 삽입 도구')
        self.root.configure(bg='#f0f0f0')
        
        # UI 구성
        self._build_ui()
        
        # 컴포넌트 초기화
        self.pdf_manager = PDFManager(self.root, self.pdf_listbox, self.canvas, self.status_label)
        self.image_manager = ImageManager(self.root, self.img_listbox, self.canvas)
        self.canvas_manager = CanvasManager(self.canvas)
        self.save_manager = SaveManager(self, self.status_label)  # self를 전달하여 pdf_manager에 접근 가능하게 함
        
        # 이벤트 바인딩
        self._bind_events()
    
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
        self.pdf_listbox = tk.Listbox(pdf_list_frame, width=30, yscrollcommand=pdf_scrollbar.set)
        self.pdf_listbox.pack(side='left', fill='both', expand=True)
        
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
        self.img_listbox = tk.Listbox(img_list_frame, width=30, yscrollcommand=img_scrollbar.set)
        self.img_listbox.pack(side='left', fill='both', expand=True)
        
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
    
    def _bind_events(self):
        # PDF 리스트박스 이벤트
        self.pdf_listbox.bind('<<ListboxSelect>>', self.on_pdf_select)
        self.pdf_listbox.bind('<Button-3>', self.show_pdf_context_menu)
        
        # 이미지 리스트박스 이벤트
        self.img_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        self.img_listbox.bind('<Button-3>', self.show_image_context_menu)
        
        # 캔버스 이벤트
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
    
    # PDF 관련 함수들
    def load_pdfs(self):
        pdf_list, pdf_image, pdf_image_tk = self.pdf_manager.load_pdfs()
        self._redraw_canvas()
    
    def on_pdf_select(self, event):
        pdf_image, pdf_image_tk = self.pdf_manager.on_pdf_select(event)
        self._redraw_canvas()
    
    def show_pdf_context_menu(self, event):
        self.pdf_manager.show_pdf_context_menu(event, self.pdf_context_menu)
    
    def delete_pdf(self):
        pdf_image, pdf_image_tk, current_pdf_idx = self.pdf_manager.delete_pdf()
        self._redraw_canvas()
    
    # 이미지 관련 함수들
    def insert_image(self):
        inserted_images, selected_image_idx = self.image_manager.insert_image(self.pdf_manager.pdf_list)
        self._redraw_canvas()
    
    def on_image_select(self, event):
        selected_image_idx = self.image_manager.on_image_select(event)
        self._redraw_canvas()
    
    def show_image_context_menu(self, event):
        selected_image_idx = self.image_manager.show_image_context_menu(event, self.img_context_menu)
        self._redraw_canvas()
    
    def delete_image(self):
        inserted_images, selected_image_idx = self.image_manager.delete_image()
        self._redraw_canvas()
    
    # 캔버스 관련 함수들
    def on_canvas_press(self, event):
        result = self.canvas_manager.on_canvas_press(event, self.image_manager, self.pdf_manager.pdf_image)
        self._redraw_canvas()
    
    def on_canvas_drag(self, event):
        inserted_images = self.canvas_manager.on_canvas_drag(event, self.image_manager)
        self._redraw_canvas()
    
    def on_canvas_release(self, event):
        self.canvas_manager.on_canvas_release(event, self.image_manager)
    
    def _redraw_canvas(self):
        self.canvas_manager._redraw_canvas(
            self.pdf_manager.pdf_image_tk, 
            self.image_manager.inserted_images, 
            self.image_manager.selected_image_idx
        )
    
    # 저장 관련 함수들
    def batch_save(self):
        self.save_manager.batch_save(
            self.pdf_manager.pdf_list, 
            self.image_manager.inserted_images
        )
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop() 