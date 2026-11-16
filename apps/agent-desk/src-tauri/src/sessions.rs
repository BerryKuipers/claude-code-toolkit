use crate::session_codex::CodexHistory;
use crate::session_formats::{
    SessionInput, now, parse_antigravity, parse_claude, parse_codex, parse_gemini,
};
use crate::types::{AppSettings, DeskResult, SessionIndex, SessionRecord, Transcript};
use chrono::{DateTime, SecondsFormat, Utc};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet, VecDeque};
use std::fs::{self, File};
use std::io::{Read, Seek, SeekFrom};
use std::path::{Component, Path, PathBuf};
use std::time::{Duration, Instant, UNIX_EPOCH};

const MAX_FILE_BYTES: usize = 32 * 1024 * 1024;
const MAX_RECORD_BYTES: usize = 2 * 1024 * 1024;
const MAX_FILES: usize = 10000;
const MAX_DIRECTORIES: usize = 20000;
const MAX_DEPTH: usize = 10;

#[derive(Clone)]
struct ScanRoot {
    agent: String,
    path: PathBuf,
    source_kind: String,
    archived: bool,
    custom: bool,
}

#[derive(Clone)]
struct Source {
    session: SessionRecord,
    root: Option<ScanRoot>,
    app_server: bool,
    native_store: bool,
}

struct CachedFile {
    signature: String,
    transcript: Option<Transcript>,
}

#[derive(Debug)]
struct ReadResult {
    records: Vec<Value>,
    warnings: Vec<String>,
    truncated: bool,
    modified_at: String,
}

fn normalize(path: &Path) -> PathBuf {
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir
                if normalized.file_name().is_some()
                    && normalized.file_name() != Some(std::ffi::OsStr::new("..")) =>
            {
                normalized.pop();
            }
            Component::ParentDir if normalized.has_root() => {}
            _ => normalized.push(component.as_os_str()),
        }
    }
    normalized
}

fn absolute_metadata_path(value: &str) -> bool {
    Path::new(value).is_absolute()
        || (value
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphabetic)
            && value.as_bytes().get(1) == Some(&b':')
            && matches!(value.as_bytes().get(2), Some(b'/' | b'\\')))
}

fn candidate(agent: &str, name: &str) -> bool {
    match agent {
        "claude" => {
            name.ends_with(".jsonl")
                && name != "history.jsonl"
                && !name.starts_with("agent-")
                && !name.contains(".orphaned-")
                && !name.contains(".superseded-")
        }
        "codex" => name.starts_with("rollout-") && name.ends_with(".jsonl"),
        "gemini" => {
            name.starts_with("session-") && (name.ends_with(".json") || name.ends_with(".jsonl"))
        }
        "antigravity" => name == "transcript.jsonl",
        _ => false,
    }
}

