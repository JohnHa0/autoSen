import sys
import os
import tkinter as tk
from tkinter import messagebox
from config_manager import ConfigManager
from core_processor import process_archive

def show_error_and_exit(title, message):
    root = tk.Tk()
    root.withdraw() # Hide the main window
    messagebox.showerror(title, message)
    root.destroy()
    sys.exit(1)

def main():
    config_mgr = ConfigManager()
    
    if len(sys.argv) > 1:
        # Silent Mode (Right Click context menu)
        if not config_mgr.exists():
            show_error_and_exit("配置未初始化", "系统检测到您尚未进行任何设置。\n请先从应用菜单(或双击本程序主体)打开设置界面进行初始化配置！")
            
        config = config_mgr.load_config()
        # Process all passed files
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                process_archive(arg, config)
    else:
        # GUI Mode
        root = tk.Tk()
        root.withdraw() # Hide main root until login is done
        
        # 1. Login
        from gui_login import require_login
        auth_user = require_login(root)
        
        if not auth_user:
            # Login cancelled or failed
            sys.exit(0)
            
        # 2. Main Config UI
        root.destroy() # Destroy the temporary root
        from gui_manager import launch_gui
        launch_gui(config_mgr, auth_user)

if __name__ == "__main__":
    main()
