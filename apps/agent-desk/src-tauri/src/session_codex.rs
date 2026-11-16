use crate::executables::resolve_executable;
use crate::session_formats::{
    MAX_CONTENT, SessionFields, SessionInput, content_text, date, head, list, make_transcript,
    nonempty, now, string,
};
use crate::types::{DeskResult, SessionMessage, SessionRecord, Transcript};
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
use std::io::{BufRead, BufReader, Read, Write};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::{Duration, Instant};
use wait_timeout::ChildExt;

const MAX_RESPONSE: usize = 32 * 1024 * 1024;
const REQUEST_TIMEOUT: Duration = Duration::from_secs(10);

enum RpcError {
    Remote { code: i64, method: String },
    Failure(String),
}

impl RpcError {
    fn message(self) -> String {
        match self {
            Self::Remote { code, method } => format!("Codex {method} failed ({code})."),
            Self::Failure(message) => message,
        }
    }

    fn code(&self) -> Option<i64> {
        match self {
            Self::Remote { code, .. } => Some(*code),
            _ => None,
        }
    }
}

struct Connection {
    child: Child,
    responses: Receiver<Result<Value, String>>,
}

impl Drop for Connection {
    fn drop(&mut self) {
        if matches!(self.child.try_wait(), Ok(None)) {
            #[cfg(unix)]
            unsafe {
                libc::kill(-(self.child.id() as i32), libc::SIGTERM);
            }
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                let taskkill = std::env::var_os("SystemRoot")
                    .map(PathBuf::from)
                    .map(|root| root.join("System32/taskkill.exe"))
                    .unwrap_or_else(|| PathBuf::from("taskkill.exe"));
                if let Ok(mut killer) = Command::new(taskkill)
                    .args(["/PID", &self.child.id().to_string(), "/T", "/F"])
                    .creation_flags(0x08000000)
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
                    && !matches!(killer.wait_timeout(Duration::from_secs(2)), Ok(Some(_)))
                {
                    let _ = killer.kill();
                    let _ = killer.wait();
                }
            }
        }
        self.child.stdin.take();
        if !matches!(
            self.child.wait_timeout(Duration::from_millis(500)),
            Ok(Some(_))
        ) {
            #[cfg(unix)]
            unsafe {
                libc::kill(-(self.child.id() as i32), libc::SIGKILL);
            }
            let _ = self.child.kill();
        }
        let _ = self.child.wait();
    }
}

pub struct CodexHistory {
    command: String,
    home: PathBuf,
    user_home: PathBuf,
    environment: HashMap<String, String>,
    connection: Option<Connection>,
    sequence: u64,
    failure: Option<String>,
    initialized: bool,
}

impl CodexHistory {
    pub fn new(
        command: String,
        home: PathBuf,
        user_home: PathBuf,
        environment: HashMap<String, String>,
    ) -> Self {
        Self {
            command,
            home,
            user_home,
            environment,
            connection: None,
            sequence: 0,
            failure: None,
            initialized: false,
        }
    }

