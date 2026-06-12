import os
import shutil
import re
import time
import datetime
import csv
import zipfile
import logging
from log_manager import setup_logger

def safe_makedirs(path):
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
                
                fixed_name = fixed_name.replace('\\', '/')
                target_path = os.path.join(extract_folder, fixed_name)
                
                if fixed_name.endswith('/'):
                    safe_makedirs(target_path)
                    continue
                
                safe_makedirs(os.path.dirname(target_path))
                with zf.open(member) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
    else:
        shutil.unpack_archive(archive_path, extract_folder)

def process_text_file(file_path, config, logger):
    comment = config.get("COMMENT", "")
    if not comment:
        return
        
    insert_pos = config.get("INSERT_POS", "before_keyword")
    encoding_mode = config.get("FILE_ENCODING", "auto")
    
    content_lines = []
    
    if encoding_mode == 'auto':
        encodings_to_try = ['utf-8', 'gbk']
    else:
        encodings_to_try = [encoding_mode]
        
    read_success = False
    used_encoding = 'utf-8'
    
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content_lines = f.readlines()
            read_success = True
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue
            
    if not read_success:
        logger.warning("无法读取文件内容（编码错误）: {}".format(file_path))
        return
        
    out_lines = []
    inserted = False
    
    if insert_pos == 'at_eof':
        out_lines = content_lines[:]
        if out_lines and not out_lines[-1].endswith('\n'):
            out_lines[-1] += '\n'
        out_lines.append(comment + '\n')
        inserted = True
    else:
        for line in content_lines:
            if line.startswith("主题词") and not inserted:
                out_lines.append(comment + "\n")
                inserted = True
            out_lines.append(line)
            
        if not inserted:
            if out_lines and not out_lines[-1].endswith('\n'):
                out_lines[-1] += '\n'
            out_lines.append(comment + '\n')
            inserted = True
            
    if inserted:
        try:
            with open(file_path, 'w', encoding=used_encoding) as f:
                f.writelines(out_lines)
            logger.info("成功插入尾注到文件: {}".format(file_path))
        except Exception as e:
            logger.error("写入文件失败: {}, Error: {}".format(file_path, e))

def update_csv_summary(file_path, opt_name, config, logger):
    csv_folder = config.get("CSV_FOLDER_PATH", "")
    if not csv_folder:
        return
        
    safe_makedirs(csv_folder)
    
    author = config.get("AUTHOR", "未命名")
    template = config.get("CSV_NAME_TEMPLATE", "{author}_上报条目_{year}-{month}.csv")
    
    now = datetime.datetime.now()
    # Support formatting for old python 3.5 without f-strings
    csv_name = template.replace("{author}", author) \
                       .replace("{year}", now.strftime("%Y")) \
                       .replace("{month}", now.strftime("%m")) \
                       .replace("{day}", now.strftime("%d"))
    
    csv_path = os.path.join(csv_folder, csv_name)
    file_exists = os.path.exists(csv_path)
    
    mtime = os.path.getmtime(file_path)
    date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    
    try:
        with open(csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["日期", "作者", "文件名称"])
            writer.writerow([date_str, author, opt_name])
        logger.info("CSV记录已更新: {}".format(csv_path))
    except Exception as e:
        logger.error("CSV写入失败: {}".format(e))

def process_archive(archive_path, config):
    logger = setup_logger(config)
    logger.info("开始处理压缩包: {}".format(archive_path))
    
    target_dir = config.get("TARGET_DIR")
    if not target_dir:
        logger.error("未配置 TARGET_DIR 目标保存目录")
        return
        
    safe_makedirs(target_dir)
    extract_folder = archive_path + "_extracted"
    
    try:
        smart_extract(archive_path, extract_folder)
    except Exception as e:
        logger.error("解压失败 {}: {}".format(archive_path, e))
        return

    pre_fix = config.get("PRE_FIX", "（文件前缀名）")
    
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            if file.endswith(".txt"):
                # Use sub, avoid f-strings for python < 3.6 compatibility
                new_name = re.sub(r'^【原文】(?:(?!\d+月)[\d\s\-_\.])+', pre_fix, file)
                
                if new_name == file and file.startswith("【原文】"):
                    new_name = file.replace("【原文】", pre_fix, 1)
                
                old_path = os.path.join(root, file)
                new_path = os.path.join(target_dir, new_name)
                
                if os.path.exists(new_path):
                    name, ext = os.path.splitext(new_name)
                    timestamp = int(time.time())
                    new_path = os.path.join(target_dir, "{}_{}{}".format(name, timestamp, ext))
                
                shutil.move(old_path, new_path)
                logger.info("文件已重命名并移动: {}".format(new_name))
                
                process_text_file(new_path, config, logger)
                
                opt_name = new_name.replace(pre_fix, "").replace(".txt", "")
                update_csv_summary(new_path, opt_name, config, logger)

    try:
        shutil.rmtree(extract_folder)
        os.remove(archive_path)
        logger.info("处理完成并已删除原始压缩包: {}".format(archive_path))
    except Exception as e:
        logger.error("清理临时文件失败: {}".format(e))
