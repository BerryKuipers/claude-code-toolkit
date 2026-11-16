use crate::executables::Executable;
use crate::launch_plan::LaunchPlan;
use crate::types::{DeskResult, TerminalEvent, TerminalInfo, TerminalSnapshot};
use portable_pty::{Child, CommandBuilder, MasterPty, PtySize, native_pty_system};
use std::collections::{HashMap, VecDeque};
use std::io::{Read, Write};
use std::sync::{Arc, Mutex, RwLock};
use std::time::{Duration, Instant};
#[cfg(windows)]
use wait_timeout::ChildExt;

const SNAPSHOT_BYTES: usize = 2_000_000;
type EventListener = Arc<dyn Fn(TerminalEvent) + Send + Sync>;

struct TerminalState {
    info: TerminalInfo,
    chunks: VecDeque<String>,
    bytes: usize,
    sequence: u64,
    output_closed: bool,
    process_exit: Option<u32>,
    exit_emitted: bool,
}

struct TerminalIo {
    master: Mutex<Option<Box<dyn MasterPty + Send>>>,
    writer: Mutex<Option<Box<dyn Write + Send>>>,
}

struct Terminal {
    state: Mutex<TerminalState>,
    io: TerminalIo,
    child: Mutex<TerminalChild>,
}

struct TerminalChild {
    process: Option<Box<dyn Child + Send + Sync>>,
    exit: Option<u32>,
}

#[derive(Default)]
pub struct TerminalService {
    terminals: Mutex<HashMap<String, Arc<Terminal>>>,
    listener: Arc<RwLock<Option<EventListener>>>,
}

impl TerminalService {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn subscribe(&self, listener: EventListener) {
        if let Ok(mut slot) = self.listener.write() {
            *slot = Some(listener);
        }
    }