    fn start(&mut self) -> DeskResult<()> {
        if let Some(failure) = &self.failure {
            return Err(failure.clone());
        }
        if self.initialized {
            return Ok(());
        }
        let mut environment: HashMap<_, _> = self
            .environment
            .iter()
            .filter(|(key, _)| !key.starts_with("ELECTRON_") && key.as_str() != "NODE_OPTIONS")
            .map(|(key, value)| (key.clone(), value.clone()))
            .collect();
        environment.insert(
            "CODEX_HOME".into(),
            self.home.to_string_lossy().into_owned(),
        );
        let executable = resolve_executable(&self.command, &environment, &self.user_home)?;
        let mut command = Command::new(&executable.file);
        command
            .args(&executable.args)
            .args(["app-server", "--listen", "stdio://"])
            .env_clear()
            .envs(&environment)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        let mut child = command
            .spawn()
            .map_err(|error| format!("Codex app-server could not start ({:?}).", error.kind()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| "Codex app-server stdout is unavailable.".to_owned())?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| "Codex app-server stderr is unavailable.".to_owned())?;
        let (sender, responses) = mpsc::sync_channel(1);
        self.connection = Some(Connection { child, responses });
        thread::Builder::new()
            .name("codex-history-output".into())
            .spawn(move || {
                let mut reader = BufReader::new(stdout);
                loop {
                    let mut line = Vec::new();
                    let result = Read::take(&mut reader, (MAX_RESPONSE + 1) as u64)
                        .read_until(b'\n', &mut line);
                    match result {
                        Ok(0) => {
                            let _ = sender
                                .send(Err("Codex app-server closed its history output.".into()));
                            break;
                        }
                        Ok(_) if line.len() > MAX_RESPONSE => {
                            let _ = sender.send(Err(
                                "Codex history response exceeded the 32 MiB limit.".into(),
                            ));
                            break;
                        }
                        Ok(_) => {
                            if line.iter().all(u8::is_ascii_whitespace) {
                                continue;
                            }
                            let result = serde_json::from_slice::<Value>(&line)
                                .map_err(|_| "Codex app-server returned invalid JSON.".to_owned());
                            let failed = result.is_err();
                            if sender.send(result).is_err() || failed {
                                break;
                            }
                        }
                        Err(_) => {
                            let _ = sender.send(Err("The Codex history connection closed.".into()));
                            break;
                        }
                    }
                }
            })
            .map_err(|error| self.fail(format!("Codex history reader could not start: {error}")))?;
        thread::Builder::new()
            .name("codex-history-errors".into())
            .spawn(move || {
                let _ = std::io::copy(&mut BufReader::new(stderr), &mut std::io::sink());
            })
            .map_err(|error| {
                self.fail(format!(
                    "Codex history error reader could not start: {error}"
                ))
            })?;
        self.request("initialize", json!({ "clientInfo": { "name": "agent-desk", "title": "Agent Desk", "version": env!("CARGO_PKG_VERSION") }, "capabilities": { "experimentalApi": false } })).map_err(RpcError::message)?;
        let result = self
            .connection
            .as_mut()
            .and_then(|connection| connection.child.stdin.as_mut())
            .ok_or_else(|| "The Codex history connection closed.".to_owned())
            .and_then(|stdin| {
                writeln!(stdin, "{}", json!({ "method": "initialized" }))
                    .map_err(|_| "The Codex history connection closed.".to_owned())
            });
        if let Err(error) = result {
            return Err(self.fail(error));
        }
        self.initialized = true;
        Ok(())
    }

    fn fail(&mut self, message: String) -> String {
        self.failure.get_or_insert_with(|| message.clone());
        self.connection.take();
        self.initialized = false;
        message
    }

    fn request(&mut self, method: &str, params: Value) -> Result<Value, RpcError> {
        if let Some(failure) = &self.failure {
            return Err(RpcError::Failure(failure.clone()));
        }
        self.sequence += 1;
        let id = self.sequence;
        let Some(connection) = self.connection.as_mut() else {
            return Err(RpcError::Failure("Codex app-server is not running.".into()));
        };
        let Some(stdin) = connection.child.stdin.as_mut() else {
            return Err(RpcError::Failure(
                self.fail("The Codex history connection closed.".into()),
            ));
        };
        if writeln!(
            stdin,
            "{}",
            json!({ "id": id, "method": method, "params": params })
        )
        .is_err()
        {
            return Err(RpcError::Failure(
                self.fail("The Codex history connection closed.".into()),
            ));
        }
        let deadline = Instant::now() + REQUEST_TIMEOUT;
        loop {
            let remaining = deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() {
                return Err(RpcError::Failure(
                    self.fail(format!("Codex {method} timed out after 10 seconds.")),
                ));
            }
            let response = self
                .connection
                .as_ref()
                .unwrap()
                .responses
                .recv_timeout(remaining);
            let mut response = match response {
                Ok(Ok(response)) => response,
                Ok(Err(error)) => return Err(RpcError::Failure(self.fail(error))),
                Err(mpsc::RecvTimeoutError::Timeout) => {
                    return Err(RpcError::Failure(
                        self.fail(format!("Codex {method} timed out after 10 seconds.")),
                    ));
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    return Err(RpcError::Failure(
                        self.fail("Codex app-server closed its history output.".into()),
                    ));
                }
            };
            if response["id"].as_u64() != Some(id) {
                continue;
            }
            if !response["error"].is_null() {
                return Err(RpcError::Remote {
                    code: response["error"]["code"].as_i64().unwrap_or(-1),
                    method: method.into(),
                });
            }
            return Ok(response
                .as_object_mut()
                .and_then(|response| response.remove("result"))
                .unwrap_or(Value::Null));
        }
    }

    pub fn close(&mut self) {
        self.fail("Codex history connection closed.".into());
    }

