use chrono::Local;
use encoding_rs::{GBK, UTF_8};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use zip::ZipArchive;

const MAX_ARCHIVE_ENTRIES: usize = 10_000;
const MAX_UNCOMPRESSED_BYTES: u64 = 2 * 1024 * 1024 * 1024;

#[derive(Serialize, Deserialize, Clone)]
#[serde(default)]
pub struct AppConfig {
    pub author: String,
    pub pre_fix: String,
    pub log_retention_days: String,
    pub target_dir: String,
    pub csv_folder: String,
    pub csv_tmpl: String,
    pub insert_pos: String,
    pub file_encoding: String,
    pub comment: String,
    pub enable_monitor: bool,
    pub monitor_only_txt: bool,
    pub monitor_dir: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            author: String::new(),
            pre_fix: "（文件前缀名）".into(),
            log_retention_days: "7".into(),
            target_dir: String::new(),
            csv_folder: String::new(),
            csv_tmpl: "{author}_上报条目_{year}-{month}.csv".into(),
            insert_pos: "before_keyword".into(),
            file_encoding: "auto".into(),
            comment: String::new(),
            enable_monitor: false,
            monitor_only_txt: true,
            monitor_dir: String::new(),
        }
    }
}

pub fn get_config_path() -> PathBuf {
    let mut path = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    path.push("autoSen");
    let _ = fs::create_dir_all(&path);
    path.push("config.json");
    path
}

pub fn load_config() -> AppConfig {
    fs::read_to_string(get_config_path())
        .ok()
        .and_then(|content| serde_json::from_str(&content).ok())
        .unwrap_or_default()
}

pub fn validate_config(config: &AppConfig) -> Result<(), String> {
    if config.enable_monitor && config.monitor_dir.trim().is_empty() {
        return Err("开启监控时必须选择监听目录".into());
    }
    if !matches!(config.insert_pos.as_str(), "before_keyword" | "at_eof") {
        return Err("无效的文字插入位置".into());
    }
    if !matches!(config.file_encoding.as_str(), "auto" | "gbk" | "utf-8") {
        return Err("无效的文本编码".into());
    }
    Ok(())
}

pub fn save_config(config: &AppConfig) -> Result<(), String> {
    validate_config(config)?;
    let content = serde_json::to_string_pretty(config).map_err(|e| e.to_string())?;
    fs::write(get_config_path(), content).map_err(|e| e.to_string())
}

pub fn log_message(level: &str, message: &str, retention_days: &str) {
    let mut dir = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    dir.push("autoSen");
    dir.push("logs");
    if fs::create_dir_all(&dir).is_err() {
        return;
    }
    let path = dir.join("autosen.log");
    if let Ok(days) = retention_days.parse::<u64>() {
        if days > 0 {
            let expired = fs::metadata(&path)
                .and_then(|m| m.modified())
                .ok()
                .and_then(|t| SystemTime::now().duration_since(t).ok())
                .map(|age| age.as_secs() > days * 86_400)
                .unwrap_or(false);
            if expired {
                let _ = fs::remove_file(&path);
            }
        }
    }
    if let Ok(mut file) = fs::OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(
            file,
            "[{}] [{}] {}",
            Local::now().format("%Y-%m-%d %H:%M:%S"),
            level,
            message
        );
    }
}

pub fn process_archive(archive_path: &str, config: &AppConfig) -> Result<(), String> {
    validate_config(config)?;
    let path = Path::new(archive_path);
    if !path.is_file() {
        return Err("压缩包不存在或不是文件".into());
    }
    if config.target_dir.trim().is_empty() {
        return Err("尚未配置解压保存目录".into());
    }
    let target_dir = Path::new(&config.target_dir);
    fs::create_dir_all(target_dir).map_err(|e| format!("无法创建保存目录: {e}"))?;

    let extract_folder = temporary_extract_path(path);
    fs::create_dir_all(&extract_folder).map_err(|e| format!("无法创建临时目录: {e}"))?;
    let result = process_archive_inner(path, target_dir, &extract_folder, config);
    let _ = fs::remove_dir_all(&extract_folder);
    if result.is_ok() {
        fs::remove_file(path).map_err(|e| format!("处理成功但无法删除原压缩包: {e}"))?;
    }
    result
}