fn read_records(file: &Path) -> DeskResult<ReadResult> {
    let info = fs::symlink_metadata(file)
        .map_err(|error| format!("Could not inspect session source ({:?}).", error.kind()))?;
    if !info.is_file() || info.file_type().is_symlink() {
        return Err("Session source is not a regular file.".into());
    }
    let modified_at = info
        .modified()
        .map(DateTime::<Utc>::from)
        .map(|time| time.to_rfc3339_opts(SecondsFormat::Millis, true))
        .map_err(|error| format!("Could not read session modification time: {error}"))?;
    let truncated = info.len() > MAX_FILE_BYTES as u64;
    let legacy = file
        .extension()
        .is_some_and(|extension| extension == "json");
    if truncated && legacy {
        return Err("This legacy JSON session exceeds the 32 MiB read limit.".into());
    }
    let mut handle = File::open(file)
        .map_err(|error| format!("Could not open transcript ({:?}).", error.kind()))?;
    let mut chunks = Vec::new();
    let mut warnings = Vec::new();
    if truncated {
        let head_size = 8 * 1024 * 1024;
        let tail_size = MAX_FILE_BYTES - head_size;
        let mut first = Vec::with_capacity(head_size);
        Read::by_ref(&mut handle)
            .take(head_size as u64)
            .read_to_end(&mut first)
            .map_err(|error| format!("Could not read transcript: {error}"))?;
        let end = first
            .iter()
            .rposition(|byte| *byte == b'\n')
            .map(|position| position + 1)
            .unwrap_or(0);
        first.truncate(end);
        chunks.push(first);
        handle
            .seek(SeekFrom::Start(info.len() - tail_size as u64))
            .map_err(|error| format!("Could not seek transcript: {error}"))?;
        let mut last = Vec::with_capacity(tail_size);
        Read::by_ref(&mut handle)
            .take(tail_size as u64)
            .read_to_end(&mut last)
            .map_err(|error| format!("Could not read transcript: {error}"))?;
        let start = last
            .iter()
            .position(|byte| *byte == b'\n')
            .map(|position| position + 1)
            .unwrap_or(last.len());
        last.drain(..start);
        chunks.push(last);
        warnings.push(
            "This large session is a partial view: the first 8 MiB and last 24 MiB were read."
                .into(),
        );
    } else {
        let mut buffer = Vec::with_capacity(info.len() as usize);
        Read::by_ref(&mut handle)
            .take(info.len())
            .read_to_end(&mut buffer)
            .map_err(|error| format!("Could not read transcript: {error}"))?;
        chunks.push(buffer);
    }
    let mut records = Vec::new();
    if legacy {
        let parsed = serde_json::from_slice::<Value>(&chunks[0]).map_err(|_| {
            "Session JSON is malformed or is being written. Refresh to try again.".to_owned()
        })?;
        if !parsed.is_object() {
            return Err(
                "Session JSON is malformed or is being written. Refresh to try again.".into(),
            );
        }
        records.push(parsed);
    } else {
        let mut malformed = 0;
        for chunk in chunks {
            for line in chunk.split(|byte| *byte == b'\n') {
                if line.iter().all(u8::is_ascii_whitespace) {
                    continue;
                }
                if line.len() > MAX_RECORD_BYTES {
                    malformed += 1;
                    continue;
                }
                match serde_json::from_slice::<Value>(line) {
                    Ok(record) if record.is_object() => records.push(record),
                    _ => malformed += 1,
                }
            }
        }
        if malformed > 0 {
            warnings.push(format!(
                "{malformed} malformed, incomplete, or oversized transcript record{} skipped.",
                if malformed == 1 { " was" } else { "s were" }
            ));
        }
    }
    Ok(ReadResult {
        records,
        warnings,
        truncated,
        modified_at,
    })
}

pub struct SessionService {
    home: PathBuf,
    environment: HashMap<String, String>,
    cached: Option<SessionIndex>,
    cache_key: String,
    sources: HashMap<String, Source>,
    file_cache: HashMap<PathBuf, CachedFile>,
    codex: Option<CodexHistory>,
    codex_key: String,
    codex_retry_at: Option<Instant>,
    codex_warning: String,
}

impl SessionService {
    pub fn new(home: PathBuf) -> Self {
        Self {
            home,
            environment: std::env::vars().collect(),
            cached: None,
            cache_key: String::new(),
            sources: HashMap::new(),
            file_cache: HashMap::new(),
            codex: None,
            codex_key: String::new(),
            codex_retry_at: None,
            codex_warning: String::new(),
        }
    }

    fn expand(&self, value: &str) -> PathBuf {
        if value == "~" {
            self.home.clone()
        } else if value.starts_with("~/") || value.starts_with("~\\") {
            normalize(&self.home.join(&value[2..]))
        } else {
            normalize(Path::new(value))
        }
    }