    pub fn index(&mut self) -> DeskResult<(Vec<SessionRecord>, Vec<String>)> {
        self.start()?;
        let mut sessions = Vec::new();
        let mut warnings = Vec::new();
        for archived in [false, true] {
            let mut cursor: Option<String> = None;
            let mut cursors = HashSet::new();
            let mut compatibility = false;
            for page in 0..100 {
                let mut params =
                    json!({ "limit": 100, "archived": archived, "modelProviders": [] });
                if let Some(cursor) = &cursor {
                    params["cursor"] = cursor.clone().into();
                }
                if !compatibility {
                    params["sortKey"] = "updated_at".into();
                    params["sourceKinds"] =
                        json!(["cli", "vscode", "exec", "appServer", "unknown"]);
                }
                let result = match self.request("thread/list", params) {
                    Ok(result) => result,
                    Err(error) if error.code() == Some(-32602) && !compatibility => {
                        compatibility = true;
                        warnings.push("This Codex version accepts fewer thread filters. All providers are included, but its default source filter may omit non-interactive sessions.".into());
                        let mut params =
                            json!({ "limit": 100, "archived": archived, "modelProviders": [] });
                        if let Some(cursor) = &cursor {
                            params["cursor"] = cursor.clone().into();
                        }
                        self.request("thread/list", params)
                            .map_err(RpcError::message)?
                    }
                    Err(error) => return Err(error.message()),
                };
                let data = result["data"]
                    .as_array()
                    .ok_or_else(|| "Codex thread/list returned no session array.".to_owned())?;
                for thread in data {
                    if !string(&thread["id"]).is_empty() {
                        sessions.push(self.record(thread, archived));
                    }
                }
                let Some(next) = nonempty(&result["nextCursor"]) else {
                    break;
                };
                if !cursors.insert(next.clone()) {
                    warnings.push(
                        "Codex repeated a history cursor. Remaining pages were not loaded.".into(),
                    );
                    break;
                }
                cursor = Some(next);
                if page == 99 {
                    warnings.push(
                        "Codex history reached the 10,000-session limit for this section.".into(),
                    );
                }
            }
        }
        Ok((sessions, warnings))
    }

    fn record(&self, thread: &Value, archived: bool) -> SessionRecord {
        let source = nonempty(&thread["source"])
            .or_else(|| nonempty(&thread["sourceKind"]))
            .unwrap_or_default();
        let modified_at = now();
        let title = nonempty(&thread["name"]).unwrap_or_else(|| {
            let preview = head(
                &string(&thread["preview"])
                    .split_whitespace()
                    .collect::<Vec<_>>()
                    .join(" "),
                110,
            );
            if preview.is_empty() {
                "Untitled Codex session".into()
            } else {
                preview
            }
        });
        let mut record = make_transcript(
            &SessionInput {
                agent: "codex".into(),
                source_path: nonempty(&thread["path"])
                    .unwrap_or_else(|| format!("codex-app-server:{}", self.home.display())),
                modified_at: modified_at.clone(),
                archived,
                ..Default::default()
            },
            SessionFields {
                native_id: nonempty(&thread["id"]),
                title: Some(title),
                project_path: nonempty(&thread["cwd"]),
                created_at: Some(date(&thread["createdAt"], &modified_at)),
                updated_at: Some(date(&thread["updatedAt"], &modified_at)),
                model: nonempty(&thread["model"]),
                source_kind: Some(
                    match source.as_str() {
                        "vscode" => "ide",
                        "appServer" => "desktop",
                        _ => "cli",
                    }
                    .into(),
                ),
                ..Default::default()
            },
            Vec::new(),
        )
        .session;
        record.preview = head(string(&thread["preview"]), 2400);
        record.source_path = nonempty(&thread["path"]);
        record
    }

    fn read_turns(
        &mut self,
        native_id: &str,
        warnings: &mut Vec<String>,
    ) -> Result<(Vec<Value>, bool), RpcError> {
        let mut turns = Vec::new();
        let mut cursor: Option<String> = None;
        let mut cursors = HashSet::new();
        let mut history_bytes = 0;
        let mut truncated = false;
        for page in 0..100 {
            let mut params = json!({ "threadId": native_id, "limit": 50, "sortDirection": "desc", "itemsView": "full" });
            if let Some(cursor) = &cursor {
                params["cursor"] = cursor.clone().into();
            }
            let batch = self.request("thread/turns/list", params)?;
            let data = batch["data"].as_array().ok_or_else(|| {
                RpcError::Failure("Codex thread/turns/list returned no turns array.".into())
            })?;
            history_bytes += batch.to_string().len();
            if history_bytes > MAX_RESPONSE {
                warnings.push("The Codex transcript reached the 32 MiB history limit. Older turns were not loaded.".into());
                truncated = true;
                break;
            }
            turns.extend(data.iter().cloned());
            let Some(next) = nonempty(&batch["nextCursor"]) else {
                break;
            };
            if !cursors.insert(next.clone()) {
                warnings.push(
                    "Codex repeated a transcript cursor. Older turns were not loaded.".into(),
                );
                truncated = true;
                break;
            }
            cursor = Some(next);
            if page == 99 {
                truncated = true;
                warnings.push(
                    "Codex transcript reached the 5,000-turn limit. Older turns were not loaded."
                        .into(),
                );
            }
        }
        turns.reverse();
        Ok((turns, truncated))
    }

