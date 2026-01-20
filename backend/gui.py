import os
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import scrolledtext, messagebox
import uvicorn
import warnings
from app.main import app

# Suppress warnings for cleaner logs
warnings.filterwarnings("ignore")

VERSION = "1.1.0"

# Handle PyInstaller paths
if getattr(sys, 'frozen', False):
    sys.path.append(sys._MEIPASS)

class LogRedirector:
    """Redirects stdout/stderr to a Tkinter ScrolledText widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, string)
            self.text_widget.configure(state='disabled')
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

    def flush(self):
        pass
    
    def isatty(self):
        """Required by uvicorn's logging formatter to check if stdout is a terminal."""
        return False

class RibFactoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"RIB Factory v{VERSION} - Server Manager")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Colors & Fonts
        self.bg_color = "#f8f9fa"
        self.primary_color = "#2c3e50"
        self.accent_color = "#3498db"
        self.success_color = "#27ae60"
        self.warning_color = "#f39c12"
        self.root.configure(bg=self.bg_color)
        
        self.setup_ui()
        
        # Start server thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        # Redirect stdout/stderr
        sys.stdout = LogRedirector(self.log_area)
        sys.stderr = LogRedirector(self.log_area)

    def setup_ui(self):
        # Header Area
        header = tk.Frame(self.root, bg=self.primary_color, height=80)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(header, text="RIB Factory Manager", 
                               fg="white", bg=self.primary_color, 
                               font=("Segoe UI", 18, "bold"))
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        ver_label = tk.Label(header, text=f"v{VERSION}", 
                               fg="#bdc3c7", bg=self.primary_color, 
                               font=("Segoe UI", 9))
        ver_label.pack(side=tk.LEFT, pady=(18, 0))

        # Status Panel (Top Right)
        status_panel = tk.Frame(header, bg=self.primary_color)
        status_panel.pack(side=tk.RIGHT, padx=20)

        # Server Status
        self.srv_status_ind = tk.Label(status_panel, text="●", fg="#f1c40f", 
                                        bg=self.primary_color, font=("Arial", 12))
        self.srv_status_ind.grid(row=0, column=0, sticky="e")
        self.srv_status_txt = tk.Label(status_panel, text="Serveur: Démarrage", 
                                   fg="white", bg=self.primary_color, font=("Segoe UI", 9))
        self.srv_status_txt.grid(row=0, column=1, sticky="w", padx=5)

        # OCR Model Status
        self.ocr_status_ind = tk.Label(status_panel, text="●", fg="#7f8c8d", 
                                        bg=self.primary_color, font=("Arial", 12))
        self.ocr_status_ind.grid(row=1, column=0, sticky="e")
        self.ocr_status_txt = tk.Label(status_panel, text="IA OCR: Attente", 
                                   fg="white", bg=self.primary_color, font=("Segoe UI", 9))
        self.ocr_status_txt.grid(row=1, column=1, sticky="w", padx=5)

        # Main Layout
        main_content = tk.Frame(self.root, bg=self.bg_color)
        main_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # Control Panel
        ctrl_frame = tk.Frame(main_content, bg=self.bg_color)
        ctrl_frame.pack(fill=tk.X, pady=(0, 20))

        self.btn_open = tk.Button(ctrl_frame, text="Ouvrir l'application", 
                                 command=self.open_browser,
                                 bg=self.accent_color, fg="white", 
                                 font=("Segoe UI", 10, "bold"),
                                 padx=25, pady=10, cursor="hand2", relief=tk.FLAT)
        self.btn_open.pack(side=tk.LEFT)

        tk.Button(ctrl_frame, text="Copier URL", 
                  command=self.copy_url,
                  bg="#95a5a6", fg="white", 
                  font=("Segoe UI", 9),
                  padx=15, pady=5, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT, padx=10)

        tk.Button(ctrl_frame, text="Vider les logs", 
                  command=self.clear_logs,
                  bg=self.bg_color, fg="#7f8c8d", 
                  font=("Segoe UI", 9),
                  padx=10, pady=5, cursor="hand2", relief=tk.FLAT, 
                  highlightbackground="#bdc3c7", highlightthickness=1).pack(side=tk.RIGHT)

        # Info Cards Area
        cards_frame = tk.Frame(main_content, bg=self.bg_color)
        cards_frame.pack(fill=tk.X, pady=(0, 15))

        # Dashboard Label
        tk.Label(main_content, text="Journal d'activité et Erreurs", 
                 bg=self.bg_color, fg=self.primary_color, 
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Log Area
        self.log_area = scrolledtext.ScrolledText(main_content, wrap=tk.WORD, 
                                                state='disabled', height=18,
                                                bg="white", font=("Consolas", 9),
                                                borderwidth=1, relief="solid")
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instr_label = tk.Label(main_content, text="L'application est accessible localement. Ne fermez pas cette fenêtre pendant l'utilisation.", 
                                bg=self.bg_color, fg="#7f8c8d", font=("Segoe UI", 8, "italic"))
        instr_label.pack(pady=(10, 0))

        # Footer
        footer = tk.Frame(self.root, bg="#ececec", height=45)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        # Credits & Info
        credits_label = tk.Label(footer, text="© 2026 @jerome0025 | Made with Python & DocTR", 
                                bg="#ececec", fg="#666", font=("Segoe UI", 9))
        credits_label.pack(side=tk.LEFT, padx=20, pady=12)

        # License
        lic_label = tk.Label(footer, text="Licence: GNU GPL v3", 
                                bg="#ececec", fg="#999", font=("Segoe UI", 8))
        lic_label.pack(side=tk.LEFT, padx=5)

        # GitHub Link
        github_btn = tk.Label(footer, text="Repository GitHub", 
                             fg=self.accent_color, bg="#ececec", 
                             font=("Segoe UI", 9, "underline"), cursor="hand2")
        github_btn.pack(side=tk.RIGHT, padx=20, pady=12)
        github_btn.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/jerome0025/RIB"))

    def run_server(self):
        try:
            print("DEBUG: Starting server initialization...")
            # Monitoring loop for OCR model (internal check)
            self.root.after(2000, self.check_ocr_status)
            
            print("DEBUG: Creating uvicorn config...")
            # Don't use custom log_config - let uvicorn handle it with defaults
            config = uvicorn.Config(
                app, 
                host="127.0.0.1", 
                port=8000, 
                log_level="info",
                access_log=False  # Disable access logs for cleaner output
            )
            print("DEBUG: Creating uvicorn server...")
            server = uvicorn.Server(config)
            
            print("DEBUG: Server ready, updating status...")
            self.root.after(0, self.update_server_status, "En ligne", self.success_color)
            
            print("DEBUG: Starting server.run()...")
            server.run()
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, self.update_server_status, "Erreur", "#e74c3c")

    def check_ocr_status(self):
        # We try to see if OCRService instance is created and model is loaded
        # Since it's a singleton, we check without triggering it
        try:
            from app.services.ocr import OCRService
            # In Tkinter main loop, we check periodicially
            if OCRService._model is not None:
                self.ocr_status_ind.configure(fg=self.success_color)
                self.ocr_status_txt.configure(text="IA OCR: Prêt")
            else:
                self.ocr_status_ind.configure(fg=self.warning_color)
                self.ocr_status_txt.configure(text="IA OCR: Chargement...")
                self.root.after(1000, self.check_ocr_status)
        except:
            self.root.after(1000, self.check_ocr_status)

    def update_server_status(self, text, color):
        self.srv_status_ind.configure(fg=color)
        self.srv_status_txt.configure(text=f"Serveur: {text}")

    def open_browser(self):
        webbrowser.open("http://127.0.0.1:8000")

    def copy_url(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("http://127.0.0.1:8000")
        messagebox.showinfo("Copié", "L'URL http://127.0.0.1:8000 a été copiée dans le presse-papier.")

    def clear_logs(self):
        self.log_area.configure(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.configure(state='disabled')
        print("--- Journal vidé par l'utilisateur ---")

    def on_closing(self):
        if messagebox.askokcancel("Quitter", "Voulez-vous arrêter le serveur et quitter ?"):
            os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    # Attempt to set a generic icon if possible, else skip
    try:
        root.iconbitmap(default=None) 
    except:
        pass
        
    app_gui = RibFactoryGUI(root)
    root.mainloop()
