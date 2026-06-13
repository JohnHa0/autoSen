use std::path::{Path, PathBuf};
use std::fs;
use std::io::Write;
use zip::ZipArchive;
use encoding_rs::{GBK, UTF_8};
use regex::Regex;
use chrono::Local;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Default)]
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

pub fn get_config_path() -> PathBuf {
    let mut path = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    path.push("autoSen");
    fs::create_dir_all(&path).ok();
    path.push("config.json");
    path
}

pub fn load_config() -> AppConfig {
    let path = get_config_path();
    if let Ok(content) = fs::read_to_string(path) {
        if let Ok(config) = serde_json::from_str(&content) {
            return config;
        }
    }
    AppConfig {
        pre_fix: "（文件前缀名）".into(),
        csv_tmpl: "{author}_上报条目_{year}-{month}.csv".into(),
        insert_pos: "before_keyword".into(),
        file_encoding: "auto".into(),
        log_retention_days: "7".into(),
        monitor_only_txt: true,
        ..Default::default()
    }
}

pub fn save_config(config: &AppConfig) -> Result<(), String> {
    let path = get_config_path();
    let content = serde_json::to_string_pretty(config).map_err(|e| e.to_string())?;
    fs::write(path, content).map_err(|e| e.to_string())
}

pub fn process_archive(archive_path: &str, config: &AppConfig) -> Result<(), String> {
    let path = Path::new(archive_path);
    if !path.exists() {
        return Err("Archive does not exist".into());
    }

    let target_dir = Path::new(&config.target_dir);
    if config.target_dir.is_empty() {
        return Err("Target directory not configured".into());
    }
    fs::create_dir_all(target_dir).ok();

    // 1. Unzip
    let file = fs::File::open(path).map_err(|e| e.to_string())?;
    let mut archive = ZipArchive::new(file).map_err(|e| e.to_string())?;

    let extract_folder = path.with_extension("extracted");
    fs::create_dir_all(&extract_folder).ok();

    for i in 0..archive.len() {
        let mut file = archive.by_index(i).map_err(|e| e.to_string())?;
        
        let _outpath = match file.enclosed_name() {
            Some(path) => path.to_owned(),
            None => continue,
        };

        // Name decoding for CP437/GBK issues from Windows
        let raw_name = file.name_raw();
        let (decoded, _, _) = GBK.decode(raw_name);
        let fixed_name = decoded.to_string();
        
        let target_path = extract_folder.join(fixed_name);

        if (*file.name()).ends_with('/') {
            fs::create_dir_all(&target_path).unwrap();
        } else {
            if let Some(p) = target_path.parent() {
                fs::create_dir_all(p).unwrap();
            }
            let mut outfile = fs::File::create(&target_path).unwrap();
            std::io::copy(&mut file, &mut outfile).unwrap();
        }
    }

    // 2. Process Files
    let re = Regex::new(r"^【原文】(?:(?!\d+月)[\d\s\-_.])+").unwrap();
    
    for entry in walkdir::WalkDir::new(&extract_folder).into_iter().filter_map(|e| e.ok()) {
        let entry_path = entry.path();
        if entry_path.is_file() {
            if let Some(ext) = entry_path.extension() {
                if ext == "txt" {
                    let file_name = entry_path.file_name().unwrap().to_string_lossy().to_string();
                    
                    let mut new_name = re.replace(&file_name, &config.pre_fix).to_string();
                    if new_name == file_name && file_name.starts_with("【原文】") {
                        new_name = file_name.replacen("【原文】", &config.pre_fix, 1);
                    }

                    let mut final_path = target_dir.join(&new_name);
                    if final_path.exists() {
                        let stem = Path::new(&new_name).file_stem().unwrap().to_string_lossy();
                        let ext = Path::new(&new_name).extension().unwrap().to_string_lossy();
                        let ts = Local::now().timestamp();
                        final_path = target_dir.join(format!("{}_{}.{}", stem, ts, ext));
                    }

                    fs::rename(entry_path, &final_path).map_err(|e| e.to_string())?;

                    // Process text content
                    process_text_file(&final_path, config)?;
                    
                    // CSV logging
                    let opt_name = new_name.replace(&config.pre_fix, "").replace(".txt", "");
                    update_csv_summary(&opt_name, config)?;
                }
            }
        }
    }

    // 3. Cleanup
    fs::remove_dir_all(&extract_folder).ok();
    fs::remove_file(path).ok();

    Ok(())
}

fn process_text_file(file_path: &Path, config: &AppConfig) -> Result<(), String> {
    if config.comment.is_empty() { return Ok(()); }

    let bytes = fs::read(file_path).map_err(|e| e.to_string())?;
    
    // Auto detect encoding
    let (content, enc, _) = if config.file_encoding == "gbk" {
        GBK.decode(&bytes)
    } else if config.file_encoding == "utf-8" {
        UTF_8.decode(&bytes)
    } else {
        let (c, e, _) = UTF_8.decode(&bytes);
        if c.contains('\u{FFFD}') {
            GBK.decode(&bytes)
        } else {
            (c, e, false)
        }
    };

    let lines: Vec<&str> = content.lines().collect();
    let mut out_lines = Vec::new();
    let mut inserted = false;

    if config.insert_pos == "at_eof" {
        out_lines = lines.clone();
        out_lines.push(&config.comment);
    } else {
        for line in lines {
            if line.starts_with("主题词") && !inserted {
                out_lines.push(&config.comment);
                inserted = true;
            }
            out_lines.push(line);
        }
        if !inserted {
            out_lines.push(&config.comment);
        }
    }

    let out_content = out_lines.join("\n");
    let out_bytes = if enc == GBK {
        let (b, _, _) = GBK.encode(&out_content);
        b.into_owned()
    } else {
        out_content.into_bytes()
    };

    fs::write(file_path, out_bytes).map_err(|e| e.to_string())?;
    Ok(())
}

fn update_csv_summary(opt_name: &str, config: &AppConfig) -> Result<(), String> {
    if config.csv_folder.is_empty() { return Ok(()); }

    fs::create_dir_all(&config.csv_folder).ok();

    let now = Local::now();
    let year = now.format("%Y").to_string();
    let month = now.format("%m").to_string();
    let day = now.format("%d").to_string();

    let csv_name = config.csv_tmpl
        .replace("{author}", &config.author)
        .replace("{year}", &year)
        .replace("{month}", &month)
        .replace("{day}", &day);

    let csv_path = Path::new(&config.csv_folder).join(csv_name);
    let exists = csv_path.exists();

    let mut file = fs::OpenOptions::new()
        .write(true)
        .append(true)
        .create(true)
        .open(&csv_path)
        .map_err(|e| e.to_string())?;

    if !exists {
        // write BOM for Excel UTF-8
        file.write_all(b"\xEF\xBB\xBF").ok();
        let mut wtr = csv::Writer::from_writer(&mut file);
        wtr.write_record(&["日期", "作者", "文件名称"]).ok();
    }

    let mut wtr = csv::Writer::from_writer(file);
    let date_str = now.format("%Y-%m-%d").to_string();
    wtr.write_record(&[date_str, config.author.clone(), opt_name.to_string()]).ok();
    
    Ok(())
}