fn process_archive_inner(
    path: &Path,
    target_dir: &Path,
    extract_folder: &Path,
    config: &AppConfig,
) -> Result<(), String> {
    let input = fs::File::open(path).map_err(|e| format!("无法打开压缩包: {e}"))?;
    let mut archive = ZipArchive::new(input).map_err(|e| format!("ZIP 格式无效: {e}"))?;
    if archive.len() > MAX_ARCHIVE_ENTRIES {
        return Err(format!("压缩包文件数超过安全上限 {MAX_ARCHIVE_ENTRIES}"));
    }

    if config.monitor_only_txt {
        let has_txt = (0..archive.len()).any(|i| {
            archive
                .by_index(i)
                .ok()
                .map(|f| has_txt_extension(f.name()))
                .unwrap_or(false)
        });
        if !has_txt {
            return Err("压缩包中不包含 TXT 文件，已跳过".into());
        }
    }

    let total_size = (0..archive.len()).try_fold(0_u64, |total, i| {
        let file = archive.by_index(i).map_err(|e| e.to_string())?;
        total
            .checked_add(file.size())
            .ok_or_else(|| "压缩包解压大小溢出".to_string())
    })?;
    if total_size > MAX_UNCOMPRESSED_BYTES {
        return Err("压缩包解压后超过 2 GiB 安全上限".into());
    }

    for i in 0..archive.len() {
        let mut file = archive
            .by_index(i)
            .map_err(|e| format!("读取 ZIP 条目失败: {e}"))?;
        let decoded_name = decode_zip_name(file.name_raw());
        let relative = safe_relative_path(&decoded_name)?;
        if relative.as_os_str().is_empty() {
            continue;
        }
        let output = extract_folder.join(relative);
        if file.is_dir() || file.name().ends_with('/') {
            fs::create_dir_all(&output).map_err(|e| format!("创建目录失败: {e}"))?;
            continue;
        }
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {e}"))?;
        }
        let mut output_file =
            fs::File::create(&output).map_err(|e| format!("创建文件失败: {e}"))?;
        std::io::copy(&mut file, &mut output_file).map_err(|e| format!("解压文件失败: {e}"))?;
        output_file
            .sync_all()
            .map_err(|e| format!("写入文件失败: {e}"))?;
    }

    let mut text_files = Vec::new();
    for entry in walkdir::WalkDir::new(extract_folder) {
        let entry = entry.map_err(|e| format!("遍历解压目录失败: {e}"))?;
        if entry.file_type().is_file() && has_txt_extension(&entry.file_name().to_string_lossy()) {
            text_files.push(entry.into_path());
        }
    }
    if text_files.is_empty() {
        return Err("压缩包中没有可处理的 TXT 文件，原压缩包已保留".into());
    }
    for source in text_files {
        process_text_file(&source, config)?;
        let original_name = source
            .file_name()
            .ok_or_else(|| "无法读取文件名".to_string())?
            .to_string_lossy();
        let new_name = renamed_text_file(&original_name, &config.pre_fix);
        let destination = unique_destination(target_dir, &new_name);
        move_file(&source, &destination)?;
        let summary_name = Path::new(&new_name)
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .trim_start_matches(&config.pre_fix)
            .to_string();
        if let Err(error) = update_csv_summary(&summary_name, config) {
            log_message(
                "ERROR",
                &format!("文件已处理，但写入 CSV 失败: {error}"),
                &config.log_retention_days,
            );
        }
    }
    Ok(())
}

fn decode_zip_name(raw: &[u8]) -> String {
    std::str::from_utf8(raw)
        .map(str::to_owned)
        .unwrap_or_else(|_| GBK.decode(raw).0.into_owned())
}

fn safe_relative_path(name: &str) -> Result<PathBuf, String> {
    let normalized = name.replace('\\', "/");
    let mut safe = PathBuf::new();
    for component in Path::new(&normalized).components() {
        match component {
            Component::Normal(part) => safe.push(part),
            Component::CurDir => {}
            _ => return Err(format!("压缩包包含不安全路径: {name}")),
        }
    }
    Ok(safe)
}

fn has_txt_extension(name: &str) -> bool {
    Path::new(name)
        .extension()
        .map(|ext| ext.to_string_lossy().eq_ignore_ascii_case("txt"))
        .unwrap_or(false)
}

fn renamed_text_file(file_name: &str, prefix: &str) -> String {
    const MARKER: &str = "【原文】";
    if !file_name.starts_with(MARKER) {
        return sanitize_file_name(file_name);
    }
    let remainder = &file_name[MARKER.len()..];
    let chars: Vec<(usize, char)> = remainder.char_indices().collect();
    let mut end = 0;
    let mut index = 0;
    while index < chars.len() {
        let (offset, ch) = chars[index];
        if ch.is_ascii_digit() {
            let mut next = index;
            while next < chars.len() && chars[next].1.is_ascii_digit() {
                next += 1;
            }
            if next < chars.len() && chars[next].1 == '月' {
                break;
            }
            end = if next < chars.len() {
                chars[next].0
            } else {
                remainder.len()
            };
            index = next;
        } else if ch.is_whitespace() || matches!(ch, '-' | '_' | '.') {
            end = offset + ch.len_utf8();
            index += 1;
        } else {
            break;
        }
    }
    sanitize_file_name(&format!("{}{}", prefix, &remainder[end..]))
}

