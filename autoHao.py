import os
import shutil
import re
import time
import datetime
import csv
import zipfile
 
 
# ============================================
#        ------ --------           
#        -------- 系统组 ----------
#        ------ 2026.04.20 --------
# ============================================

# ================= 配置区域 =================
# ======== 自行替换引号内的内容/文件路径 ======
# --------------- 报文前缀--------------------
PRE_FIX = "（北部战区）"
# --------------- 报文保存路径 ---------------
TARGET_DIR = "/root/下载/0420-0426" 
# --------------- 报文统计表格保存路径 ---------------
CSV_PATH = "/root/文档/文件/1.个人目录/韩立/2026/上报/上报条目0420-0426.csv" 
# ------------- 手动插入尾注（待实现） ---------------
COMMENT = "（黄枫谷）\n （根据银月上报）"
# ============================================
 
def safe_makedirs(path):
    """安全创建目录的兼容写法"""
    if path and not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            pass
 
def smart_extract(archive_path, extract_folder):
    safe_makedirs(extract_folder)
    
    if archive_path.lower().endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            for member in zf.infolist():
                original_name = member.filename
                
                try:
                    name_bytes = original_name.encode('cp437')
                    fixed_name = name_bytes.decode('gbk')
                except Exception:
                    fixed_name = original_name
                
                # 【核心修复】：把 Windows 乱入的反斜杠，统统替换成 Linux 的正斜杠
                fixed_name = fixed_name.replace('\\', '/')
                
                target_path = os.path.join(extract_folder, fixed_name)
                
                # 如果是文件夹，创建后跳过
                if fixed_name.endswith('/'):
                    safe_makedirs(target_path)
                    continue
                
                # 确保文件的父目录存在，然后写入文件
                safe_makedirs(os.path.dirname(target_path))
                with zf.open(member) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
    else:
        shutil.unpack_archive(archive_path, extract_folder)
 
def process_archive(archive_path):
    safe_makedirs(TARGET_DIR)
 
    extract_folder = archive_path + "_extracted"
    
    try:
        smart_extract(archive_path, extract_folder)
    except Exception as e:
        print("解压失败 {}: {}".format(archive_path, e))
        return
 
    # 遍历解压后的文件，正则重命名并移动
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            if file.endswith(".txt"):
                # 恢复你最初的需求：基于txt本身的名字，去除开头的数字等字符
                new_name = re.sub(r'^【原文】[\d\s\-_\.]+', PRE_FIX, file)
                
                old_path = os.path.join(root, file)
                new_path = os.path.join(TARGET_DIR, new_name)
                
                # 防重名覆盖处理
                if os.path.exists(new_path):
                    name, ext = os.path.splitext(new_name)
                    timestamp = int(time.time())
                    new_path = os.path.join(TARGET_DIR, "{}_{}{}".format(name, timestamp, ext))
                
                shutil.move(old_path, new_path)
 
    # 清理：删除解压临时文件夹和原始压缩包
    shutil.rmtree(extract_folder)
    os.remove(archive_path)
    print("处理完成并已删除原始压缩包: {}".format(archive_path))
 
    # 更新 CSV 汇总
    update_csv_summary()
 
def update_csv_summary():
    with open(CSV_PATH, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["日期", "文件名称"]) 
 
        if not os.path.exists(TARGET_DIR):
            return
 
        for file in os.listdir(TARGET_DIR):
            if file.endswith(".txt"):
                file_path = os.path.join(TARGET_DIR, file)
                mtime = os.path.getmtime(file_path)
                date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                f_opt = file.strip(PRE_FIX)
                writer.writerow([date_str, f_opt.strip(".txt")])
 
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                process_archive(arg)
