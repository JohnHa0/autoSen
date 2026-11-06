// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod core;
use core::{load_config, log_message, process_archive, save_config, AppConfig};

use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::{mpsc, Mutex};
use std::time::Duration;
use tauri::Manager;
use tauri::{CustomMenuItem, SystemTray, SystemTrayEvent, SystemTrayMenu, SystemTrayMenuItem};

struct AppState {
    config: Mutex<AppConfig>,
    monitor_tx: mpsc::Sender<AppConfig>,
}

#[tauri::command]
fn get_config(state: tauri::State<AppState>) -> AppConfig {
    state.config.lock().unwrap().clone()
}

#[tauri::command]
fn update_config(new_config: AppConfig, state: tauri::State<AppState>) -> Result<(), String> {
    save_config(&new_config)?;
    *state.config.lock().map_err(|_| "配置锁已损坏")? = new_config.clone();
    state
        .monitor_tx
        .send(new_config)
        .map_err(|_| "无法重新加载监控配置".to_string())
}

#[tauri::command]
fn open_path(path: String) -> Result<(), String> {
    let path_obj = std::path::Path::new(&path);
    if !path_obj.exists() {
        return Err("路径不存在".into());
    }

    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn handle_context_menu(action: String) -> Result<String, String> {
    let _ = action;
    Err("麒麟不同桌面环境的右键菜单机制不一致，此版本未启用该功能".into())
}

#[tauri::command]
fn open_log_file() -> Result<(), String> {
    let mut path = dirs::config_dir().unwrap_or_else(|| std::path::PathBuf::from("."));
    path.push("autoSen");
    path.push("logs");
    std::fs::create_dir_all(&path).ok();
    path.push("autosen.log");

    // Ensure file exists
    if !path.exists() {
        std::fs::write(&path, "[System] Log file created.\n").ok();
    }

    let path_str = path.to_string_lossy().to_string();
    open_path(path_str)
}

fn start_monitor(initial_config: AppConfig) -> mpsc::Sender<AppConfig> {
    let (config_tx, config_rx) = mpsc::channel::<AppConfig>();
    std::thread::spawn(move || {
        let mut config = initial_config;
        let mut pending: HashMap<PathBuf, ((u64, Option<std::time::SystemTime>), u8)> =
            HashMap::new();
        let mut handled: HashMap<PathBuf, (u64, Option<std::time::SystemTime>)> = HashMap::new();
        log_monitor_state(&config);

        loop {
            match config_rx.recv_timeout(Duration::from_millis(500)) {
                Ok(updated) => {
                    config = updated;
                    pending.clear();
                    handled.clear();
                    log_monitor_state(&config);
                    continue;
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => break,
                Err(mpsc::RecvTimeoutError::Timeout) => {}
            }

            if !config.enable_monitor {
                continue;
            }
            poll_monitor_directory(&config, &mut pending, &mut handled);
        }
    });
    config_tx
}

type FileSignature = (u64, Option<std::time::SystemTime>);

fn log_monitor_state(config: &AppConfig) {
    if !config.enable_monitor {
        log_message("INFO", "目录监控已停止", &config.log_retention_days);
        return;
    }
    let path = PathBuf::from(&config.monitor_dir);
    if path.is_dir() {
        log_message(
            "INFO",
            &format!("开始监听: {}", path.display()),
            &config.log_retention_days,
        );
    } else {
        log_message(
            "ERROR",
            &format!("监听目录不存在: {}", path.display()),
            &config.log_retention_days,
        );
    }
}

fn poll_monitor_directory(
    config: &AppConfig,
    pending: &mut HashMap<PathBuf, (FileSignature, u8)>,
    handled: &mut HashMap<PathBuf, FileSignature>,
) {
    let directory = PathBuf::from(&config.monitor_dir);
    let entries = match std::fs::read_dir(&directory) {
        Ok(entries) => entries,
        Err(_) => return,
    };
    let mut ready = Vec::new();
    for entry in entries.flatten() {
        let path = entry.path();
        if !is_zip_path(&path) {
            continue;
        }
        let metadata = match entry.metadata() {
            Ok(metadata) if metadata.is_file() => metadata,
            _ => continue,
        };
        let signature = (metadata.len(), metadata.modified().ok());
        if handled.get(&path) == Some(&signature) {
            continue;
        }
        let state = pending.entry(path.clone()).or_insert((signature, 0));
        if state.0 == signature {
            state.1 = state.1.saturating_add(1);
            if state.1 >= 3 {
                ready.push((path, signature));
            }
        } else {
            *state = (signature, 0);
        }
    }
    pending.retain(|path, _| path.is_file());

    for (path, signature) in ready {
        pending.remove(&path);
        let display = path.to_string_lossy().to_string();
        match process_archive(&display, config) {
            Ok(()) => log_message(
                "INFO",
                &format!("处理完成: {display}"),
                &config.log_retention_days,
            ),
            Err(error) => {
                handled.insert(path, signature);
                log_message(
                    "ERROR",
                    &format!("处理失败: {display}; {error}"),
                    &config.log_retention_days,
                );
            }
        }
    }
}

fn is_zip_path(path: &std::path::Path) -> bool {
    path.extension()
        .map(|extension| extension.to_string_lossy().eq_ignore_ascii_case("zip"))
        .unwrap_or(false)
}

fn main() {
    let config = load_config();
    let config_state = AppConfig { ..config.clone() };

    // For CLI Mode
    let args: Vec<String> = std::env::args().collect();
    if args.len() > 2 && args[1] == "--process-file" {
        let file_path = &args[2];
        if config.target_dir.is_empty() {
            println!("Error: Target directory not set. Please configure in the UI.");
            std::process::exit(1);
        }
        if let Err(e) = process_archive(file_path, &config) {
            eprintln!("Process Error: {}", e);
            std::process::exit(2);
        }
        std::process::exit(0);
    }

    let monitor_tx = start_monitor(config.clone());

    let quit = CustomMenuItem::new("quit".to_string(), "退出");
    let show = CustomMenuItem::new("show".to_string(), "显示主界面");
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
    let tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "quit" => {
                    std::process::exit(0);
                }
                "show" => {
                    let window = app.get_window("main").unwrap();
                    window.show().unwrap();
                    window.set_focus().unwrap();
                }
                _ => {}
            },
            SystemTrayEvent::LeftClick { .. } => {
                let window = app.get_window("main").unwrap();
                window.show().unwrap();
                window.set_focus().unwrap();
            }
            _ => {}
        })
        .manage(AppState {
            config: Mutex::new(config_state),
            monitor_tx,
        })
        .invoke_handler(tauri::generate_handler![
            get_config,
            update_config,
            open_path,
            handle_context_menu,
            open_log_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
