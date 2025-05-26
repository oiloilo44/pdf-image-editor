import tkinter as tk
from gui.unified_pdf_editor import UnifiedPDFEditor

def main():
    root = tk.Tk()
    app = UnifiedPDFEditor(root)
    app.run()

if __name__ == '__main__':
    main() 