    fn homes(&self) -> [PathBuf; 3] {
        [
            self.environment
                .get("CLAUDE_CONFIG_DIR")
                .filter(|value| !value.is_empty())
                .map(|value| self.expand(value))
                .unwrap_or_else(|| self.home.join(".claude")),
            self.environment
                .get("CODEX_HOME")
                .filter(|value| !value.is_empty())
                .map(|value| self.expand(value))
                .unwrap_or_else(|| self.home.join(".codex")),
            self.environment
                .get("GEMINI_CLI_HOME")
                .filter(|value| !value.is_empty())
                .map(|value| self.expand(value))
                .unwrap_or_else(|| self.home.clone())
                .join(".gemini"),
        ]
    }

    fn native_roots(&self) -> Vec<ScanRoot> {
        let [claude, codex, gemini] = self.homes();
        [
            ("claude", claude.join("projects"), "cli", false),
            ("codex", codex.join("sessions"), "cli", false),
            ("codex", codex.join("archived_sessions"), "cli", true),
            ("gemini", gemini.join("tmp"), "cli", false),
            (
                "antigravity",
                self.home.join(".gemini/antigravity-cli/brain"),
                "cli",
                false,
            ),
            (
                "antigravity",
                self.home.join(".gemini/antigravity/brain"),
                "desktop",
                false,
            ),
            (
                "antigravity",
                self.home.join(".gemini/antigravity-ide/brain"),
                "ide",
                false,
            ),
        ]
        .into_iter()
        .map(|(agent, path, source_kind, archived)| ScanRoot {
            agent: agent.into(),
            path,
            source_kind: source_kind.into(),
            archived,
            custom: false,
        })
        .collect()
    }

    fn roots(&self, settings: &AppSettings) -> Vec<ScanRoot> {
        let mut roots = self.native_roots();
        for root in &settings.history_roots {
            let expanded = self.expand(&root.path);
            let components: Vec<_> = root.path.split(['/', '\\']).collect();
            let source_kind =
                if root.agent != "antigravity" || components.contains(&"antigravity-cli") {
                    "cli"
                } else if components.contains(&"antigravity-ide") {
                    "ide"
                } else {
                    "desktop"
                };
            roots.push(ScanRoot {
                agent: root.agent.clone(),
                path: expanded,
                source_kind: source_kind.into(),
                custom: true,
                archived: components.contains(&"archived_sessions"),
            });
        }
        let mut unique = HashSet::new();
        roots.retain(|root| unique.insert((root.agent.clone(), root.path.clone())));
        roots
    }

    pub fn index(&mut self, settings: &AppSettings, refresh: bool) -> DeskResult<SessionIndex> {
        let key = json!([
            settings.history_roots,
            settings.projects,
            settings.agent_commands.get("codex"),
            self.homes()
        ])
        .to_string();
        if !refresh
            && key == self.cache_key
            && let Some(cached) = &self.cached
        {
            return Ok(cached.clone());
        }
        self.scan(settings, key)
    }

