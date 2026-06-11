import os
import json

class ConfigManager:
    def __init__(self):
        # Linux: ~/.config/autoHao/, Windows: AppData/Local/autoHao/
        if os.name == 'nt':
            self.config_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'autoHao')
        else:
            self.config_dir = os.path.join(os.path.expanduser('~'), '.config', 'autoHao')
            
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.default_config = {
            "PRE_FIX": "（北部战区）",
            "TARGET_DIR": os.path.join(os.path.expanduser('~'), "Downloads", "Extracted"),
            "CSV_FOLDER_PATH": os.path.join(os.path.expanduser('~'), "Documents"),
            "CSV_NAME_TEMPLATE": "{author}_上报条目_{year}-{month}.csv",
            "COMMENT": "（黄枫谷）\n（根据银月上报）",
            "INSERT_POS": "before_keyword", # 'before_keyword' or 'at_eof'
            "FILE_ENCODING": "auto", # 'auto', 'gbk', 'utf-8'
            "AUTHOR": "未命名",
            "LOG_RETENTION_DAYS": 15
        }
        self.config = self.load_config()

    def safe_makedirs(self, path):
        if path and not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError:
                pass

    def load_config(self):
        if not os.path.exists(self.config_file):
            return self.default_config.copy()
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # merge with default to ensure all keys exist
                config = self.default_config.copy()
                config.update(loaded)
                return config
        except Exception:
            return self.default_config.copy()

    def save_config(self, new_config=None):
        if new_config:
            self.config.update(new_config)
        self.safe_makedirs(self.config_dir)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def exists(self):
        return os.path.exists(self.config_file)
