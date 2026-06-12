// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod core;
use core::{AppConfig, load_config, save_config, process_archive};

use tauri::{Manager, Emitter};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder, MouseButton, MouseButtonState};
use std::sync::{Arc, Mutex};
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

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            config: Mutex::new(config_state),
        })
        .setup(|app| {
            let quit_i = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let show_i = MenuItem::with_id(app, "show", "显示主界面", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &quit_i])?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "quit" => std::process::exit(0),
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let tauri::tray::TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_config, update_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