    fn walk(root: &ScanRoot, warnings: &mut Vec<String>) -> Vec<PathBuf> {
        let mut files = Vec::new();
        let mut queue = VecDeque::from([(root.path.clone(), 0)]);
        let mut visited = 0;
        let mut depth_limited = false;
        while !queue.is_empty() && files.len() < MAX_FILES && visited < MAX_DIRECTORIES {
            let (directory, depth) = queue.pop_front().unwrap();
            visited += 1;
            let info = match fs::symlink_metadata(&directory) {
                Ok(info) => info,
                Err(error) => {
                    if error.kind() != std::io::ErrorKind::NotFound || root.custom {
                        warnings.push(format!(
                            "Could not scan {} ({:?}).",
                            directory.display(),
                            error.kind()
                        ));
                    }
                    continue;
                }
            };
            if info.file_type().is_symlink() {
                continue;
            }
            if info.is_file() {
                if candidate(
                    &root.agent,
                    directory
                        .file_name()
                        .and_then(|name| name.to_str())
                        .unwrap_or(""),
                ) {
                    files.push(directory);
                }
                continue;
            }
            if !info.is_dir() {
                continue;
            }
            let entries = match fs::read_dir(&directory) {
                Ok(entries) => entries,
                Err(error) => {
                    warnings.push(format!(
                        "Could not scan {} ({:?}).",
                        directory.display(),
                        error.kind()
                    ));
                    continue;
                }
            };
            let mut entries: Vec<_> = entries
                .filter_map(|entry| match entry {
                    Ok(entry) => Some(entry),
                    Err(error) => {
                        warnings.push(format!(
                            "Could not scan an entry under {} ({:?}).",
                            directory.display(),
                            error.kind()
                        ));
                        None
                    }
                })
                .collect();
            entries.sort_by_key(|entry| std::cmp::Reverse(entry.file_name()));
            for entry in entries {
                let kind = match entry.file_type() {
                    Ok(kind) => kind,
                    Err(error) => {
                        warnings.push(format!(
                            "Could not inspect {} ({:?}).",
                            entry.path().display(),
                            error.kind()
                        ));
                        continue;
                    }
                };
                if kind.is_symlink() {
                    continue;
                }
                let name = entry.file_name().to_string_lossy().into_owned();
                if kind.is_file() && candidate(&root.agent, &name) {
                    files.push(entry.path());
                }
                if kind.is_dir()
                    && ![
                        "subagents",
                        "node_modules",
                        ".git",
                        "memory",
                        "tool-results",
                        "plugins",
                    ]
                    .contains(&name.as_str())
                {
                    if depth < MAX_DEPTH {
                        queue.push_back((entry.path(), depth + 1));
                    } else {
                        depth_limited = true;
                    }
                }
                if files.len() >= MAX_FILES {
                    break;
                }
            }
        }
        if !queue.is_empty() || files.len() >= MAX_FILES || depth_limited {
            warnings.push(format!("History scan limit reached under {}. Add a narrower history folder to inspect remaining sessions.", root.path.display()));
        }
        files
    }

    fn project_for_gemini(file: &Path, settings: &AppSettings) -> Option<String> {
        let mut directory = file.parent();
        for _ in 0..4 {
            let Some(current) = directory else {
                break;
            };
            let marker = current.join(".project_root");
            if let Ok(info) = fs::symlink_metadata(&marker)
                && info.is_file()
                && !info.file_type().is_symlink()
                && info.len() < 16384
                && let Ok(project) = fs::read_to_string(&marker)
            {
                let project = project.trim();
                if absolute_metadata_path(project) {
                    return Some(project.to_owned());
                }
            }
            directory = current.parent();
        }
        let directory_key = file.parent()?.parent()?.file_name()?.to_str()?;
        settings
            .projects
            .iter()
            .find(|project| format!("{:x}", Sha256::digest(project.as_bytes())) == directory_key)
            .cloned()
    }

    fn antigravity_projects(root: &ScanRoot) -> HashMap<String, String> {
        let mut mapping = HashMap::new();
        for parent in [Some(root.path.as_path()), root.path.parent()]
            .into_iter()
            .flatten()
        {
            let cache = parent.join("cache/last_conversations.json");
            let Ok(info) = fs::symlink_metadata(&cache) else {
                continue;
            };
            if !info.is_file() || info.file_type().is_symlink() || info.len() > 1024 * 1024 {
                continue;
            }
            let Ok(file) = File::open(&cache) else {
                continue;
            };
            let Ok(contents) = serde_json::from_reader::<_, Value>(file.take(1024 * 1024)) else {
                continue;
            };
            if let Some(contents) = contents.as_object() {
                for (project, native_id) in contents {
                    if let Some(native_id) = native_id
                        .as_str()
                        .filter(|_| absolute_metadata_path(project))
                    {
                        mapping.insert(native_id.to_owned(), project.clone());
                    }
                }
            }
        }
        mapping
    }

