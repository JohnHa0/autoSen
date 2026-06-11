import unittest
import os
import shutil
import tempfile
import re

# We will mock the logger to avoid creating real logs during tests
class DummyLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

from core_processor import process_text_file

class TestCoreProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = DummyLogger()
        self.config = {
            "COMMENT": "TEST_COMMENT",
            "INSERT_POS": "before_keyword",
            "FILE_ENCODING": "utf-8"
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_regex_rename_preserves_month(self):
        pre_fix = "（前缀）"
        filenames = [
            ("【原文】5月6日汇报.txt", "（前缀）5月6日汇报.txt"),
            ("【原文】2026-05-06_工作.txt", "（前缀）工作.txt"),
            ("【原文】 2026.05.06 测试.txt", "（前缀）测试.txt"),
            ("【原文】 12月3日 .txt", "（前缀）12月3日 .txt")
        ]
        
        for original, expected in filenames:
            new_name = re.sub(r'^【原文】(?:(?!\d+月)[\d\s\-_\.])+', pre_fix, original)
            if new_name == original and original.startswith("【原文】"):
                new_name = original.replace("【原文】", pre_fix, 1)
                
            self.assertEqual(new_name, expected, f"Failed on {original}")

    def test_text_insertion_with_keyword(self):
        test_file = os.path.join(self.temp_dir, "test1.txt")
        content = "Line 1\n主题词: 测试\nLine 3"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        process_text_file(test_file, self.config, self.logger)
        
        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()
            
        expected = "Line 1\nTEST_COMMENT\n主题词: 测试\nLine 3"
        self.assertEqual(result, expected)

    def test_text_insertion_fallback_eof(self):
        test_file = os.path.join(self.temp_dir, "test2.txt")
        content = "Line 1\nLine 2\nLine 3"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        process_text_file(test_file, self.config, self.logger)
        
        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()
            
        expected = "Line 1\nLine 2\nLine 3\nTEST_COMMENT\n"
        self.assertEqual(result, expected)

    def test_text_insertion_force_eof(self):
        test_file = os.path.join(self.temp_dir, "test3.txt")
        content = "Line 1\n主题词: 测试\nLine 3"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        config = self.config.copy()
        config["INSERT_POS"] = "at_eof"
        
        process_text_file(test_file, config, self.logger)
        
        with open(test_file, "r", encoding="utf-8") as f:
            result = f.read()
            
        expected = "Line 1\n主题词: 测试\nLine 3\nTEST_COMMENT\n"
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
