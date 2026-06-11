import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import datetime
from system_integrator import SystemIntegrator
from monitor_service import FolderMonitor

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
        self.root.geometry("950x650")
        self.root.configure(bg="#f0f2f5")
        
        self.root.update_idletasks()
        width = 950
        height = 650
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        self.system_integrator = SystemIntegrator()
        
        # Start Background Monitor
        self.monitor = FolderMonitor(self.config)
        self.monitor.start()
        
        self.build_ui()
        
        if self.auth_user and self.auth_user != "tsrhs":
            self.var_author.set(self.auth_user)
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
    def on_closing(self):
        self.monitor.stop()
        self.root.destroy()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", font=("Microsoft YaHei", 10), background="#ffffff")
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 14, "bold"), foreground="#1890ff", background="#ffffff")
        style.configure("SubHeader.TLabel", font=("Microsoft YaHei", 11, "bold"), foreground="#333333", background="#ffffff")
        style.configure("TFrame", background="#ffffff")
        style.configure("Card.TFrame", background="#ffffff", relief="groove", borderwidth=1)
        style.configure("TCheckbutton", font=("Microsoft YaHei", 10), background="#ffffff")
        
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_container, text="系统全局配置", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 15))
        
        # Create a frame to hold the cards in a 2x2 grid
        cards_container = ttk.Frame(main_container, style="TFrame")
        cards_container.pack(fill=tk.BOTH, expand=True)
        cards_container.columnconfigure(0, weight=1)
        cards_container.columnconfigure(1, weight=1)
        
        # Card 1: Basic settings
        card1 = ttk.Frame(cards_container, style="Card.TFrame", padding="15 15 15 15")
        card1.grid(row=0, column=0, padx=(0, 10), pady=(0, 15), sticky="nsew")
        ttk.Label(card1, text="基础信息", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(card1, text="作者 (提交人):").grid(row=1, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_author = tk.StringVar(value=self.config.get("AUTHOR"))
        author_entry = ttk.Entry(card1, textvariable=self.var_author, width=35)
        author_entry.grid(row=1, column=1, pady=5, sticky=tk.W)
        create_tooltip(author_entry, "用于在统计表格中记录处理人姓名")
        
        ttk.Label(card1, text="重命名前缀:").grid(row=2, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_prefix = tk.StringVar(value=self.config.get("PRE_FIX"))
        prefix_entry = ttk.Entry(card1, textvariable=self.var_prefix, width=35)
        prefix_entry.grid(row=2, column=1, pady=5, sticky=tk.W)
        create_tooltip(prefix_entry, "自动解压出的文本文件开头，会用此文本替换【原文】")
        
        ttk.Label(card1, text="日志保留周期:").grid(row=3, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_log_retention = tk.StringVar(value=str(self.config.get("LOG_RETENTION_DAYS")))
        log_combo = ttk.Combobox(card1, textvariable=self.var_log_retention, state="readonly", values=["7", "15", "30", "0"], width=10)
        log_combo.grid(row=3, column=1, pady=5, sticky=tk.W)
        ttk.Label(card1, text="天 (0为永久)").grid(row=3, column=1, sticky=tk.E, padx=(0, 100))
        
        # Card 2: Path settings
        card2 = ttk.Frame(cards_container, style="Card.TFrame", padding="15 15 15 15")
        card2.grid(row=0, column=1, padx=(10, 0), pady=(0, 15), sticky="nsew")
        ttk.Label(card2, text="路径与表格配置", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(card2, text="解压保存文件夹:").grid(row=1, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_target_dir = tk.StringVar(value=self.config.get("TARGET_DIR"))
        ttk.Entry(card2, textvariable=self.var_target_dir, width=40).grid(row=1, column=1, pady=5, sticky=tk.W)
        ttk.Button(card2, text="浏览...", command=lambda: self.browse_dir(self.var_target_dir)).grid(row=1, column=2, padx=10)
        
        ttk.Label(card2, text="CSV 表格保存目录:").grid(row=2, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_csv_folder = tk.StringVar(value=self.config.get("CSV_FOLDER_PATH"))
        ttk.Entry(card2, textvariable=self.var_csv_folder, width=40).grid(row=2, column=1, pady=5, sticky=tk.W)
        ttk.Button(card2, text="浏览...", command=lambda: self.browse_dir(self.var_csv_folder)).grid(row=2, column=2, padx=10)
        
        ttk.Label(card2, text="CSV 命名模板:").grid(row=3, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_csv_tmpl = tk.StringVar(value=self.config.get("CSV_NAME_TEMPLATE"))
        tmpl_entry = ttk.Entry(card2, textvariable=self.var_csv_tmpl, width=40)
        tmpl_entry.grid(row=3, column=1, pady=5, sticky=tk.W)
        create_tooltip(tmpl_entry, "支持动态标签: {author}, {year}, {month}, {day}\n例如: {author}_汇总_{year}.csv")
        
        # Card 3: Advanced Settings
        card3 = ttk.Frame(cards_container, style="Card.TFrame", padding="15 15 15 15")
        card3.grid(row=1, column=0, padx=(0, 10), pady=(0, 15), sticky="nsew")
        ttk.Label(card3, text="文本尾注设置", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(card3, text="尾注插入位置:").grid(row=1, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        
        # Mappings for UI strings
        self.pos_map = {"主题词上一行": "before_keyword", "文件末尾": "at_eof"}
        self.pos_inv = {"before_keyword": "主题词上一行", "at_eof": "文件末尾"}
        self.enc_map = {"自动检测": "auto", "统当为GBK": "gbk", "统当为UTF-8": "utf-8"}
        self.enc_inv = {"auto": "自动检测", "gbk": "统当为GBK", "utf-8": "统当为UTF-8"}
        
        self.var_insert_pos = tk.StringVar(value=self.pos_inv.get(self.config.get("INSERT_POS", "before_keyword"), "主题词上一行"))
        ttk.Combobox(card3, textvariable=self.var_insert_pos, state="readonly", values=list(self.pos_map.keys()), width=15).grid(row=1, column=1, pady=5, sticky=tk.W)
        
        ttk.Label(card3, text="文本读写编码:").grid(row=2, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_encoding = tk.StringVar(value=self.enc_inv.get(self.config.get("FILE_ENCODING", "auto"), "自动检测"))
        ttk.Combobox(card3, textvariable=self.var_encoding, state="readonly", values=list(self.enc_map.keys()), width=15).grid(row=2, column=1, pady=5, sticky=tk.W)
        
        ttk.Label(card3, text="待插入尾注内容:").grid(row=3, column=0, sticky=tk.NE, pady=5, padx=(0, 10))
        self.txt_comment = tk.Text(card3, height=3, width=40, font=("Microsoft YaHei", 9))
        self.txt_comment.insert("1.0", self.config.get("COMMENT", ""))
        self.txt_comment.grid(row=3, column=1, pady=5, sticky=tk.W)

        # Card 4: Monitor Settings
        card4 = ttk.Frame(cards_container, style="Card.TFrame", padding="15 15 15 15")
        card4.grid(row=1, column=1, padx=(10, 0), pady=(0, 15), sticky="nsew")
        ttk.Label(card4, text="后台文件夹监控", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        self.var_enable_monitor = tk.BooleanVar(value=self.config.get("ENABLE_MONITOR", False))
        ttk.Checkbutton(card4, text="开启指定文件夹监控 (发现新压缩包自动处理)", variable=self.var_enable_monitor).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(card4, text="监控文件夹:").grid(row=2, column=0, sticky=tk.E, pady=5, padx=(0, 10))
        self.var_monitor_dir = tk.StringVar(value=self.config.get("MONITOR_DIR", ""))
        ttk.Entry(card4, textvariable=self.var_monitor_dir, width=40).grid(row=2, column=1, pady=5, sticky=tk.W)
        ttk.Button(card4, text="浏览...", command=lambda: self.browse_dir(self.var_monitor_dir)).grid(row=2, column=2, padx=10)

        # Buttons
        btn_frame = ttk.Frame(main_container, style="TFrame")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = ttk.Button(btn_frame, text="💾 保存所有配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        install_btn = ttk.Button(btn_frame, text="🚀 添加到右键菜单", command=self.install_menu)
        install_btn.pack(side=tk.LEFT, padx=10)
        
        uninstall_btn = ttk.Button(btn_frame, text="🗑 移除右键菜单", command=self.uninstall_menu)
        uninstall_btn.pack(side=tk.LEFT, padx=10)
        
        open_log_btn = ttk.Button(btn_frame, text="📂 查看运行日志", command=self.open_log_dir)
        open_log_btn.pack(side=tk.RIGHT, padx=10)
        
        # Status Label
        self.status_var = tk.StringVar()
        ttk.Label(main_container, textvariable=self.status_var, foreground="#52c41a", font=("Microsoft YaHei", 9, "bold")).pack(pady=(15, 0))
        
        # Copyright
        ttk.Label(self.root, text="Copyright © 2026 AutoHao v1.2 | 系统组研制", font=("Microsoft YaHei", 8, "italic"), foreground="#8c8c8c", background="#f0f2f5").pack(side=tk.BOTTOM, pady=10)

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
        
        pos_val = self.pos_map.get(self.var_insert_pos.get(), "before_keyword")
        self.config.set("INSERT_POS", pos_val)
        
        enc_val = self.enc_map.get(self.var_encoding.get(), "auto")
        self.config.set("FILE_ENCODING", enc_val)
        
        self.config.set("LOG_RETENTION_DAYS", int(self.var_log_retention.get()))
        self.config.set("MONITOR_DIR", self.var_monitor_dir.get().strip())
        self.config.set("ENABLE_MONITOR", self.var_enable_monitor.get())
        
        self.status_var.set("✅ 配置已成功保存！")
        self.root.after(3000, lambda: self.status_var.set(""))
        
    def install_menu(self):
        success, msg = self.system_integrator.install_right_click()
        if success:
            self.status_var.set(f"✅ {msg}")
        else:
            messagebox.showerror("系统错误", f"集成失败:\n{msg}", parent=self.root)
            
    def uninstall_menu(self):
        success, msg = self.system_integrator.uninstall_right_click()
        if success:
            self.status_var.set(f"✅ {msg}")
        else:
            messagebox.showerror("系统错误", f"移除失败:\n{msg}", parent=self.root)
            
    def open_log_dir(self):
        import os
        import platform
        import subprocess
        
        if os.name == 'nt':
            log_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'autoHao', 'logs')
        else:
            log_dir = os.path.join(os.path.expanduser('~'), '.config', 'autoHao', 'logs')
            
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                pass
                
        if platform.system() == "Windows":
            os.startfile(log_dir)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", log_dir])
        else:
            subprocess.Popen(["xdg-open", log_dir])
            
    def run(self):
        self.root.mainloop()

def launch_gui(config_manager, auth_user):
    app = ConfigGUI(config_manager, auth_user)
    app.run()
