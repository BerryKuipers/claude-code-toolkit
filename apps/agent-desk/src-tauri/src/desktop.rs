use crate::executables::agent_label;
use crate::file_store::absolute;
use crate::services::{Services, argument, identifier, text};
use crate::types::{DeskResult, TerminalEvent};
use serde_json::Value;
use std::path::PathBuf;
use std::sync::Arc;
use tauri::{Manager, State, WebviewWindow, WebviewWindowBuilder, ipc::Channel};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_opener::OpenerExt;

fn trusted_url(url: &reqwest::Url) -> bool {
    if url.port().is_none()
        && ((url.scheme() == "tauri" && url.host_str() == Some("localhost"))
            || (matches!(url.scheme(), "http" | "https")
                && url.host_str() == Some("tauri.localhost")))
    {
        return true;
    }
    cfg!(debug_assertions)
        && url.scheme() == "http"
        && url.host_str() == Some("127.0.0.1")
        && url.port() == Some(1420)
}

fn trusted_window(window: &WebviewWindow) -> DeskResult<()> {
    if window.label() != "main" || !trusted_url(&window.url().map_err(|e| e.to_string())?) {
        return Err("Untrusted renderer request.".into());
    }
    Ok(())
}

#[tauri::command]
async fn desk_invoke(
    window: WebviewWindow,
    state: State<'_, Arc<Services>>,
    method: String,
    args: Vec<Value>,
) -> DeskResult<Value> {
    trusted_window(&window)?;
    let services = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || match method.as_str() {
        "pickDirectory" if args.is_empty() => Ok(window
            .app_handle()
            .dialog()
            .file()
            .set_title("Choose project folder")
            .blocking_pick_folder()
            .and_then(|p| p.into_path().ok())
            .map(|p| Value::String(p.to_string_lossy().into_owned()))
            .unwrap_or(Value::Null)),
        "revealPath" if args.len() == 1 => {
            let path: String = argument(&args, 0)?;
            text(&path, 32_768)?;
            if !PathBuf::from(&path).is_absolute() || !PathBuf::from(&path).exists() {
                return Err("An existing absolute file path is required.".into());
            }
            window
                .app_handle()
                .opener()
                .reveal_item_in_dir(path)
                .map_err(|e| e.to_string())?;
            Ok(Value::Null)
        }
        "openExternal" if args.len() == 1 => {
            let value: String = argument(&args, 0)?;
            text(&value, 32_768)?;
            let url = reqwest::Url::parse(&value).map_err(|e| e.to_string())?;
            if !matches!(url.scheme(), "https" | "http")
                || !url.username().is_empty()
                || url.password().is_some()
            {
                return Err(
                    "Only HTTP(S) links without embedded credentials can be opened.".into(),
                );
            }
            window
                .app_handle()
                .opener()
                .open_url(url.to_string(), None::<&str>)
                .map_err(|e| e.to_string())?;
            Ok(Value::Null)
        }
        "exportSession" if args.len() == 1 => {
            let transcript = services.transcript(&identifier(&args, 0)?)?;
            let mut name: String = transcript
                .session
                .title
                .chars()
                .filter(|c| c.is_alphanumeric() || matches!(c, ' ' | '_' | '-'))
                .take(100)
                .collect();
            if name.is_empty() {
                name = "session".into();
            }
            let Some(path) = window
                .app_handle()
                .dialog()
                .file()
                .set_file_name(format!("{name}.md"))
                .add_filter("Markdown", &["md"])
                .blocking_save_file()
            else {
                return Ok(Value::Null);
            };
            let path = path.into_path().map_err(|e| e.to_string())?;
            let mut output = format!(
                "# {}\n\nAgent: {}\nProject: {}\n\n",
                transcript.session.title,
                agent_label(&transcript.session.agent),
                transcript.session.project_path
            );
            for message in transcript.messages {
                output.push_str(&format!(
                    "## {}{}\n\n{}\n\n",
                    message.role,
                    message
                        .tool_name
                        .map(|n| format!(" · {n}"))
                        .unwrap_or_default(),
                    message.content
                ));
            }
            for warning in transcript.warnings {
                output.push_str(&format!("> {warning}\n"));
            }
            let mut options = std::fs::OpenOptions::new();
            options.write(true).create(true).truncate(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt;
                options.mode(0o600);
            }
            use std::io::Write;
            options
                .open(&path)
                .and_then(|mut file| file.write_all(output.as_bytes()))
                .map_err(|e| e.to_string())?;
            Ok(Value::String(path.to_string_lossy().into_owned()))
        }
        _ => services.dispatch(&method, args),
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
fn terminal_subscribe(
    window: WebviewWindow,
    state: State<'_, Arc<Services>>,
    on_event: Channel<TerminalEvent>,
) -> DeskResult<()> {
    trusted_window(&window)?;
    state.terminals.subscribe(Arc::new(move |event| {
        let _ = on_event.send(event);
    }));
    Ok(())
}

#[tauri::command]
async fn desktop_close(window: WebviewWindow, state: State<'_, Arc<Services>>) -> DeskResult<()> {
    trusted_window(&window)?;
    let services = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || services.close())
        .await
        .map_err(|e| e.to_string())?;
    window.destroy().map_err(|e| e.to_string())
}

pub fn run() {
    let builder = tauri::Builder::default();
    #[cfg(target_os = "macos")]
    let builder = builder.menu(macos_menu).on_menu_event(|app, event| {
        if event.id().as_ref() == "agent-desk-quit"
            && let Some(window) = app.get_webview_window("main")
        {
            let _ = window.close();
        }
    });
    let builder = builder
        .plugin(tauri_plugin_single_instance::init(|app, _, _| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            desk_invoke,
            terminal_subscribe,
            desktop_close
        ])
        .setup(|app| {
            let home = std::env::var_os("AGENT_DESK_HOME")
                .map(PathBuf::from)
                .or_else(dirs::home_dir)
                .ok_or("Cannot determine the home directory.")?;
            let home = absolute(&home);
            let data_dir = std::env::var_os("AGENT_DESK_DATA_DIR")
                .map(PathBuf::from)
                .unwrap_or_else(|| {
                    dirs::config_dir()
                        .unwrap_or_else(|| home.join(".config"))
                        .join("agent-desk")
                });
            let data_dir = absolute(&data_dir);
            let services =
                Arc::new(Services::new(home, data_dir.clone()).map_err(std::io::Error::other)?);
            app.manage(services);
            let window = WebviewWindowBuilder::from_config(app, &app.config().app.windows[0])?
                .data_directory(data_dir.join("webview"))
                .on_navigation(trusted_url)
                .on_new_window(|_, _| tauri::webview::NewWindowResponse::Deny)
                .build()?;
            let _ = window.show();
            Ok(())
        });
    match builder.build(tauri::generate_context!()) {
        Ok(app) => app.run(|app, event| {
            if matches!(event, tauri::RunEvent::Exit) {
                app.state::<Arc<Services>>().close();
            }
        }),
        Err(error) => {
            eprintln!("Agent Desk could not start: {error}");
            std::process::exit(1);
        }
    }
}

#[cfg(target_os = "macos")]
fn macos_menu(app: &tauri::AppHandle) -> tauri::Result<tauri::menu::Menu<tauri::Wry>> {
    use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};
    let menu = Menu::default(app)?;
    menu.remove_at(0)?;
    let quit = MenuItem::with_id(
        app,
        "agent-desk-quit",
        "Quit Agent Desk",
        true,
        Some("CmdOrCtrl+Q"),
    )?;
    let application = Submenu::with_items(
        app,
        &app.package_info().name,
        true,
        &[
            &PredefinedMenuItem::about(
                app,
                None,
                Some(AboutMetadata {
                    name: Some(app.package_info().name.clone()),
                    version: Some(app.package_info().version.to_string()),
                    ..Default::default()
                }),
            )?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::services(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::hide(app, None)?,
            &PredefinedMenuItem::hide_others(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &quit,
        ],
    )?;
    menu.insert(&application, 0)?;
    Ok(menu)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn native_origin_rejects_remote_pages_and_url_lookalikes() {
        for url in [
            "https://example.test",
            "http://tauri.localhost.evil.test",
            "file:///etc/passwd",
            "https://localhost:4433",
        ] {
            assert!(!trusted_url(&reqwest::Url::parse(url).unwrap()));
        }
        assert!(trusted_url(
            &reqwest::Url::parse("http://tauri.localhost/").unwrap()
        ));
        assert!(trusted_url(
            &reqwest::Url::parse("tauri://localhost/").unwrap()
        ));
    }
}
