use crate::types::{AgentInstall, AppSettings, DeskResult};
use regex::Regex;
use std::collections::HashMap;
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Command, Stdio};
use std::time::{Duration, Instant};
use wait_timeout::ChildExt;

#[derive(Clone, Debug)]
pub struct Executable {
    pub file: PathBuf,
    pub args: Vec<String>,
}

pub fn agent_label(id: &str) -> &str {
    match id {
        "claude" => "Claude Code",
        "codex" => "Codex",
        "gemini" => "Gemini CLI",
        "antigravity" => "Antigravity",
        _ => id,
    }
}

pub fn native_path(path: PathBuf) -> PathBuf {
    #[cfg(windows)]
    {
        let text = path.to_string_lossy();
        if let Some(rest) = text.strip_prefix(r"\\?\UNC\") {
            return PathBuf::from(format!(r"\\{rest}"));
        }
        if let Some(rest) = text.strip_prefix(r"\\?\") {
            return PathBuf::from(rest);
        }
    }
    path
}

pub fn find_executable(
    command: &str,
    env: &HashMap<String, String>,
    home: &Path,
) -> DeskResult<PathBuf> {
    if command.is_empty() || command.contains(['\0', '\n', '\r']) {
        return Err("Choose an executable path or command name, without arguments.".into());
    }
    let direct = Path::new(command).is_absolute() || command.contains(['/', '\\']);
    let mut paths: Vec<PathBuf> = if direct {
        vec![PathBuf::new()]
    } else {
        let value = env
            .iter()
            .find(|(key, _)| key.eq_ignore_ascii_case("PATH"))
            .map(|(_, value)| value.as_str())
            .unwrap_or("");
        std::env::split_paths(value)
            .filter(|p| !p.as_os_str().is_empty())
            .collect()
    };
    if !direct {
        paths.extend([
            home.join(".local/bin"),
            home.join(".bun/bin"),
            home.join(".npm-global/bin"),
        ]);
        if cfg!(windows) {
            paths.push(
                env.get("APPDATA")
                    .map(PathBuf::from)
                    .unwrap_or_else(|| home.join("AppData/Roaming"))
                    .join("npm"),
            );
            paths.push(home.join("AppData/Local/Microsoft/WinGet/Links"));
        } else {
            paths.extend([
                PathBuf::from("/opt/homebrew/bin"),
                PathBuf::from("/usr/local/bin"),
                PathBuf::from("/usr/bin"),
            ]);
        }
    }
    let extensions: &[&str] = if cfg!(windows) && Path::new(command).extension().is_none() {
        &[".exe", ".com", ".cmd", ".bat", ""]
    } else {
        &[""]
    };
    for root in paths {
        for ext in extensions {
            let candidate = root.join(format!("{command}{ext}"));
            let Ok(meta) = candidate.metadata() else {
                continue;
            };
            if !meta.is_file() {
                continue;
            }
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let js = matches!(
                    candidate.extension().and_then(|v| v.to_str()),
                    Some("js" | "cjs" | "mjs")
                );
                if meta.permissions().mode() & 0o111 == 0 && !js {
                    continue;
                }
            }
            return std::fs::canonicalize(&candidate)
                .map(native_path)
                .map_err(|e| e.to_string());
        }
    }
    Err(format!(
        "Executable '{command}' was not found. Install it or choose its full path in Settings."
    ))
}

