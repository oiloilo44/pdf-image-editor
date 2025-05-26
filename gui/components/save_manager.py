import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
from core import pdf_image_utils

class SaveManager:
    def __init__(self, parent, status_label):
        self.parent = parent
        self.status_label = status_label
    
    def batch_save(self, pdf_list, inserted_images):
        """모든 PDF에 삽입된 이미지 적용 후 일괄 저장"""
        if not pdf_list:
            messagebox.showerror('오류', 'PDF 파일을 먼저 불러오세요.')
            return
            
        if not inserted_images:
            messagebox.showerror('오류', '삽입할 이미지가 없습니다.')
            return
        
        # 저장 옵션 대화상자 표시
        save_options = self._show_save_options_dialog()
        if not save_options:
            return
            
        all_pages = save_options.get('all_pages', False)
        
        # 저장 폴더 선택
        save_dir = filedialog.askdirectory(title='저장할 폴더 선택')
        if not save_dir:
            return
        
        # root 객체 가져오기 (PDFEditorApp에서는 root 속성 사용)
        root = self.parent.root if hasattr(self.parent, 'root') else self.parent
        
        # 진행 상황 표시 대화상자 생성
        progress_dialog = tk.Toplevel(root)
        progress_dialog.title('저장 진행 중')
        progress_dialog.transient(root)
        progress_dialog.grab_set()
        progress_dialog.resizable(False, False)
        progress_dialog.geometry("400x150")
        
        # 대화상자 중앙 위치 설정
        progress_dialog.geometry("+%d+%d" % (
            root.winfo_rootx() + root.winfo_width() // 2 - 200,
            root.winfo_rooty() + root.winfo_height() // 2 - 75
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
        total_pdfs = len(pdf_list)
        progress_bar['maximum'] = total_pdfs
        
        # 각 PDF에 이미지 삽입 후 저장
        success_count = 0
        for index, pdf_path in enumerate(pdf_list):
            base_name = os.path.basename(pdf_path)
            save_path = os.path.join(save_dir, base_name.replace('.pdf', '_edited.pdf'))
            
            # 진행 상태 업데이트
            progress_label.config(text=f'PDF 저장 중... ({index+1}/{total_pdfs})')
            current_file_label.config(text=f'현재 파일: {base_name}')
            progress_bar['value'] = index
            progress_dialog.update()
            
            try:
                # 300 dpi 이미지 로드 (출력용)
                base_img = pdf_image_utils.pdf_to_image(pdf_path, dpi=300, page=0)
                output_w, output_h = base_img.size
                
                # 100 dpi 원본 이미지 로드 (미리보기 전 크기)
                orig_preview_img = pdf_image_utils.pdf_to_image(pdf_path, dpi=100, page=0)
                orig_preview_w, orig_preview_h = orig_preview_img.size
                
                # 현재 캔버스에 표시된 이미지 크기 얻기
                app = self.parent if hasattr(self.parent, 'pdf_manager') else None
                pdf_mgr = app.pdf_manager if app else None
                
                if pdf_mgr and pdf_mgr.pdf_image:
                    # 화면에 표시된 이미지 크기
                    display_w, display_h = pdf_mgr.pdf_image.size
                    
                    # dpi 변환 비율과 화면 맞춤 비율을 모두 고려
                    scale_x = output_w / display_w
                    scale_y = output_h / display_h
                else:
                    # pdf_manager를 얻을 수 없는 경우 기존 방식으로 계산
                    scale_x = output_w / orig_preview_w
                    scale_y = output_h / orig_preview_h
                
                # 삽입 정보 생성
                insert_infos = []
                for img in inserted_images:
                    x = int(img['pos'][0] * scale_x)
                    y = int(img['pos'][1] * scale_y)
                    w = int(img['size'][0] * scale_x)
                    h = int(img['size'][1] * scale_y)
                    insert_infos.append({
                        'path': img['path'], 
                        'pos': (x, y), 
                        'size': (w, h)
                    })
                
                pdf_image_utils.insert_image_to_pdf(pdf_path, insert_infos, save_path, dpi=300, all_pages=all_pages)
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
        self._show_completion_dialog(save_dir, success_count, total_pdfs)
        
        return success_count

    def _show_save_options_dialog(self):
        """저장 옵션을 선택하는 대화상자를 표시합니다."""
        # root 객체 가져오기
        root = self.parent.root if hasattr(self.parent, 'root') else self.parent
        
        options = {}
        dialog = tk.Toplevel(root)
        dialog.title('저장 옵션')
        dialog.transient(root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # 다이얼로그 중앙 위치 설정
        dialog.geometry("+%d+%d" % (
            root.winfo_rootx() + root.winfo_width() // 2 - 150,
            root.winfo_rooty() + root.winfo_height() // 2 - 75
        ))
        
        # 메인 프레임
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill='both', expand=True)
        
        # 체크박스 변수
        all_pages_var = tk.BooleanVar(value=False)
        
        # 체크박스
        ttk.Checkbutton(
            main_frame,
            text='다중 페이지 PDF의 모든 페이지에 이미지 삽입',
            variable=all_pages_var
        ).pack(anchor='w', padx=10, pady=10)
        
        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        # 취소 버튼
        ttk.Button(
            btn_frame,
            text='취소',
            command=dialog.destroy
        ).pack(side='right', padx=(10, 0))
        
        # 확인 버튼
        def on_ok():
            options['all_pages'] = all_pages_var.get()
            dialog.destroy()
            
        ttk.Button(
            btn_frame,
            text='확인',
            command=on_ok
        ).pack(side='right', padx=(0, 5))
        
        # ESC로 닫기
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # 대화상자를 모달로 표시
        dialog.wait_window()
        
        return options if options else None

    def _show_completion_dialog(self, save_dir, success_count, total_count):
        """저장 완료 다이얼로그를 표시하고 폴더 열기 버튼을 제공합니다."""
        # root 객체 가져오기
        root = self.parent.root if hasattr(self.parent, 'root') else self.parent
        
        dialog = tk.Toplevel(root)
        dialog.title('저장 완료')
        dialog.transient(root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # 다이얼로그 중앙 위치 설정
        dialog.geometry("+%d+%d" % (
            root.winfo_rootx() + root.winfo_width() // 2 - 150,
            root.winfo_rooty() + root.winfo_height() // 2 - 50
        ))
        
        # 메인 프레임
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill='both', expand=True)
        
        # 정보 레이블 - 왼쪽 정렬
        ttk.Label(
            main_frame, 
            text=f'전체 {total_count}개 중 {success_count}개 저장 완료\n저장 폴더: {save_dir}',
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