    pub fn launch(
        &self,
        executable: &Executable,
        plan: &LaunchPlan,
        mut info: TerminalInfo,
    ) -> DeskResult<TerminalInfo> {
        let mut terminals = self.terminals.lock().map_err(|e| e.to_string())?;
        if terminals.len() >= 24 {
            return Err(
                "Close an existing terminal before opening another one (24 maximum).".into(),
            );
        }
        if !std::path::Path::new(&plan.cwd).is_dir() {
            return Err("The project folder no longer exists. Choose an existing folder.".into());
        }
        let pair = native_pty_system()
            .openpty(PtySize {
                rows: 32,
                cols: 110,
                pixel_width: 0,
                pixel_height: 0,
            })
            .map_err(|e| e.to_string())?;
        let mut command = CommandBuilder::new(&executable.file);
        command.args(&executable.args);
        command.args(&plan.args);
        command.cwd(&plan.cwd);
        command.env_clear();
        for (name, value) in &plan.env {
            command.env(name, value);
        }
        let mut reader = pair.master.try_clone_reader().map_err(|e| e.to_string())?;
        let writer = pair.master.take_writer().map_err(|e| e.to_string())?;
        let child = pair
            .slave
            .spawn_command(command)
            .map_err(|e| e.to_string())?;
        drop(pair.slave);
        info.id = uuid::Uuid::new_v4().to_string();
        info.project_path = plan.cwd.clone();
        info.started_at = chrono::Utc::now().to_rfc3339();
        info.status = "running".into();
        let terminal = Arc::new(Terminal {
            state: Mutex::new(TerminalState {
                info: info.clone(),
                chunks: VecDeque::new(),
                bytes: 0,
                sequence: 0,
                output_closed: false,
                process_exit: None,
                exit_emitted: false,
            }),
            io: TerminalIo {
                master: Mutex::new(Some(pair.master)),
                writer: Mutex::new(Some(writer)),
            },
            child: Mutex::new(TerminalChild {
                process: Some(child),
                exit: None,
            }),
        });
        terminals.insert(info.id.clone(), terminal.clone());
        drop(terminals);
        let listener = self.listener.clone();
        let output_terminal = terminal.clone();
        std::thread::spawn(move || {
            let mut buffer = [0_u8; 16_384];
            let mut decoder = Utf8Decoder::default();
            loop {
                match reader.read(&mut buffer) {
                    Ok(0) => break,
                    Ok(count) => {
                        let text = decoder.push(&buffer[..count], false);
                        if !text.is_empty() {
                            output_terminal.data(text, &listener);
                        }
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                    Err(_) => break,
                }
            }
            let tail = decoder.push(&[], true);
            if !tail.is_empty() {
                output_terminal.data(tail, &listener);
            }
            if let Ok(mut state) = output_terminal.state.lock() {
                state.output_closed = true;
                output_terminal.finish(&mut state, &listener);
            }
        });
        let listener = self.listener.clone();
        std::thread::spawn(move || {
            let exit = loop {
                let result = terminal
                    .child
                    .lock()
                    .map_err(|error| error.to_string())
                    .and_then(|mut child| child.poll());
                match result {
                    Ok(Some(exit)) => break exit,
                    Ok(None) => std::thread::sleep(Duration::from_millis(50)),
                    Err(error) => {
                        terminal.data(
                            format!("\r\n[Could not read terminal process status: {error}]\r\n"),
                            &listener,
                        );
                        let _ = terminal.stop();
                        break 1;
                    }
                }
            };
            if let Err(error) = terminal.close_io() {
                terminal.data(
                    format!("\r\n[Could not release terminal handles: {error}]\r\n"),
                    &listener,
                );
            }
            if let Ok(mut state) = terminal.state.lock() {
                state.process_exit = Some(exit);
                terminal.finish(&mut state, &listener);
            }
        });
        Ok(info)
    }

    pub fn list(&self) -> Vec<TerminalInfo> {
        self.terminals
            .lock()
            .map(|items| {
                items
                    .values()
                    .filter_map(|item| item.state.lock().ok().map(|s| s.info.clone()))
                    .collect()
            })
            .unwrap_or_default()
    }

    pub fn snapshot(&self, id: &str) -> DeskResult<TerminalSnapshot> {
        let terminal = self.require(id)?;
        let state = terminal.state.lock().map_err(|e| e.to_string())?;
        Ok(TerminalSnapshot {
            data: state.chunks.iter().map(String::as_str).collect(),
            sequence: state.sequence,
            status: state.info.status.clone(),
            exit_code: state.info.exit_code,
        })
    }

    pub fn write(&self, id: &str, data: &str) -> DeskResult<()> {
        if data.len() > 1_000_000 {
            return Err("Terminal input is too large.".into());
        }
        let terminal = self.require(id)?;
        if terminal
            .state
            .lock()
            .map_err(|e| e.to_string())?
            .info
            .status
            != "running"
        {
            return Err("This terminal has exited. Resume the saved session to continue.".into());
        }
        let mut writer = terminal.io.writer.lock().map_err(|e| e.to_string())?;
        let writer = writer.as_mut().ok_or("This terminal has exited.")?;
        writer
            .write_all(data.as_bytes())
            .and_then(|_| writer.flush())
            .map_err(|e| e.to_string())
    }

    pub fn resize(&self, id: &str, cols: u16, rows: u16) -> DeskResult<()> {
        if !(2..=600).contains(&cols) || !(1..=300).contains(&rows) {
            return Err("Invalid terminal dimensions.".into());
        }
        let terminal = self.require(id)?;
        let master = terminal.io.master.lock().map_err(|e| e.to_string())?;
        if let Some(master) = &*master {
            master
                .resize(PtySize {
                    rows,
                    cols,
                    pixel_width: 0,
                    pixel_height: 0,
                })
                .map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    pub fn close(&self, id: &str) -> DeskResult<()> {
        let terminal = self.require(id)?;
        terminal.stop()?;
        self.terminals
            .lock()
            .map_err(|error| error.to_string())?
            .remove(id);
        Ok(())
    }

    pub fn dispose(&self) {
        let terminals = self
            .terminals
            .lock()
            .map(|mut items| {
                items
                    .drain()
                    .map(|(_, terminal)| terminal)
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        for terminal in terminals {
            if let Err(error) = terminal.stop() {
                eprintln!("Could not close terminal: {error}");
            }
        }
        if let Ok(mut listener) = self.listener.write() {
            listener.take();
        }
    }

    fn require(&self, id: &str) -> DeskResult<Arc<Terminal>> {
        self.terminals
            .lock()
            .map_err(|e| e.to_string())?
            .get(id)
            .cloned()
            .ok_or_else(|| "This terminal is no longer available.".into())
    }
}

impl Drop for TerminalService {
    fn drop(&mut self) {
        self.dispose();
    }
}

impl Terminal {
    fn data(&self, data: String, listener: &RwLock<Option<EventListener>>) {
        if let Ok(mut state) = self.state.lock() {
            state.bytes += data.len();
            state.chunks.push_back(data.clone());
            while state.bytes > SNAPSHOT_BYTES {
                let Some(front) = state.chunks.pop_front() else {
                    break;
                };
                state.bytes -= front.len();
            }
            state.sequence += 1;
            send(
                listener,
                TerminalEvent {
                    id: state.info.id.clone(),
                    sequence: state.sequence,
                    kind: "data".into(),
                    data: Some(data),
                    exit_code: None,
                },
            );
        }
    }

    fn finish(&self, state: &mut TerminalState, listener: &RwLock<Option<EventListener>>) {
        if !state.output_closed || state.process_exit.is_none() || state.exit_emitted {
            return;
        }
        state.exit_emitted = true;
        state.info.status = "exited".into();
        state.info.exit_code = state.process_exit;
        state.sequence += 1;
        send(
            listener,
            TerminalEvent {
                id: state.info.id.clone(),
                sequence: state.sequence,
                kind: "exit".into(),
                data: None,
                exit_code: state.process_exit,
            },
        );
    }

    fn stop(&self) -> DeskResult<()> {
        self.child
            .lock()
            .map_err(|error| error.to_string())?
            .stop()?;
        self.close_io()
    }

    fn close_io(&self) -> DeskResult<()> {
        let writer = self
            .io
            .writer
            .lock()
            .map_err(|error| error.to_string())?
            .take();
        drop(writer);
        let master = self
            .io
            .master
            .lock()
            .map_err(|error| error.to_string())?
            .take();
        drop(master);
        Ok(())
    }
}

impl TerminalChild {
    fn poll(&mut self) -> DeskResult<Option<u32>> {
        if self.exit.is_some() {
            return Ok(self.exit);
        }
        let process = self
            .process
            .as_mut()
            .ok_or("Terminal process ownership is unavailable.")?;
        if let Some(status) = process.try_wait().map_err(|error| error.to_string())? {
            self.exit = Some(status.exit_code());
            self.process.take();
        }
        Ok(self.exit)
    }

    fn wait_until(&mut self, deadline: Instant) -> DeskResult<bool> {
        loop {
            if self.poll()?.is_some() {
                return Ok(true);
            }
            if Instant::now() >= deadline {
                return Ok(false);
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }

    fn stop(&mut self) -> DeskResult<()> {
        if self.poll()?.is_some() {
            return Ok(());
        }
        #[cfg(unix)]
        {
            if let Some(pid) = self
                .process
                .as_ref()
                .and_then(|process| process.process_id())
            {
                unsafe {
                    libc::kill(-(pid as i32), libc::SIGTERM);
                }
                std::thread::sleep(Duration::from_millis(200));
                unsafe {
                    libc::kill(-(pid as i32), libc::SIGKILL);
                }
            }
        }
        #[cfg(windows)]
        {
            if let Some(pid) = self
                .process
                .as_ref()
                .and_then(|process| process.process_id())
            {
                let path = std::env::var_os("SystemRoot")
                    .map(std::path::PathBuf::from)
                    .map(|root| root.join("System32/taskkill.exe"))
                    .unwrap_or_else(|| "taskkill.exe".into());
                let mut command = std::process::Command::new(path);
                command
                    .args(["/PID", &pid.to_string(), "/T", "/F"])
                    .stdin(std::process::Stdio::null())
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null());
                crate::executables::hide_command(&mut command);
                if let Ok(mut taskkill) = command.spawn()
                    && !matches!(taskkill.wait_timeout(Duration::from_secs(2)), Ok(Some(_)))
                {
                    let _ = taskkill.kill();
                    let _ = taskkill.wait();
                }
            }
            if self.poll()?.is_some() {
                return Ok(());
            }
        }
        if let Some(process) = &mut self.process {
            let _ = process.kill();
        }
        if self.wait_until(Instant::now() + Duration::from_secs(2))? {
            Ok(())
        } else {
            Err("The terminal process did not stop within its shutdown deadline.".into())
        }
    }
}

fn send(listener: &RwLock<Option<EventListener>>, event: TerminalEvent) {
    let callback = listener.read().ok().and_then(|slot| slot.clone());
    if let Some(callback) = callback {
        callback(event);
    }
}

#[derive(Default)]
struct Utf8Decoder {
    pending: Vec<u8>,
}

impl Utf8Decoder {
    fn push(&mut self, bytes: &[u8], eof: bool) -> String {
        self.pending.extend_from_slice(bytes);
        let mut result = String::new();
        loop {
            match std::str::from_utf8(&self.pending) {
                Ok(text) => {
                    result.push_str(text);
                    self.pending.clear();
                    break;
                }
                Err(error) => {
                    let valid = error.valid_up_to();
                    if valid > 0 {
                        result.push_str(std::str::from_utf8(&self.pending[..valid]).unwrap());
                        self.pending.drain(..valid);
                    }
                    match error.error_len() {
                        Some(count) => {
                            result.push('\u{fffd}');
                            self.pending.drain(..count);
                        }
                        None if eof => {
                            result.push_str(&String::from_utf8_lossy(&self.pending));
                            self.pending.clear();
                            break;
                        }
                        None => break,
                    }
                }
            }
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::executables::resolve_executable;
    use std::time::{Duration, Instant};

    #[test]
    fn decoding_retains_utf8_across_reads_and_replaces_invalid_bytes() {
        let mut decoder = Utf8Decoder::default();
        assert_eq!(decoder.push(&[0xf0, 0x9f], false), "");
        assert_eq!(decoder.push(&[0x8c, 0xb1], false), "🌱");
        assert_eq!(decoder.push(&[0xff, b'a'], false), "�a");
        assert_eq!(decoder.push(&[0xe2], true), "�");
    }

    #[test]
    fn native_pty_input_resize_tail_output_exit_and_cleanup() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("agent.cjs");
        std::fs::write(&script, "const r=require('node:readline').createInterface({input:process.stdin}); process.stdout.write('READY\\n'); r.on('line',line=>{if(line.startsWith('ping')) process.stdout.write('ECHO:'+line+'\\nTAIL-🌱\\n',()=>process.exit(7));});").unwrap();
        let env: HashMap<_, _> = std::env::vars().collect();
        let executable = resolve_executable(script.to_str().unwrap(), &env, temp.path()).unwrap();
        let service = Arc::new(TerminalService::new());
        let events = Arc::new(Mutex::new(Vec::new()));
        let collected = events.clone();
        let weak = Arc::downgrade(&service);
        service.subscribe(Arc::new(move |event| {
            if event.data.as_ref().is_some_and(|s| s.contains("\u{1b}[6n"))
                && let Some(service) = weak.upgrade()
            {
                let id = event.id.clone();
                std::thread::spawn(move || {
                    let _ = service.write(&id, "\u{1b}[1;1R");
                });
            }
            collected.lock().unwrap().push(event);
        }));
        let info = service
            .launch(
                &executable,
                &LaunchPlan {
                    args: vec![],
                    env,
                    cwd: temp.path().to_string_lossy().into_owned(),
                },
                TerminalInfo {
                    agent: "claude".into(),
                    title: "PTY test".into(),
                    ..Default::default()
                },
            )
            .unwrap();
        let deadline = Instant::now() + Duration::from_secs(20);
        while !service.snapshot(&info.id).unwrap().data.contains("READY") {
            assert!(
                Instant::now() < deadline,
                "No ready output: {:?}",
                service.snapshot(&info.id)
            );
            std::thread::sleep(Duration::from_millis(20));
        }
        service.resize(&info.id, 90, 28).unwrap();
        service.write(&info.id, "ping-123\r").unwrap();
        while service.snapshot(&info.id).unwrap().status != "exited" {
            assert!(
                Instant::now() < deadline,
                "PTY failed to exit: {:?}",
                service.snapshot(&info.id)
            );
            std::thread::sleep(Duration::from_millis(20));
        }
        let snapshot = service.snapshot(&info.id).unwrap();
        assert!(snapshot.data.contains("ECHO:ping-123"));
        assert!(snapshot.data.contains("TAIL-🌱"));
        assert_eq!(snapshot.exit_code, Some(7));
        let records = events.lock().unwrap();
        assert_eq!(
            records.iter().filter(|event| event.kind == "exit").count(),
            1
        );
        assert_eq!(records.last().unwrap().kind, "exit");
        assert!(
            records
                .windows(2)
                .all(|pair| pair[0].sequence < pair[1].sequence)
        );
        drop(records);
        service.close(&info.id).unwrap();
        assert!(service.list().is_empty());
        assert!(service.snapshot(&info.id).is_err());
    }

    #[test]
    fn immediate_resize_and_early_close_release_silent_terminal_without_renderer() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("silent.cjs");
        std::fs::write(&script, "setInterval(()=>{},1000);").unwrap();
        let env = std::env::vars().collect();
        let executable = resolve_executable(script.to_str().unwrap(), &env, temp.path()).unwrap();
        let service = TerminalService::new();
        let info = service
            .launch(
                &executable,
                &LaunchPlan {
                    args: vec![],
                    env,
                    cwd: temp.path().to_string_lossy().into_owned(),
                },
                TerminalInfo::default(),
            )
            .unwrap();
        let owned = service.require(&info.id).unwrap();
        service.resize(&info.id, 82, 27).unwrap();
        service.close(&info.id).unwrap();
        assert!(service.list().is_empty());
        assert!(owned.child.lock().unwrap().exit.is_some());
        assert!(owned.child.lock().unwrap().process.is_none());
        let deadline = Instant::now() + Duration::from_secs(3);
        while Arc::strong_count(&owned) > 1 {
            assert!(
                Instant::now() < deadline,
                "Terminal worker threads survived close"
            );
            std::thread::sleep(Duration::from_millis(20));
        }
    }

    #[test]
    fn natural_exit_without_renderer_drains_final_unicode_output() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("fast-exit.cjs");
        std::fs::write(
            &script,
            "process.stdout.write('FINAL-🌱\\n',()=>process.exit(9));",
        )
        .unwrap();
        let env = std::env::vars().collect();
        let executable = resolve_executable(script.to_str().unwrap(), &env, temp.path()).unwrap();
        let service = TerminalService::new();
        let info = service
            .launch(
                &executable,
                &LaunchPlan {
                    args: vec![],
                    env,
                    cwd: temp.path().to_string_lossy().into_owned(),
                },
                TerminalInfo::default(),
            )
            .unwrap();
        let deadline = Instant::now() + Duration::from_secs(10);
        loop {
            let snapshot = service.snapshot(&info.id).unwrap();
            if snapshot.status == "exited" {
                assert_eq!(snapshot.exit_code, Some(9));
                assert!(snapshot.data.contains("FINAL-🌱"), "{snapshot:?}");
                break;
            }
            assert!(
                Instant::now() < deadline,
                "Natural exit required a renderer: {snapshot:?}"
            );
            std::thread::sleep(Duration::from_millis(20));
        }
        service.close(&info.id).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn close_reaps_signal_ignoring_child_and_releases_output_worker() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("stubborn.cjs");
        std::fs::write(&script, "process.on('SIGTERM',()=>{});process.on('SIGHUP',()=>{});process.stdout.write('READY\\n');setInterval(()=>{},1000);").unwrap();
        let env = std::env::vars().collect();
        let executable = resolve_executable(script.to_str().unwrap(), &env, temp.path()).unwrap();
        let service = TerminalService::new();
        let info = service
            .launch(
                &executable,
                &LaunchPlan {
                    args: vec![],
                    env,
                    cwd: temp.path().to_string_lossy().into_owned(),
                },
                TerminalInfo::default(),
            )
            .unwrap();
        let owned = service.require(&info.id).unwrap();
        let pid = owned
            .child
            .lock()
            .unwrap()
            .process
            .as_ref()
            .unwrap()
            .process_id()
            .unwrap();
        let deadline = Instant::now() + Duration::from_secs(5);
        while !service.snapshot(&info.id).unwrap().data.contains("READY") {
            assert!(Instant::now() < deadline, "Signal handlers were not ready");
            std::thread::sleep(Duration::from_millis(10));
        }
        let before = Instant::now();
        service.close(&info.id).unwrap();
        assert!(before.elapsed() < Duration::from_secs(3));
        assert!(owned.child.lock().unwrap().exit.is_some());
        assert!(owned.child.lock().unwrap().process.is_none());
        assert_eq!(unsafe { libc::kill(pid as i32, 0) }, -1);
        assert_eq!(
            std::io::Error::last_os_error().raw_os_error(),
            Some(libc::ESRCH)
        );
        while Arc::strong_count(&owned) > 1 {
            assert!(
                Instant::now() < deadline,
                "Terminal workers survived the child's exit"
            );
            std::thread::sleep(Duration::from_millis(10));
        }
    }

    #[cfg(unix)]
    #[test]
    fn close_kills_ignoring_descendant_after_wrapper_exits_during_grace() {
        let temp = tempfile::tempdir().unwrap();
        let script = temp.path().join("wrapper.cjs");
        let heartbeat = temp.path().join("heartbeat");
        let descendant = format!(
            "const fs=require('node:fs');process.on('SIGTERM',()=>{{}});process.on('SIGHUP',()=>{{}});fs.writeFileSync({path},'ready');process.stdout.write('DESCENDANT_READY\\n');setInterval(()=>fs.appendFileSync({path},'x'),20);",
            path = serde_json::to_string(&heartbeat.to_string_lossy()).unwrap()
        );
        std::fs::write(&script, format!("require('node:child_process').spawn(process.execPath,['-e',{}],{{stdio:'inherit'}});setInterval(()=>{{}},1000);", serde_json::to_string(&descendant).unwrap())).unwrap();
        let env = std::env::vars().collect();
        let executable = resolve_executable(script.to_str().unwrap(), &env, temp.path()).unwrap();
        let service = TerminalService::new();
        let info = service
            .launch(
                &executable,
                &LaunchPlan {
                    args: vec![],
                    env,
                    cwd: temp.path().to_string_lossy().into_owned(),
                },
                TerminalInfo::default(),
            )
            .unwrap();
        let owned = service.require(&info.id).unwrap();
        let deadline = Instant::now() + Duration::from_secs(5);
        while !service
            .snapshot(&info.id)
            .unwrap()
            .data
            .contains("DESCENDANT_READY")
        {
            assert!(
                Instant::now() < deadline,
                "Descendant signal handlers were not ready"
            );
            std::thread::sleep(Duration::from_millis(10));
        }
        service.close(&info.id).unwrap();
        assert!(owned.child.lock().unwrap().exit.is_some());
        while Arc::strong_count(&owned) > 1 {
            assert!(
                Instant::now() < deadline,
                "A descendant retained the output pipe after close"
            );
            std::thread::sleep(Duration::from_millis(10));
        }
        let after = std::fs::read(&heartbeat).unwrap();
        std::thread::sleep(Duration::from_millis(100));
        assert_eq!(
            std::fs::read(heartbeat).unwrap(),
            after,
            "Descendant remained active after wrapper teardown"
        );
    }
}