fn sanitize_file_name(name: &str) -> String {
    let sanitized: String = name
        .chars()
        .map(|ch| {
            if matches!(ch, '/' | '\\' | '\0') {
                '_'
            } else {
                ch
            }
        })
        .collect();
    let trimmed = sanitized.trim();
    if trimmed.is_empty() || trimmed == "." || trimmed == ".." {
        "unnamed.txt".into()
    } else {
        trimmed.into()
    }
}

fn temporary_extract_path(archive: &Path) -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let name = archive.file_name().unwrap_or_default().to_string_lossy();
    archive.with_file_name(format!(".{name}.autosen-{}-{stamp}", std::process::id()))
}

fn unique_destination(target_dir: &Path, file_name: &str) -> PathBuf {
    let initial = target_dir.join(file_name);
    if !initial.exists() {
        return initial;
    }
    let path = Path::new(file_name);
    let stem = path.file_stem().unwrap_or_default().to_string_lossy();
    let extension = path.extension().map(|v| v.to_string_lossy());
    for number in 1_u32.. {
        let candidate_name = match &extension {
            Some(ext) => format!("{stem}_{number}.{ext}"),
            None => format!("{stem}_{number}"),
        };
        let candidate = target_dir.join(candidate_name);
        if !candidate.exists() {
            return candidate;
        }
    }
    unreachable!()
}

fn move_file(source: &Path, destination: &Path) -> Result<(), String> {
    if fs::rename(source, destination).is_ok() {
        return Ok(());
    }
    let mut input = fs::File::open(source).map_err(|e| format!("打开源文件失败: {e}"))?;
    let mut output = fs::File::create(destination).map_err(|e| format!("创建目标文件失败: {e}"))?;
    std::io::copy(&mut input, &mut output).map_err(|e| format!("移动文件失败: {e}"))?;
    output
        .sync_all()
        .map_err(|e| format!("写入目标文件失败: {e}"))?;
    fs::remove_file(source).map_err(|e| format!("删除源文件失败: {e}"))
}

fn process_text_file(file_path: &Path, config: &AppConfig) -> Result<(), String> {
    if config.comment.is_empty() {
        return Ok(());
    }
    let bytes = fs::read(file_path).map_err(|e| format!("读取文本失败: {e}"))?;
    let (content, output_gbk) = match config.file_encoding.as_str() {
        "gbk" => (GBK.decode(&bytes).0.into_owned(), true),
        "utf-8" => (UTF_8.decode(&bytes).0.into_owned(), false),
        _ => match std::str::from_utf8(&bytes) {
            Ok(value) => (value.trim_start_matches('\u{feff}').to_owned(), false),
            Err(_) => (GBK.decode(&bytes).0.into_owned(), true),
        },
    };
    let newline = if content.contains("\r\n") {
        "\r\n"
    } else {
        "\n"
    };
    let had_trailing_newline = content.ends_with('\n');
    let mut lines: Vec<String> = content.lines().map(str::to_owned).collect();
    if config.insert_pos == "at_eof" {
        lines.push(config.comment.clone());
    } else {
        let position = lines
            .iter()
            .position(|line| line.trim_start().starts_with("主题词"))
            .unwrap_or(lines.len());
        lines.insert(position, config.comment.clone());
    }
    let mut output = lines.join(newline);
    if had_trailing_newline {
        output.push_str(newline);
    }
    let output_bytes = if output_gbk {
        GBK.encode(&output).0.into_owned()
    } else {
        output.into_bytes()
    };
    fs::write(file_path, output_bytes).map_err(|e| format!("写入文本失败: {e}"))
}

