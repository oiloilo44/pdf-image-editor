import tkinter as tk
from gui import PDFEditorApp

def main():
    root = tk.Tk()
    app = PDFEditorApp(root)
    app.run()

if __name__ == '__main__':
    main() 