    fn parse_file(
        &mut self,
        file: &Path,
        root: &ScanRoot,
        mapping: &HashMap<String, String>,
        settings: &AppSettings,
        include_messages: bool,
    ) -> DeskResult<Option<Transcript>> {
        let info = fs::symlink_metadata(file)
            .map_err(|error| format!("Could not inspect session source ({:?}).", error.kind()))?;
        if !info.is_file() || info.file_type().is_symlink() {
            return Err("Session source is not a regular file.".into());
        }
        let modified = info
            .modified()
            .map_err(|error| error.to_string())?
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();
        let mut ordered_mapping: Vec<_> = mapping.iter().collect();
        ordered_mapping.sort();
        let signature = json!([
            info.len(),
            modified.as_secs(),
            modified.subsec_nanos(),
            root.agent,
            root.source_kind,
            root.archived,
            settings.projects,
            ordered_mapping
        ])
        .to_string();
        if !include_messages
            && let Some(cached) = self
                .file_cache
                .get(file)
                .filter(|cached| cached.signature == signature)
        {
            return Ok(cached.transcript.clone());
        }
        let read = read_records(file)?;
        let mut input = SessionInput {
            agent: root.agent.clone(),
            source_path: file.to_string_lossy().into_owned(),
            source_kind: Some(root.source_kind.clone()),
            modified_at: read.modified_at,
            warnings: read.warnings,
            truncated: read.truncated,
            archived: root.archived,
            ..Default::default()
        };
        let transcript = match root.agent.as_str() {
            "claude" => parse_claude(&read.records, &input),
            "codex" => parse_codex(&read.records, &input),
            "gemini" => {
                input.project_path = Self::project_for_gemini(file, settings);
                parse_gemini(&read.records, &input)
            }
            "antigravity" => {
                let parts: Vec<_> = file
                    .components()
                    .map(|part| part.as_os_str().to_string_lossy().into_owned())
                    .collect();
                let native_id = parts
                    .iter()
                    .rposition(|part| part == "brain")
                    .and_then(|index| parts.get(index + 1))
                    .cloned()
                    .or_else(|| {
                        file.parent()?
                            .parent()?
                            .parent()?
                            .file_name()
                            .map(|name| name.to_string_lossy().into_owned())
                    });
                input.project_path = native_id.as_ref().and_then(|id| mapping.get(id)).cloned();
                input.native_id = native_id;
                parse_antigravity(&read.records, &input)
            }
            _ => return Err(format!("Unsupported session agent: {}", root.agent)),
        };
        if transcript.is_none() && !input.warnings.is_empty() {
            return Err(input.warnings.join(" "));
        }
        if self.file_cache.len() >= MAX_FILES
            && let Some(key) = self.file_cache.keys().next().cloned()
        {
            self.file_cache.remove(&key);
        }
        self.file_cache.insert(
            file.to_owned(),
            CachedFile {
                signature,
                transcript: transcript.as_ref().map(|transcript| Transcript {
                    session: transcript.session.clone(),
                    warnings: transcript.warnings.clone(),
                    truncated: transcript.truncated,
                    messages: Vec::new(),
                }),
            },
        );
        Ok(transcript)
    }