fn update_csv_summary(item_name: &str, config: &AppConfig) -> Result<(), String> {
    if config.csv_folder.trim().is_empty() {
        return Ok(());
    }
    fs::create_dir_all(&config.csv_folder).map_err(|e| format!("创建 CSV 目录失败: {e}"))?;
    let now = Local::now();
    let requested_name = config
        .csv_tmpl
        .replace("{author}", &config.author)
        .replace("{year}", &now.format("%Y").to_string())
        .replace("{month}", &now.format("%m").to_string())
        .replace("{day}", &now.format("%d").to_string());
    let mut csv_name = sanitize_file_name(&requested_name);
    if !csv_name.to_ascii_lowercase().ends_with(".csv") {
        csv_name.push_str(".csv");
    }
    let csv_path = Path::new(&config.csv_folder).join(csv_name);
    let exists = csv_path.exists();
    let mut file = fs::OpenOptions::new()
        .append(true)
        .create(true)
        .open(&csv_path)
        .map_err(|e| format!("打开 CSV 失败: {e}"))?;
    if !exists {
        file.write_all(b"\xEF\xBB\xBF")
            .map_err(|e| format!("写入 CSV BOM 失败: {e}"))?;
    }
    if !exists {
        write_csv_record(&mut file, &["日期", "作者", "文件名称"])?;
    }
    let date = now.format("%Y-%m-%d").to_string();
    write_csv_record(&mut file, &[&date, &config.author, item_name])?;
    file.flush().map_err(|e| format!("刷新 CSV 失败: {e}"))
}

fn write_csv_record(writer: &mut impl Write, fields: &[&str]) -> Result<(), String> {
    for (index, field) in fields.iter().enumerate() {
        if index > 0 {
            writer
                .write_all(b",")
                .map_err(|e| format!("写入 CSV 失败: {e}"))?;
        }
        writer
            .write_all(b"\"")
            .map_err(|e| format!("写入 CSV 失败: {e}"))?;
        writer
            .write_all(field.replace('"', "\"\"").as_bytes())
            .map_err(|e| format!("写入 CSV 失败: {e}"))?;
        writer
            .write_all(b"\"")
            .map_err(|e| format!("写入 CSV 失败: {e}"))?;
    }
    writer
        .write_all(b"\n")
        .map_err(|e| format!("写入 CSV 失败: {e}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_zip_slip_paths() {
        assert!(safe_relative_path("../escape.txt").is_err());
        assert!(safe_relative_path("/absolute.txt").is_err());
        assert_eq!(
            safe_relative_path("folder\\ok.txt").unwrap(),
            PathBuf::from("folder/ok.txt")
        );
    }

    #[test]
    fn renames_original_marker_without_unsupported_regex() {
        assert_eq!(
            renamed_text_file("【原文】2026-11-06_新闻.txt", "【编辑】"),
            "【编辑】新闻.txt"
        );
        assert_eq!(
            renamed_text_file("【原文】11月新闻.txt", "【编辑】"),
            "【编辑】11月新闻.txt"
        );
    }

    #[test]
    fn creates_collision_free_names() {
        let dir = std::env::temp_dir().join(format!("autosen-test-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("a.txt"), b"one").unwrap();
        fs::write(dir.join("a_1.txt"), b"two").unwrap();
        assert_eq!(unique_destination(&dir, "a.txt"), dir.join("a_2.txt"));
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn processes_utf8_zip_end_to_end() {
        let root = std::env::temp_dir().join(format!(
            "autosen-archive-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let output = root.join("output");
        fs::create_dir_all(&output).unwrap();
        let archive_path = root.join("sample.zip");
        let archive_file = fs::File::create(&archive_path).unwrap();
        let mut archive = zip::ZipWriter::new(archive_file);
        archive
            .start_file(
                "【原文】2026-11-06_新闻.txt",
                zip::write::FileOptions::default(),
            )
            .unwrap();
        archive
            .write_all("正文\n主题词：测试\n".as_bytes())
            .unwrap();
        archive.finish().unwrap();

        let config = AppConfig {
            pre_fix: "【编辑】".into(),
            target_dir: output.to_string_lossy().into_owned(),
            comment: "插入内容".into(),
            ..AppConfig::default()
        };
        process_archive(&archive_path.to_string_lossy(), &config).unwrap();

        assert!(!archive_path.exists());
        let result = fs::read_to_string(output.join("【编辑】新闻.txt")).unwrap();
        assert_eq!(result, "正文\n插入内容\n主题词：测试\n");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn keeps_archive_when_no_text_file_can_be_processed() {
        let root = std::env::temp_dir().join(format!(
            "autosen-empty-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let output = root.join("output");
        fs::create_dir_all(&output).unwrap();
        let archive_path = root.join("image-only.zip");
        let archive_file = fs::File::create(&archive_path).unwrap();
        let mut archive = zip::ZipWriter::new(archive_file);
        archive
            .start_file("image.png", zip::write::FileOptions::default())
            .unwrap();
        archive.write_all(b"not-an-image").unwrap();
        archive.finish().unwrap();

        let config = AppConfig {
            target_dir: output.to_string_lossy().into_owned(),
            monitor_only_txt: false,
            ..AppConfig::default()
        };
        assert!(process_archive(&archive_path.to_string_lossy(), &config).is_err());
        assert!(archive_path.exists());
        fs::remove_dir_all(root).unwrap();
    }
}
