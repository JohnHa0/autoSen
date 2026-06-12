import os
import time
import threading
from core_processor import process_archive
import logging
from log_manager import setup_logger

class FolderMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._running = False
        self._thread = None
        self.logger = setup_logger(self.config_manager.config)
        self._ignored_files = set()

    def _check_has_txt(self, file_path):
        try:
            if file_path.lower().endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for name in zf.namelist():
                        if name.lower().endswith('.txt'):
                            return True
                return False
        except Exception as e:
            self.logger.error("检查压缩包内容失败 {}: {}".format(file_path, e))
        return False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.logger.info("后台监控线程已启动")

    def stop(self):
        self._running = False
        if self._thread:
            self.logger.info("后台监控线程已停止")

    def _monitor_loop(self):
        while self._running:
            try:
                # Reload config every loop to get real-time updates
                config = self.config_manager.load_config()
                if config.get("ENABLE_MONITOR"):
                    monitor_dir = config.get("MONITOR_DIR", "")
                    if monitor_dir and os.path.isdir(monitor_dir):
                        for file in os.listdir(monitor_dir):
                            if file.lower().endswith(('.zip', '.rar')):
                                file_path = os.path.join(monitor_dir, file)
                                
                                try:
                                    file_stat = os.stat(file_path)
                                    file_key = (file_path, file_stat.st_mtime, file_stat.st_size)
                                except OSError:
                                    continue
                                    
                                if file_key in self._ignored_files:
                                    continue
                                
                                # Simple check to see if the file is fully copied (not being written to)
                                initial_size = os.path.getsize(file_path)
                                time.sleep(1)
                                if initial_size == os.path.getsize(file_path):
                                    if config.get("MONITOR_ONLY_TXT", False):
                                        if not self._check_has_txt(file_path):
                                            self.logger.info("跳过非TXT压缩包: {}".format(file_path))
                                            self._ignored_files.add(file_key)
                                            continue
                                            
                                    self.logger.info("监控到新压缩包: {}".format(file_path))
                                    process_archive(file_path, config)
            except Exception as e:
                self.logger.error("后台监控发生异常: {}".format(e))
                
            # Sleep for 5 seconds before checking again
            for _ in range(5):
                if not self._running:
                    break
                time.sleep(1)