    fn scan(&mut self, settings: &AppSettings, key: String) -> DeskResult<SessionIndex> {
        let mut warnings = Vec::new();
        let mut deduped: HashMap<String, Source> = HashMap::new();
        let mut seen_files = HashSet::new();
        let native_roots = self.native_roots();
        let homes = self.homes();
        let command = settings
            .agent_commands
            .get("codex")
            .cloned()
            .unwrap_or_default();
        let codex_key = format!("{command}:{}", homes[1].display());
        if self.codex_key != codex_key {
            if let Some(codex) = &mut self.codex {
                codex.close();
            }
            self.codex = None;
            self.codex_key = codex_key;
            self.codex_retry_at = None;
            self.codex_warning.clear();
        }
        if !command.is_empty()
            && self
                .codex_retry_at
                .is_some_and(|retry| Instant::now() < retry)
        {
            warnings.push(self.codex_warning.clone());
        } else if !command.is_empty() && homes[1].exists() {
            let codex = self.codex.get_or_insert_with(|| {
                CodexHistory::new(
                    command.clone(),
                    homes[1].clone(),
                    self.home.clone(),
                    self.environment.clone(),
                )
            });
            match codex.index() {
                Ok((sessions, codex_warnings)) => {
                    self.codex_warning.clear();
                    warnings.extend(codex_warnings);
                    for session in sessions {
                        deduped.insert(
                            format!("codex:{}", session.native_id),
                            Source {
                                session,
                                root: None,
                                app_server: true,
                                native_store: true,
                            },
                        );
                    }
                }
                Err(error) => {
                    self.codex_warning = format!(
                        "{error} Local rollout files are being indexed; newer paginated-only history may be unavailable. The native history connection retries after one minute."
                    );
                    self.codex_retry_at = Some(Instant::now() + Duration::from_secs(60));
                    warnings.push(self.codex_warning.clone());
                    if let Some(codex) = &mut self.codex {
                        codex.close();
                    }
                    self.codex = None;
                }
            }
            if let Some(codex) = &mut self.codex {
                codex.close();
            }
            self.codex = None;
        }
        for root in self.roots(settings) {
            if !root.path.is_absolute() {
                warnings.push(format!(
                    "History folder must be an absolute path: {}",
                    root.path.display()
                ));
                continue;
            }
            let files = Self::walk(&root, &mut warnings);
            let mapping = if root.agent == "antigravity" {
                Self::antigravity_projects(&root)
            } else {
                HashMap::new()
            };
            for file in files {
                if !seen_files.insert(file.clone()) {
                    continue;
                }
                let native_root = native_roots.iter().find(|candidate| {
                    candidate.agent == root.agent && file.starts_with(&candidate.path)
                });
                let native_store = native_root.is_some();
                let source_root = native_root.unwrap_or(&root);
                let parsed = self.parse_file(&file, source_root, &mapping, settings, false);
                let filename = file.file_name().unwrap_or_default().to_string_lossy();
                let transcript = match parsed {
                    Ok(Some(transcript)) => transcript,
                    Ok(None) => continue,
                    Err(error) => {
                        warnings.push(format!("{filename}: {error}"));
                        continue;
                    }
                };
                warnings.extend(
                    transcript
                        .warnings
                        .iter()
                        .map(|warning| format!("{filename}: {warning}")),
                );
                let mut session = transcript.session;
                if !native_store {
                    session.resumable = false;
                    session.resume_note = Some("This history is outside the active native session store. Open or import it with its native app before resuming.".into());
                }
                let dedupe_key = format!("{}:{}", session.agent, session.native_id);
                if let Some(previous) = deduped
                    .get_mut(&dedupe_key)
                    .filter(|previous| previous.app_server)
                {
                    if !native_store {
                        continue;
                    }
                    previous.root = Some(source_root.clone());
                    previous.session.source_path = session.source_path;
                    if previous.session.project_path.is_empty() && !session.project_path.is_empty()
                    {
                        previous.session.project_path = session.project_path;
                        previous.session.project_name = session.project_name;
                        previous.session.resumable = session.resumable;
                        previous.session.resume_note = session.resume_note;
                    }
                    if previous.session.model.is_none() {
                        previous.session.model = session.model;
                    }
                    if previous.session.message_count == 0 {
                        previous.session.message_count = session.message_count;
                    }
                } else {
                    let priority = if native_store {
                        if session.archived.unwrap_or(false) {
                            1
                        } else {
                            2
                        }
                    } else {
                        0
                    };
                    let replace = deduped
                        .get(&dedupe_key)
                        .map(|previous| {
                            let previous_priority = if previous.native_store {
                                if previous.session.archived.unwrap_or(false) {
                                    1
                                } else {
                                    2
                                }
                            } else {
                                0
                            };
                            priority > previous_priority
                                || (priority == previous_priority
                                    && previous.session.updated_at < session.updated_at)
                        })
                        .unwrap_or(true);
                    if replace {
                        deduped.insert(
                            dedupe_key,
                            Source {
                                session,
                                root: Some(source_root.clone()),
                                native_store,
                                app_server: false,
                            },
                        );
                    }
                }
            }
        }
        let mut sources = HashMap::new();
        for (_, mut source) in deduped {
            if source.session.resumable && !Path::new(&source.session.project_path).is_dir() {
                source.session.resumable = false;
                source.session.resume_note = Some(
                    "The original project directory is not available on this computer.".into(),
                );
            }
            sources.insert(source.session.id.clone(), source);
        }
        let mut sessions: Vec<_> = sources
            .values()
            .map(|source| source.session.clone())
            .collect();
        sessions.sort_by(|left, right| {
            right
                .updated_at
                .cmp(&left.updated_at)
                .then_with(|| left.id.cmp(&right.id))
        });
        let mut unique_warnings = HashSet::new();
        warnings.retain(|warning| unique_warnings.insert(warning.clone()));
        warnings.truncate(200);
        let indexed = SessionIndex {
            sessions,
            warnings,
            scanned_at: now(),
        };
        self.sources = sources;
        self.file_cache.retain(|file, _| seen_files.contains(file));
        self.cached = Some(indexed.clone());
        self.cache_key = key;
        Ok(indexed)
    }

