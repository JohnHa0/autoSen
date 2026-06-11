import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import datetime
from system_integrator import SystemIntegrator

# ToolTip Implementation for old tkinter versions
class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None

    def enter(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("Microsoft YaHei", 9, "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

def create_tooltip(widget, text):
    ToolTip(widget, text)

class ConfigGUI:
    def __init__(self, config_manager, authenticated_user=None):
        self.config = config_manager
        self.auth_user = authenticated_user
        
        self.root = tk.Tk()
        self.root.title("自动化解压处理工具 - 设置中心")
        self.root.geometry("600x650")
        
        # Center Window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        self.system_integrator = SystemIntegrator()
        
        self.build_ui()
        
        # Auto-update author if logged in via real name
        if self.auth_user and self.auth_user != "tsrhs":
            self.var_author.set(self.auth_user)
            
    def build_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 14, "bold"))
        
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="全局配置", style="Header.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.W)
        
        row = 1
        # Author
        ttk.Label(main_frame, text="作 者 (提交人):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_author = tk.StringVar(value=self.config.get("AUTHOR"))
        author_entry = ttk.Entry(main_frame, textvariable=self.var_author, width=40)
        author_entry.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(author_entry, "用于在统计表格中记录处理人姓名")
        row += 1
        
        # Prefix
        ttk.Label(main_frame, text="重命名前缀:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_prefix = tk.StringVar(value=self.config.get("PRE_FIX"))
        prefix_entry = ttk.Entry(main_frame, textvariable=self.var_prefix, width=40)
        prefix_entry.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(prefix_entry, "自动解压出的文本文件开头，会用此文本替换【原文】")
        row += 1
        
        # Target Dir
        ttk.Label(main_frame, text="解压保存文件夹:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_target_dir = tk.StringVar(value=self.config.get("TARGET_DIR"))
        dir_entry = ttk.Entry(main_frame, textvariable=self.var_target_dir, width=40)
        dir_entry.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        ttk.Button(main_frame, text="选择...", command=lambda: self.browse_dir(self.var_target_dir)).grid(row=row, column=2, padx=5)
        row += 1
        
        # CSV Path
        ttk.Label(main_frame, text="CSV 表格保存目录:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_csv_folder = tk.StringVar(value=self.config.get("CSV_FOLDER_PATH"))
        csv_dir_entry = ttk.Entry(main_frame, textvariable=self.var_csv_folder, width=40)
        csv_dir_entry.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        ttk.Button(main_frame, text="选择...", command=lambda: self.browse_dir(self.var_csv_folder)).grid(row=row, column=2, padx=5)
        row += 1
        
        # CSV Template
        ttk.Label(main_frame, text="CSV 命名模板:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_csv_tmpl = tk.StringVar(value=self.config.get("CSV_NAME_TEMPLATE"))
        tmpl_entry = ttk.Entry(main_frame, textvariable=self.var_csv_tmpl, width=40)
        tmpl_entry.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(tmpl_entry, "支持动态标签: {author}, {year}, {month}, {day}。例如: {author}_汇总_{year}.csv")
        row += 1
        
        # Comment
        ttk.Label(main_frame, text="待插入尾注:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.txt_comment = tk.Text(main_frame, height=4, width=40, font=("Microsoft YaHei", 9))
        self.txt_comment.insert("1.0", self.config.get("COMMENT", ""))
        self.txt_comment.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        row += 1
        
        # Insert Pos
        ttk.Label(main_frame, text="尾注插入位置:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_insert_pos = tk.StringVar(value=self.config.get("INSERT_POS"))
        pos_combo = ttk.Combobox(main_frame, textvariable=self.var_insert_pos, state="readonly", values=["before_keyword", "at_eof"])
        pos_combo.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(pos_combo, "before_keyword: 在'主题词'上一行插入 (若找不到则自动在末尾插入)\nat_eof: 强制插入在文件最后一行")
        row += 1
        
        # Encoding
        ttk.Label(main_frame, text="文本读写编码:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_encoding = tk.StringVar(value=self.config.get("FILE_ENCODING"))
        enc_combo = ttk.Combobox(main_frame, textvariable=self.var_encoding, state="readonly", values=["auto", "gbk", "utf-8"])
        enc_combo.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(enc_combo, "auto: 自动尝试识别(推荐)\ngbk: 统一当做GBK处理\nutf-8: 统一当做UTF-8处理")
        row += 1
        
        # Log Retention
        ttk.Label(main_frame, text="日志保留周期(天):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.var_log_retention = tk.StringVar(value=str(self.config.get("LOG_RETENTION_DAYS")))
        log_combo = ttk.Combobox(main_frame, textvariable=self.var_log_retention, state="readonly", values=["7", "15", "30", "0"])
        log_combo.grid(row=row, column=1, pady=5, padx=5, sticky=tk.W)
        create_tooltip(log_combo, "选择0天代表永久保留不清理")
        row += 1
        
        # Buttons
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky="ew", pady=15)
        row += 1
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="ew")
        
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🚀 一键集成到右键菜单", command=self.install_menu).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 解除集成", command=self.uninstall_menu).pack(side=tk.LEFT, padx=5)
        
        row += 1
        # Status Label
        self.status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.status_var, foreground="green").grid(row=row, column=0, columnspan=3, pady=10)
        
        # Copyright
        ttk.Label(self.root, text="Copyright © 2026 AutoHao v1.0 | 系统组", font=("Microsoft YaHei", 8, "italic"), foreground="gray").pack(side=tk.BOTTOM, pady=10)

    def browse_dir(self, string_var):
        dir_path = filedialog.askdirectory(parent=self.root)
        if dir_path:
            string_var.set(dir_path)

    def save_config(self):
        self.config.set("AUTHOR", self.var_author.get().strip())
        self.config.set("PRE_FIX", self.var_prefix.get().strip())
        self.config.set("TARGET_DIR", self.var_target_dir.get().strip())
        self.config.set("CSV_FOLDER_PATH", self.var_csv_folder.get().strip())
        self.config.set("CSV_NAME_TEMPLATE", self.var_csv_tmpl.get().strip())
        self.config.set("COMMENT", self.txt_comment.get("1.0", tk.END).strip())
        self.config.set("INSERT_POS", self.var_insert_pos.get())
        self.config.set("FILE_ENCODING", self.var_encoding.get())
        self.config.set("LOG_RETENTION_DAYS", int(self.var_log_retention.get()))
        
        self.status_var.set("✅ 配置已成功保存！后台执行将立即采用新设定。")
        self.root.after(3000, lambda: self.status_var.set(""))
        
    def install_menu(self):
        success, msg = self.system_integrator.install_right_click()
        if success:
            self.status_var.set(f"✅ {msg}")
        else:
            messagebox.showerror("错误", f"集成失败:\n{msg}", parent=self.root)
            
    def uninstall_menu(self):
        success, msg = self.system_integrator.uninstall_right_click()
        if success:
            self.status_var.set(f"✅ {msg}")
        else:
            messagebox.showerror("错误", f"移除失败:\n{msg}", parent=self.root)
            
    def run(self):
        self.root.mainloop()

def launch_gui(config_manager, auth_user):
    app = ConfigGUI(config_manager, auth_user)
    app.run()