pub fn npm_shim_target(content: &str, shim_path: &Path) -> Option<PathBuf> {
    let regex = Regex::new(r#"(?i)"%dp0%[\\/]([^"\r\n]+\.(?:[cm]?js|exe))""#).ok()?;
    let captures = regex.captures(content)?;
    let relative = captures.get(1)?.as_str().replace('\\', "/");
    if relative.split('/').any(|part| part == "..")
        || !relative.to_lowercase().starts_with("node_modules/")
    {
        return None;
    }
    Some(shim_path.parent()?.join(relative))
}

pub fn resolve_executable(
    command: &str,
    env: &HashMap<String, String>,
    home: &Path,
) -> DeskResult<Executable> {
    let file = find_executable(command, env, home)?;
    let ext = file
        .extension()
        .and_then(|v| v.to_str())
        .unwrap_or("")
        .to_lowercase();
    if cfg!(windows) && matches!(ext.as_str(), "cmd" | "bat") {
        if file.metadata().map_err(|e| e.to_string())?.len() > 1_000_000 {
            return Err("The command launcher is too large.".into());
        }
        let content = std::fs::read_to_string(&file).map_err(|e| e.to_string())?;
        let target = npm_shim_target(&content, &file).ok_or_else(|| format!("The launcher '{}' is not a supported npm shim. Select the native executable or JavaScript CLI entry point in Settings.", file.display()))?;
        if !target.is_file() {
            return Err("The npm launcher's entry point no longer exists.".into());
        }
        if target
            .extension()
            .and_then(|v| v.to_str())
            .is_some_and(|s| s.eq_ignore_ascii_case("exe"))
        {
            return Ok(Executable {
                file: target,
                args: vec![],
            });
        }
        let sibling = file.parent().unwrap_or(home).join("node.exe");
        let node = find_executable(&sibling.to_string_lossy(), env, home)
            .or_else(|_| find_executable("node", env, home))?;
        return Ok(Executable {
            file: node,
            args: vec![target.to_string_lossy().into_owned()],
        });
    }
    if matches!(ext.as_str(), "js" | "cjs" | "mjs") {
        return Ok(Executable {
            file: find_executable("node", env, home)?,
            args: vec![file.to_string_lossy().into_owned()],
        });
    }
    Ok(Executable { file, args: vec![] })
}

pub fn hide_command(command: &mut Command) {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    #[cfg(not(windows))]
    let _ = command;
}

pub fn detect_agents(settings: &AppSettings, home: &Path) -> Vec<AgentInstall> {
    let env: HashMap<String, String> = std::env::vars().collect();
    std::thread::scope(|scope| {
        let jobs: Vec<_> = ["claude", "codex", "gemini", "antigravity"].into_iter().map(|id| {
            let env = &env;
            scope.spawn(move || {
                let name = settings.agent_commands.get(id).cloned().unwrap_or_else(|| id.to_string());
                let mut item = AgentInstall { id: id.into(), label: agent_label(id).into(), command: name.clone(), ..Default::default() };
                match resolve_executable(&name, env, home) {
                    Ok(executable) => {
                        item.available = true;
                        item.path = Some(executable.file.to_string_lossy().into_owned());
                        match version(&executable) {
                            Ok(value) => item.version = Some(value),
                            Err(_) => item.error = Some("Executable found; its version command did not finish successfully.".into()),
                        }
                    }
                    Err(error) => item.error = Some(error),
                }
                item
            })
        }).collect();
        jobs.into_iter().filter_map(|job| job.join().ok()).collect()
    })
}

fn version(executable: &Executable) -> DeskResult<String> {
    version_with_timeout(executable, Duration::from_secs(5))
}

fn version_with_timeout(executable: &Executable, timeout: Duration) -> DeskResult<String> {
    let deadline = Instant::now() + timeout;
    let run_deadline = deadline - timeout.min(Duration::from_secs(4)) / 4;
    let mut command = Command::new(&executable.file);
    command
        .args(&executable.args)
        .arg("--version")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    hide_command(&mut command);
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    let mut child = command.spawn().map_err(|error| error.to_string())?;
    let mut output = child.stdout.take();
    let result = (|| -> DeskResult<Vec<u8>> {
        let output = output.as_mut().ok_or("No version output")?;
        prepare_version_output(output).map_err(|error| error.to_string())?;
        let mut bytes = Vec::new();
        let mut complete = false;
        loop {
            read_version_output(output, &mut bytes, &mut complete)
                .map_err(|error| error.to_string())?;
            if let Some(status) = child.try_wait().map_err(|error| error.to_string())? {
                if !status.success() {
                    return Err("Version command failed".into());
                }
                read_version_output(output, &mut bytes, &mut complete)
                    .map_err(|error| error.to_string())?;
                return Ok(bytes);
            }
            if Instant::now() >= run_deadline {
                return Err("Version command timed out".into());
            }
            std::thread::sleep(
                Duration::from_millis(10)
                    .min(run_deadline.saturating_duration_since(Instant::now())),
            );
        }
    })();
    stop_version_process(&mut child, deadline);
    drop(output);
    let bytes = result?;
    let text = String::from_utf8_lossy(&bytes);
    let ansi = Regex::new(r"\x1b\[[0-9;]*m").map_err(|error| error.to_string())?;
    let text: String = ansi
        .replace_all(text.trim(), "")
        .chars()
        .take(160)
        .collect();
    if text.is_empty() {
        return Err("No version output".into());
    }
    Ok(text)
}

fn prepare_version_output(output: &ChildStdout) -> io::Result<()> {
    #[cfg(unix)]
    {
        use std::os::fd::AsRawFd;
        let descriptor = output.as_raw_fd();
        let flags = unsafe { libc::fcntl(descriptor, libc::F_GETFL) };
        if flags < 0
            || unsafe { libc::fcntl(descriptor, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0
        {
            return Err(io::Error::last_os_error());
        }
    }
    #[cfg(not(unix))]
    let _ = output;
    Ok(())
}

fn version_read(output: &mut ChildStdout, buffer: &mut [u8]) -> io::Result<Option<usize>> {
    #[cfg(windows)]
    {
        use std::os::windows::io::AsRawHandle;
        use windows_sys::Win32::Foundation::{ERROR_BROKEN_PIPE, ERROR_NO_DATA};
        use windows_sys::Win32::System::Pipes::PeekNamedPipe;
        let mut available = 0;
        let success = unsafe {
            PeekNamedPipe(
                output.as_raw_handle(),
                std::ptr::null_mut(),
                0,
                std::ptr::null_mut(),
                &mut available,
                std::ptr::null_mut(),
            )
        };
        if success == 0 {
            let error = io::Error::last_os_error();
            if matches!(
                error.raw_os_error().map(|code| code as u32),
                Some(ERROR_BROKEN_PIPE | ERROR_NO_DATA)
            ) {
                return Ok(Some(0));
            }
            return Err(error);
        }
        if available == 0 {
            return Ok(None);
        }
        let count = buffer.len().min(available as usize);
        output.read(&mut buffer[..count]).map(Some)
    }
    #[cfg(not(windows))]
    {
        match output.read(buffer) {
            Err(error)
                if error.kind() == io::ErrorKind::WouldBlock
                    || error.kind() == io::ErrorKind::Interrupted =>
            {
                Ok(None)
            }
            result => result.map(Some),
        }
    }
}

fn read_version_output(
    output: &mut ChildStdout,
    bytes: &mut Vec<u8>,
    complete: &mut bool,
) -> io::Result<()> {
    let mut buffer = [0_u8; 4096];
    for _ in 0..16 {
        let Some(count) = version_read(output, &mut buffer)? else {
            break;
        };
        if count == 0 {
            break;
        }
        if *complete {
            continue;
        }
        for byte in &buffer[..count] {
            if *byte == b'\n' {
                if bytes.iter().any(|byte| !byte.is_ascii_whitespace()) {
                    *complete = true;
                    break;
                }
                bytes.clear();
            } else if bytes.len() < 65_536 {
                bytes.push(*byte);
            } else {
                *complete = true;
                break;
            }
        }
    }
    Ok(())
}

fn stop_version_process(child: &mut Child, deadline: Instant) {
    #[cfg(unix)]
    unsafe {
        libc::kill(-(child.id() as i32), libc::SIGKILL);
    }
    #[cfg(windows)]
    {
        if child.try_wait().ok().flatten().is_none() {
            let executable = std::env::var_os("SystemRoot")
                .map(PathBuf::from)
                .unwrap_or_else(|| PathBuf::from(r"C:\Windows"))
                .join("System32/taskkill.exe");
            let mut command = Command::new(executable);
            command
                .args(["/PID", &child.id().to_string(), "/T", "/F"])
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null());
            hide_command(&mut command);
            if let Ok(mut tree_kill) = command.spawn() {
                let budget = deadline.saturating_duration_since(Instant::now()) / 2;
                if !matches!(tree_kill.wait_timeout(budget), Ok(Some(_))) {
                    let _ = tree_kill.kill();
                    let _ = tree_kill
                        .wait_timeout(deadline.saturating_duration_since(Instant::now()) / 2);
                }
            }
        }
    }
    if child.try_wait().ok().flatten().is_none() {
        let _ = child.kill();
        let _ = child.wait_timeout(deadline.saturating_duration_since(Instant::now()));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture_process_running(node: &Path, pid: u32) -> bool {
        let mut command = Command::new(node);
        command.args(["-e", "const fs=require('fs');const p=Number(process.argv[1]);let alive=true;try{process.kill(p,0);if(process.platform==='linux'){const status=fs.readFileSync('/proc/'+p+'/stat','utf8');if(status.slice(status.lastIndexOf(')')+2).startsWith('Z'))alive=false}}catch{alive=false}process.exit(alive?1:0)", &pid.to_string()]).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
        hide_command(&mut command);
        command.status().is_ok_and(|status| !status.success())
    }

    #[test]
    fn version_timeout_stops_the_wrapper_and_its_stdout_holding_child() {
        let temp = tempfile::tempdir().unwrap();
        let child = temp.path().join("child.cjs");
        let wrapper = temp.path().join("wrapper.cjs");
        std::fs::write(&child, "const fs=require('fs'),path=require('path');fs.writeFileSync(path.join(__dirname,'child.pid'),String(process.pid));setInterval(()=>{},1000);").unwrap();
        std::fs::write(&wrapper, "const fs=require('fs'),path=require('path');fs.writeFileSync(path.join(__dirname,'wrapper.pid'),String(process.pid));require('child_process').spawn(process.execPath,[path.join(__dirname,'child.cjs')],{stdio:['ignore','inherit','ignore']});setInterval(()=>{},1000);").unwrap();
        let executable = resolve_executable(
            wrapper.to_str().unwrap(),
            &std::env::vars().collect(),
            temp.path(),
        )
        .unwrap();
        let started = Instant::now();
        let result = version_with_timeout(&executable, Duration::from_secs(3));
        assert!(started.elapsed() < Duration::from_secs(4));
        assert!(result.unwrap_err().contains("timed out"));
        for marker in ["wrapper.pid", "child.pid"] {
            let pid: u32 = std::fs::read_to_string(temp.path().join(marker))
                .expect("The fixture must reach its running state")
                .parse()
                .unwrap();
            let deadline = Instant::now() + Duration::from_secs(2);
            let mut running = fixture_process_running(&executable.file, pid);
            while running && Instant::now() < deadline {
                std::thread::sleep(Duration::from_millis(20));
                running = fixture_process_running(&executable.file, pid);
            }
            if running {
                let mut cleanup = Command::new(&executable.file);
                cleanup.args([
                    "-e",
                    "try{process.kill(Number(process.argv[1]),'SIGKILL')}catch{}",
                    &pid.to_string(),
                ]);
                hide_command(&mut cleanup);
                let _ = cleanup.status();
            }
            assert!(!running, "The version timeout left {marker} alive");
        }
    }

    #[test]
    fn version_keeps_the_first_line_and_drains_bounded_memory_output() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("version.cjs");
        std::fs::write(
            &script,
            "process.stdout.write('\\n\\u001b[32magent 1.2.3\\u001b[0m\\n'+'tail'.repeat(100000));",
        )
        .unwrap();
        let executable = resolve_executable(
            script.to_str().unwrap(),
            &std::env::vars().collect(),
            temp.path(),
        )
        .unwrap();
        assert_eq!(version(&executable).unwrap(), "agent 1.2.3");
        std::fs::write(
            &script,
            "process.stdout.write('failure\\n');process.exit(1);",
        )
        .unwrap();
        assert!(version(&executable).unwrap_err().contains("failed"));
    }

    #[test]
    fn shim_targets_are_arguments_and_cannot_escape_the_package() {
        let root = std::env::temp_dir().join("bin");
        let shim = root.join("codex.cmd");
        assert_eq!(
            npm_shim_target(
                r#""%_prog%" "%dp0%\node_modules\@openai\codex\bin\codex.js" %*"#,
                &shim
            ),
            Some(root.join("node_modules/@openai/codex/bin/codex.js"))
        );
        assert!(npm_shim_target(r#""%dp0%\..\outside.js" %*"#, &shim).is_none());
        assert!(npm_shim_target("powershell -Command anything", &shim).is_none());
    }

    #[test]
    fn a_javascript_entry_point_need_not_have_an_executable_bit() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("agent.cjs");
        std::fs::write(&path, "process.stdout.write('test');").unwrap();
        assert_eq!(
            find_executable(path.to_str().unwrap(), &HashMap::new(), temp.path()).unwrap(),
            native_path(path.canonicalize().unwrap())
        );
    }
}
