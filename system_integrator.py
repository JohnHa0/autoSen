import os
import sys
import stat

class SystemIntegrator:
    def __init__(self):
        self.is_windows = os.name == 'nt'
        
    def get_executable_path(self):
        # Determine the current executable path
        if getattr(sys, 'frozen', False):
            # If packaged with pyinstaller
            return sys.executable
        else:
            # If running as script
            return sys.executable + ' ' + os.path.abspath(sys.argv[0])

    def install_right_click(self):
        try:
            if self.is_windows:
                return self._install_windows()
            else:
                return self._install_linux()
        except Exception as e:
            return False, str(e)

    def uninstall_right_click(self):
        try:
            if self.is_windows:
                return self._uninstall_windows()
            else:
                return self._uninstall_linux()
        except Exception as e:
            return False, str(e)

    def _install_linux(self):
        script_dir = os.path.join(os.path.expanduser('~'), '.config', 'caja', 'scripts')
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
            
        script_path = os.path.join(script_dir, '一键处理')
        exec_path = self.get_executable_path()
        
        # Write the shell script for caja
        script_content = '''#!/bin/bash
IFS=$'\\n'
for file in $CAJA_SCRIPT_SELECTED_FILE_PATHS; do
    {exec_path} "$file"
done
notify-send "✅ 任务完成" "选中的压缩包已解压整理，CSV 清单已更新！"
'''.format(exec_path=exec_path)

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        # Make it executable
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
        return True, "成功添加到 Caja 右键脚本目录"

    def _uninstall_linux(self):
        script_path = os.path.join(os.path.expanduser('~'), '.config', 'caja', 'scripts', '一键处理')
        if os.path.exists(script_path):
            os.remove(script_path)
            return True, "已从 Caja 脚本目录移除"
        return True, "原本就不存在，无需移除"

    def _install_windows(self):
        try:
            import winreg
            exec_path = self.get_executable_path()
            key_path = r"Software\\Classes\\*\\shell\\AutoHao"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValue(key, '', winreg.REG_SZ, "🚀 自动解压并整理(&A)")
            winreg.CloseKey(key)
            
            command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\\command")
            winreg.SetValue(command_key, '', winreg.REG_SZ, '"{}" "%1"'.format(exec_path))
            winreg.CloseKey(command_key)
            
            return True, "成功添加到 Windows 右键菜单"
        except Exception as e:
            return False, "注册表写入失败: " + str(e)

    def _uninstall_windows(self):
        try:
            import winreg
            key_path = r"Software\\Classes\\*\\shell\\AutoHao"
            
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            
            return True, "已从 Windows 右键菜单移除"
        except FileNotFoundError:
            return True, "原本就不存在，无需移除"
        except Exception as e:
            return False, "注册表移除失败: " + str(e)