    pub fn transcript(&mut self, session: &SessionRecord) -> DeskResult<Transcript> {
        self.start()?;
        let result = self
            .request("thread/read", json!({ "threadId": session.native_id }))
            .map_err(RpcError::message)?;
        let mut thread = result["thread"].clone();
        if !thread.is_object() {
            return Err("Codex thread/read returned no thread object.".into());
        }
        let mut warnings = Vec::new();
        let (turns, truncated) = match self.read_turns(&session.native_id, &mut warnings) {
            Ok(result) => result,
            Err(error) if matches!(error.code(), Some(-32601 | -32602)) => {
                let legacy = self
                    .request(
                        "thread/read",
                        json!({ "threadId": session.native_id, "includeTurns": true }),
                    )
                    .map_err(RpcError::message)?;
                let turns = legacy["thread"]["turns"].as_array().ok_or_else(|| {
                    "This Codex version cannot provide a readable stored transcript.".to_owned()
                })?;
                warnings.push(
                    "This Codex version uses the older thread/read history interface.".into(),
                );
                (turns.clone(), false)
            }
            Err(error) => return Err(error.message()),
        };
        let mut messages = Vec::new();
        let mut seen = HashSet::new();
        for (turn_index, turn) in turns.iter().enumerate() {
            for (index, item) in list(&turn["items"]).iter().enumerate() {
                let id = nonempty(&item["id"])
                    .unwrap_or_else(|| format!("turn-{turn_index}-item-{index}"));
                if !seen.insert(id.clone()) {
                    continue;
                }
                let kind = string(&item["type"]);
                let mut tool_name = None;
                let (role, content) = match kind {
                    "userMessage" => ("user", content_text(&item["content"])),
                    "agentMessage" => (
                        "assistant",
                        content_text(item.get("text").unwrap_or(&item["content"])),
                    ),
                    "reasoning" => (
                        "system",
                        content_text(item.get("summary").unwrap_or(&item["content"])),
                    ),
                    "commandExecution" => {
                        tool_name = Some("Shell".into());
                        (
                            "tool",
                            format!(
                                "{}\n{}",
                                string(&item["command"]),
                                string(&item["aggregatedOutput"])
                            ),
                        )
                    }
                    "fileChange" => {
                        tool_name = Some("File changes".into());
                        (
                            "tool",
                            list(&item["changes"])
                                .iter()
                                .map(|change| {
                                    format!(
                                        "{}\n{}",
                                        string(&change["path"]),
                                        string(&change["diff"])
                                    )
                                })
                                .collect::<Vec<_>>()
                                .join("\n"),
                        )
                    }
                    _ if ["tool", "search", "image", "collab"]
                        .iter()
                        .any(|fragment| kind.to_ascii_lowercase().contains(fragment)) =>
                    {
                        let name = nonempty(&item["tool"]).unwrap_or_else(|| kind.into());
                        let output = item
                            .get("result")
                            .or_else(|| item.get("output"))
                            .unwrap_or(&item["content"]);
                        let content = content_text(output);
                        tool_name = Some(name.clone());
                        ("tool", if content.is_empty() { name } else { content })
                    }
                    _ => continue,
                };
                if !content.trim().is_empty() {
                    messages.push(SessionMessage {
                        id,
                        role: role.into(),
                        content: head(&content, MAX_CONTENT),
                        tool_name,
                        timestamp: Some(date(&turn["startedAt"], &session.updated_at)),
                        model: None,
                    });
                }
            }
        }
        thread["id"] = session.native_id.clone().into();
        let mut updated = self.record(&thread, session.archived.unwrap_or(false));
        updated.id = session.id.clone();
        updated.message_count = messages.len();
        if updated.project_path.is_empty() {
            updated.project_path = session.project_path.clone();
            updated.project_name = session.project_name.clone();
        }
        updated.resumable = session.resumable;
        updated.resume_note = session.resume_note.clone();
        updated.source_path = updated.source_path.or_else(|| session.source_path.clone());
        let mut transcript = make_transcript(
            &SessionInput {
                agent: "codex".into(),
                source_path: session.source_path.clone().unwrap_or_default(),
                modified_at: session.updated_at.clone(),
                truncated,
                warnings,
                ..Default::default()
            },
            SessionFields::default(),
            messages,
        );
        transcript.session = updated;
        if transcript.messages.is_empty() {
            transcript.warnings.push(
                "The Codex history API returned no displayable messages for this session.".into(),
            );
        }
        Ok(transcript)
    }
}
