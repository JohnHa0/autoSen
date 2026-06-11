import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re

class LoginDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("系统登录")
        self.top.geometry("350x250")
        self.top.resizable(False, False)
        
        # Center the window
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        self.top.grab_set()
        
        self.authenticated_user = None
        
        self.build_ui()
        
    def build_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10))
        
        frame = ttk.Frame(self.top, padding="30 30 30 30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="欢迎使用自动化系统", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 20))
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, expand=True)
        
        ttk.Label(input_frame, text="账 号:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(input_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(input_frame, text="密 码:").grid(row=1, column=0, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(input_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, expand=True, pady=(20, 0))
        
        ttk.Button(btn_frame, text="登 录", command=self.attempt_login).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="退 出", command=self.top.destroy).pack(side=tk.RIGHT)
        
        self.top.bind('<Return>', lambda e: self.attempt_login())
        
    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("提示", "请输入账号和密码", parent=self.top)
            return
            
        # Auth Logic 1: Admin
        if username == "tsrhs" and password == "815008":
            self.authenticated_user = "tsrhs"
            self.top.destroy()
            return
            
        # Auth Logic 2: Chinese name
        if re.match(r'^[\u4e00-\u9fa5]{2,}$', username):
            if password == "12345!":
                self.authenticated_user = username
                self.top.destroy()
                return
            else:
                messagebox.showerror("错误", "密码错误！实名认证默认密码为 12345!", parent=self.top)
                return
                
        messagebox.showerror("错误", "账号或密码错误！\n支持纯中文姓名登录或管理员账户", parent=self.top)

def require_login(parent):
    dialog = LoginDialog(parent)
    parent.wait_window(dialog.top)
    return dialog.authenticated_user