    pub fn transcript(&mut self, settings: &AppSettings, id: &str) -> DeskResult<Transcript> {
        self.index(settings, false)?;
        let source = self.sources.get(id).cloned().ok_or_else(|| {
            "Session not found. Refresh your history and select it again.".to_owned()
        })?;
        let mut api_failure = None;
        if source.app_server {
            if self
                .codex_retry_at
                .is_some_and(|retry| Instant::now() < retry)
            {
                api_failure = Some(self.codex_warning.clone());
            } else {
                let command = settings
                    .agent_commands
                    .get("codex")
                    .cloned()
                    .unwrap_or_default();
                self.codex = Some(CodexHistory::new(
                    command,
                    self.homes()[1].clone(),
                    self.home.clone(),
                    self.environment.clone(),
                ));
                let result = self.codex.as_mut().unwrap().transcript(&source.session);
                self.codex.as_mut().unwrap().close();
                self.codex = None;
                match result {
                    Ok(transcript) => return Ok(transcript),
                    Err(error) => {
                        self.codex_retry_at = Some(Instant::now() + Duration::from_secs(60));
                        self.codex_warning = format!(
                            "{error} Local rollout files are being indexed; newer paginated-only history may be unavailable. The native history connection retries after one minute."
                        );
                        api_failure = Some(error);
                    }
                }
            }
        }
        if let (Some(root), Some(file)) = (&source.root, &source.session.source_path) {
            let mapping = if root.agent == "antigravity" {
                Self::antigravity_projects(root)
            } else {
                HashMap::new()
            };
            let mut transcript = self
                .parse_file(Path::new(file), root, &mapping, settings, true)?
                .ok_or_else(|| {
                    "The session no longer contains a recognized transcript.".to_owned()
                })?;
            transcript.session = source.session;
            transcript.session.message_count = transcript.messages.len();
            if let Some(error) = api_failure {
                transcript
                    .warnings
                    .push(format!("{error} Showing the local rollout transcript."));
            }
            return Ok(transcript);
        }
        Err(api_failure
            .unwrap_or_else(|| "A readable transcript is not available for this session.".into()))
    }

    pub fn close(&mut self) {
        if let Some(codex) = &mut self.codex {
            codex.close();
        }
        self.codex = None;
        self.file_cache.clear();
        self.sources.clear();
        self.cached = None;
    }
}

impl Drop for SessionService {
    fn drop(&mut self) {
        self.close();
    }
}

#[cfg(test)]
#[path = "sessions_tests.rs"]
mod tests;
