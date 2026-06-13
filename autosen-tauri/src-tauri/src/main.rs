// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod core;
use core::{AppConfig, load_config, save_config, process_archive};

use tauri::Manager;
use tauri::{CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayMenuItem, SystemTrayEvent};
use std::sync::Mutex;
use notify::{Watcher, RecursiveMode, EventKind};
use std::path::PathBuf;

struct AppState {
    config: Mutex<AppConfig>,
}

#[tauri::command]
fn get_config(state: tauri::State<AppState>) -> AppConfig {
    state.config.lock().unwrap().clone()
}

#[tauri::command]
fn update_config(new_config: AppConfig, state: tauri::State<AppState>) -> Result<(), String> {
    *state.config.lock().unwrap() = new_config.clone();
    save_config(&new_config)
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
    // 跨平台集成逻辑 (后续可拓展)
    if action == "add" {
        Ok("已发送集成请求 (需管理员权限生效)".into())
    } else {
        Ok("已清理系统右键菜单集成".into())
    }
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

fn start_monitor(config: AppConfig) {
    if !config.enable_monitor || config.monitor_dir.is_empty() { return; }
    
    let path = PathBuf::from(&config.monitor_dir);
    if !path.exists() { return; }

    std::thread::spawn(move || {
        let (tx, rx) = std::sync::mpsc::channel();
        let mut watcher = notify::recommended_watcher(tx).unwrap();
        watcher.watch(&path, RecursiveMode::NonRecursive).unwrap();

        for res in rx {
            if let Ok(event) = res {
                if let EventKind::Create(_) = event.kind {
                    for path in event.paths {
                        if path.extension().unwrap_or_default() == "zip" {
                            let _ = process_archive(&path.to_string_lossy(), &config);
                        }
                    }
                }
            }
        }
    });
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
            println!("Process Error: {}", e);
        }
        std::process::exit(0);
    }

    start_monitor(config.clone());

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
            SystemTrayEvent::MenuItemClick { id, .. } => {
                match id.as_str() {
                    "quit" => {
                        std::process::exit(0);
                    }
                    "show" => {
                        let window = app.get_window("main").unwrap();
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                    _ => {}
                }
            }
            SystemTrayEvent::LeftClick { .. } => {
                let window = app.get_window("main").unwrap();
                window.show().unwrap();
                window.set_focus().unwrap();
            }
            _ => {}
        })
        .manage(AppState {
            config: Mutex::new(config_state),
        })
        .invoke_handler(tauri::generate_handler![get_config, update_config, open_path, handle_context_menu, open_log_file])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
