use super::*;
use crate::types::HistoryRoot;
use serde_json::json;
use std::io::{Seek, SeekFrom, Write};
use tempfile::TempDir;

const TIMESTAMP: &str = "2026-11-16T09:00:00.000Z";

struct Fixture {
    service: SessionService,
    settings: AppSettings,
    project: String,
    home: TempDir,
}

impl Fixture {
    fn new() -> Self {
        let home = tempfile::tempdir().unwrap();
        let project = home.path().join("project");
        fs::create_dir(&project).unwrap();
        let mut service = SessionService::new(home.path().to_owned());
        for key in ["CLAUDE_CONFIG_DIR", "CODEX_HOME", "GEMINI_CLI_HOME"] {
            service.environment.remove(key);
        }
        let project = project.to_string_lossy().into_owned();
        let settings = AppSettings {
            projects: vec![project.clone()],
            agent_commands: HashMap::from([(
                "codex".into(),
                home.path()
                    .join("not-installed")
                    .to_string_lossy()
                    .into_owned(),
            )]),
            ..Default::default()
        };
        Self {
            service,
            settings,
            project,
            home,
        }
    }

    fn write(&self, relative: &str, content: &str) -> PathBuf {
        let file = self.home.path().join(relative);
        fs::create_dir_all(file.parent().unwrap()).unwrap();
        fs::write(&file, content).unwrap();
        file
    }

    fn jsonl(&self, relative: &str, records: &[Value]) -> PathBuf {
        self.write(
            relative,
            &format!(
                "{}\n",
                records
                    .iter()
                    .map(Value::to_string)
                    .collect::<Vec<_>>()
                    .join("\n")
            ),
        )
    }

    fn root(&mut self, agent: &str, relative: &str) {
        self.settings.history_roots.push(HistoryRoot {
            id: relative.into(),
            agent: agent.into(),
            path: self
                .home
                .path()
                .join(relative)
                .to_string_lossy()
                .into_owned(),
        });
    }

    fn index(&mut self) -> SessionIndex {
        self.service.index(&self.settings, false).unwrap()
    }

    fn transcript(&mut self, id: &str) -> Transcript {
        self.service.transcript(&self.settings, id).unwrap()
    }

    fn claude(&self, id: &str, text: &str) -> Value {
        json!({ "type": "user", "uuid": "u1", "sessionId": id, "cwd": self.project, "timestamp": TIMESTAMP, "message": { "role": "user", "content": text } })
    }

    fn fake_codex(&mut self, mode: &str) -> PathBuf {
        fs::create_dir_all(self.home.path().join(".codex")).unwrap();
        let script = r#"const readline = require('node:readline');
const fs = require('node:fs');
const project = PROJECT;
const mode = MODE;
const log = LOG;
if (mode === 'failure') { fs.appendFileSync(log, 'start\n'); process.exit(1); }
const turn = (id, text) => ({ id, startedAt: 1794819600, items: [{ id: id + '-item', type: 'agentMessage', text }] });
const thread = id => ({ id, cwd: project, name: 'Server ' + id, preview: 'From native metadata', createdAt: 1794816000, updatedAt: 1794819600, model: 'test-codex', source: 'cli' });
readline.createInterface({ input: process.stdin }).on('line', line => {
  const request = JSON.parse(line);
  fs.appendFileSync(log, JSON.stringify(request) + '\n');
  if (request.id === undefined) return;
  const p = request.params || {};
  if (mode === 'malformed') { process.stdout.write('{broken\n'); return; }
  if (mode === 'filters' && request.method === 'thread/list' && p.sourceKinds) { process.stdout.write(JSON.stringify({ id: request.id, error: { code: -32602 } }) + '\n'); return; }
  let result = {};
  if (request.method === 'thread/list') result = p.archived ? { data: [], nextCursor: null } : p.cursor ? { data: [thread('second')], nextCursor: mode === 'repeat' ? 'next-page' : null } : { data: [thread('first')], nextCursor: 'next-page' };
  if (request.method === 'thread/read') result = { thread: { ...thread(p.threadId), turns: p.includeTurns ? [turn('old', 'Legacy history')] : [] } };
  if (request.method === 'thread/turns/list') {
    if (mode === 'legacy') { process.stdout.write(JSON.stringify({ id: request.id, error: { code: -32601 } }) + '\n'); return; }
    result = p.cursor ? { data: [turn('earlier', 'Earlier turn')], nextCursor: mode === 'repeat' ? 'older-page' : null } : { data: [turn('latest', 'Latest turn')], nextCursor: 'older-page' };
  }
  process.stdout.write(JSON.stringify({ id: request.id, result }) + '\n');
});
"#;
        let log = self.home.path().join("requests.jsonl");
        let script = script
            .replace("PROJECT", &json!(self.project).to_string())
            .replace("MODE", &json!(mode).to_string())
            .replace("LOG", &json!(log).to_string());
        let command = self.write("fake-codex.cjs", &script);
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            fs::set_permissions(&command, fs::Permissions::from_mode(0o755)).unwrap();
        }
        self.settings
            .agent_commands
            .insert("codex".into(), command.to_string_lossy().into_owned());
        log
    }
}

#[test]
fn reconstructs_selected_claude_branch_and_reports_malformed_records() {
    let mut fixture = Fixture::new();
    let file = fixture.jsonl(".claude/projects/project/session-one.jsonl", &[
        json!({ "type": "user", "uuid": "u1", "parentUuid": null, "sessionId": "one", "cwd": fixture.project, "timestamp": TIMESTAMP, "message": { "role": "user", "content": "Build the desktop app" } }),
        json!({ "type": "assistant", "uuid": "a1", "parentUuid": "u1", "sessionId": "one", "timestamp": TIMESTAMP, "message": { "role": "assistant", "model": "abandoned-model", "content": "Abandoned answer" } }),
        json!({ "type": "assistant", "uuid": "a2", "parentUuid": "u1", "sessionId": "one", "timestamp": TIMESTAMP, "message": { "role": "assistant", "model": "selected-model", "content": [{ "type": "text", "text": "The current answer" }] } }),
        json!({ "type": "custom-title", "customTitle": "Agent Desk implementation" }),
    ]);
    writeln!(
        fs::OpenOptions::new().append(true).open(file).unwrap(),
        "{{incomplete"
    )
    .unwrap();
    fixture.jsonl(
        ".claude/projects/project/session-one/subagents/agent-one.jsonl",
        &[fixture.claude("sub", "Not a parent session")],
    );
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 1);
    let session = &index.sessions[0];
    assert_eq!(session.title, "Agent Desk implementation");
    assert_eq!(session.model.as_deref(), Some("selected-model"));
    assert_eq!(session.project_path, fixture.project);
    assert!(session.resumable);
    assert!(index.warnings.join(" ").contains("malformed"));
    let transcript = fixture.transcript(&session.id);
    assert_eq!(
        transcript
            .messages
            .iter()
            .map(|message| message.content.as_str())
            .collect::<Vec<_>>(),
        ["Build the desktop app", "The current answer"]
    );
    assert!(fixture.service.file_cache.values().all(|cached| {
        cached
            .transcript
            .as_ref()
            .is_none_or(|transcript| transcript.messages.is_empty())
    }));
}

#[test]
fn reads_codex_rollouts_and_archives_with_visible_missing_server_warning() {
    let mut fixture = Fixture::new();
    let mut records = vec![
        json!({ "type": "session_meta", "payload": { "id": "codex-one", "cwd": fixture.project, "source": "cli", "timestamp": TIMESTAMP } }),
        json!({ "type": "turn_context", "payload": { "cwd": fixture.project, "model": "context-model" } }),
        json!({ "type": "response_item", "timestamp": TIMESTAMP, "payload": { "type": "message", "role": "user", "content": [{ "type": "input_text", "text": "Inspect the proxy" }] } }),
        json!({ "type": "response_item", "timestamp": TIMESTAMP, "payload": { "type": "message", "role": "assistant", "content": [{ "type": "output_text", "text": "Configured" }] } }),
        json!({ "type": "event_msg", "timestamp": TIMESTAMP, "payload": { "type": "user_message", "message": "Duplicate event" } }),
    ];
    fixture.jsonl(".codex/sessions/2026/11/16/rollout-one.jsonl", &records);
    records[0]["payload"]["id"] = "codex-archived".into();
    fixture.jsonl(".codex/archived_sessions/rollout-archived.jsonl", &records);
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 2);
    assert!(index.warnings.join(" ").contains("Local rollout files"));
    assert!(index.warnings.join(" ").contains("not found"));
    let active = index
        .sessions
        .iter()
        .find(|session| !session.archived.unwrap_or(false))
        .unwrap();
    assert_eq!(active.model.as_deref(), Some("context-model"));
    assert!(active.resumable);
    assert!(
        !index
            .sessions
            .iter()
            .find(|session| session.archived.unwrap_or(false))
            .unwrap()
            .resumable
    );
    assert_eq!(
        fixture
            .transcript(&active.id)
            .messages
            .iter()
            .map(|message| message.role.as_str())
            .collect::<Vec<_>>(),
        ["user", "assistant"]
    );
}

#[test]
fn deduplicates_claude_updates_without_parent_links() {
    let mut fixture = Fixture::new();
    fixture.jsonl(".claude/projects/project/repeated.jsonl", &[
        fixture.claude("repeated", "Review the change"),
        json!({ "type": "assistant", "uuid": "a1", "sessionId": "repeated", "message": { "role": "assistant", "content": "Partial" } }),
        json!({ "type": "assistant", "uuid": "a1", "sessionId": "repeated", "message": { "role": "assistant", "content": "Complete" } }),
    ]);
    let index = fixture.index();
    assert_eq!(
        fixture
            .transcript(&index.sessions[0].id)
            .messages
            .iter()
            .map(|message| message.content.as_str())
            .collect::<Vec<_>>(),
        ["Review the change", "Complete"]
    );
}

#[test]
fn reads_legacy_gemini_and_actual_project_marker() {
    let mut fixture = Fixture::new();
    fixture.write(".gemini/tmp/project-slug/.project_root", &fixture.project);
    fixture.write(".gemini/tmp/project-slug/chats/session-old.json", &json!({
        "sessionId": "gemini-legacy", "projectHash": "opaque", "startTime": TIMESTAMP, "lastUpdated": TIMESTAMP,
        "messages": [ { "id": "g1", "type": "user", "content": [{ "text": "Fix the status line" }] }, { "id": "g2", "type": "gemini", "model": "gemini-local", "content": "Fixed it." } ]
    }).to_string());
    let index = fixture.index();
    let session = &index.sessions[0];
    assert_eq!(session.native_id, "gemini-legacy");
    assert_eq!(session.project_path, fixture.project);
    assert!(session.resumable);
    assert_eq!(session.model.as_deref(), Some("gemini-local"));
    assert_eq!(
        fixture.transcript(&session.id).messages[0].content,
        "Fix the status line"
    );
}

#[test]
fn applies_gemini_patch_tools_metadata_and_rewind() {
    let fixture = Fixture::new();
    let records = vec![
        json!({ "sessionId": "gemini-current", "projectHash": "hash", "startTime": TIMESTAMP }),
        json!({ "id": "u1", "type": "user", "content": "Original prompt" }),
        json!({ "id": "a1", "type": "gemini", "content": "Initial response", "toolCalls": [{ "id": "t1", "name": "read_file", "args": { "path": "README.md" } }] }),
        json!({ "$patch": { "updates": [ { "id": "u1", "content": "Corrected prompt" }, { "id": "a1", "content": "Final response", "toolCalls": [{ "id": "t1", "result": [{ "text": "File content" }] }] } ] } }),
        json!({ "id": "u2", "type": "user", "content": "Discard branch" }),
        json!({ "id": "a2", "type": "gemini", "content": "Discard response" }),
        json!({ "$rewindTo": "u2" }),
        json!({ "$set": { "summary": "Reviewed readme", "lastUpdated": TIMESTAMP } }),
    ];
    let input = SessionInput {
        agent: "gemini".into(),
        source_path: "/tmp/session.jsonl".into(),
        modified_at: TIMESTAMP.into(),
        project_path: Some(fixture.project),
        ..Default::default()
    };
    let transcript = parse_gemini(&records, &input).unwrap();
    assert_eq!(transcript.session.title, "Reviewed readme");
    assert_eq!(
        transcript
            .messages
            .iter()
            .map(|message| message.content.as_str())
            .collect::<Vec<_>>(),
        [
            "Corrected prompt",
            "Final response",
            "read_file\nFile content"
        ]
    );
    let mut reorder = records[..3].to_vec();
    reorder.push(json!({ "$patch": { "orderIds": ["a1", "u1"] } }));
    assert_eq!(parse_gemini(&reorder, &input).unwrap().messages[0].id, "a1");
    reorder.push(json!({ "$patch": { "removeIds": ["a1"] } }));
    assert_eq!(parse_gemini(&reorder, &input).unwrap().messages.len(), 1);
    reorder.push(json!({ "$set": { "messages": [{ "id": "new", "type": "user", "content": "Replacement" }] } }));
    assert_eq!(
        parse_gemini(&reorder, &input).unwrap().messages[0].id,
        "new"
    );
}

#[test]
fn never_invents_gemini_cwd_from_opaque_folders() {
    let mut fixture = Fixture::new();
    fixture.jsonl(
        ".gemini/tmp/opaque/chats/session-current.jsonl",
        &[
            json!({ "sessionId": "unmapped", "projectHash": "opaque" }),
            json!({ "id": "g1", "type": "user", "content": "Find project" }),
        ],
    );
    let session = &fixture.index().sessions[0];
    assert_eq!(session.project_path, "");
    assert!(!session.resumable);
    assert!(
        session
            .resume_note
            .as_deref()
            .unwrap()
            .contains("could not be determined")
    );
}

#[test]
fn respects_gemini_home_parent_and_known_project_hash() {
    let mut fixture = Fixture::new();
    fixture.service.environment.insert(
        "GEMINI_CLI_HOME".into(),
        fixture
            .home
            .path()
            .join("isolated")
            .to_string_lossy()
            .into_owned(),
    );
    let hash = format!("{:x}", Sha256::digest(fixture.project.as_bytes()));
    fixture.jsonl(
        &format!("isolated/.gemini/tmp/{hash}/chats/session-isolated.jsonl"),
        &[
            json!({ "sessionId": "isolated" }),
            json!({ "id": "g1", "type": "user", "content": "Isolated state" }),
        ],
    );
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 1);
    assert_eq!(index.sessions[0].native_id, "isolated");
    assert_eq!(index.sessions[0].project_path, fixture.project);
    assert!(index.sessions[0].resumable);
}

#[test]
fn indexes_antigravity_cli_and_separates_app_and_ide_imports() {
    let mut fixture = Fixture::new();
    fixture.write(
        ".gemini/antigravity-cli/cache/last_conversations.json",
        &json!({ &fixture.project: "agy-cli" }).to_string(),
    );
    fixture.jsonl(
        ".gemini/antigravity-cli/brain/agy-cli/.system_generated/logs/transcript.jsonl",
        &[
            json!({ "type": "user", "content": "Continue CLI", "timestamp": TIMESTAMP }),
            json!({ "type": "assistant", "content": "Ready", "timestamp": TIMESTAMP }),
        ],
    );
    for (directory, id) in [("antigravity", "agy-app"), ("antigravity-ide", "agy-ide")] {
        fixture.jsonl(&format!(".gemini/{directory}/brain/{id}/.system_generated/logs/transcript.jsonl"), &[json!({ "type": "user", "content": "Other app", "workspacePaths": [&fixture.project], "timestamp": TIMESTAMP })]);
    }
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 3);
    let cli = index
        .sessions
        .iter()
        .find(|session| session.native_id == "agy-cli")
        .unwrap();
    assert_eq!(cli.project_path, fixture.project);
    assert_eq!(cli.source_kind, "cli");
    assert!(cli.resumable);
    for session in index
        .sessions
        .iter()
        .filter(|session| session.native_id != "agy-cli")
    {
        assert!(!session.resumable);
        assert!(
            session
                .resume_note
                .as_deref()
                .unwrap()
                .contains("/resume → Other")
        );
    }
}

#[test]
fn reports_unrecognized_antigravity_rows_without_fabricated_messages() {
    let mut fixture = Fixture::new();
    fixture.jsonl(
        ".gemini/antigravity-cli/brain/agy-unknown/.system_generated/logs/transcript.jsonl",
        &[json!({ "storageVersion": 999, "binary": "opaque" })],
    );
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 1);
    assert!(
        index
            .warnings
            .join(" ")
            .contains("no recognized message records")
    );
    assert!(
        fixture
            .transcript(&index.sessions[0].id)
            .messages
            .is_empty()
    );
}

#[test]
fn custom_root_is_view_only_and_refresh_reloads_changed_files() {
    let mut fixture = Fixture::new();
    let file = fixture.jsonl(
        "custom-history/session.jsonl",
        &[fixture.claude("custom", "First message")],
    );
    fixture.root("claude", "custom-history");
    #[cfg(unix)]
    {
        std::os::unix::fs::symlink(file.parent().unwrap(), file.parent().unwrap().join("cycle"))
            .unwrap();
        std::os::unix::fs::symlink(&file, file.parent().unwrap().join("copy.jsonl")).unwrap();
    }
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 1);
    assert!(!index.sessions[0].resumable);
    assert!(
        index.sessions[0]
            .resume_note
            .as_deref()
            .unwrap()
            .contains("outside the active native session store")
    );
    writeln!(fs::OpenOptions::new().append(true).open(file).unwrap(), "{}", json!({ "type": "assistant", "sessionId": "custom", "message": { "role": "assistant", "content": "Second message" } })).unwrap();
    let index = fixture.service.index(&fixture.settings, true).unwrap();
    assert_eq!(fixture.transcript(&index.sessions[0].id).messages.len(), 2);
    assert!(
        fixture
            .service
            .transcript(&fixture.settings, "../../credentials.json")
            .unwrap_err()
            .contains("Session not found")
    );
}

#[test]
fn prefers_native_identity_over_newer_export() {
    let mut fixture = Fixture::new();
    let record = fixture.claude("same-session", "Native conversation");
    let native = fixture.jsonl(
        ".claude/projects/project/same-session.jsonl",
        std::slice::from_ref(&record),
    );
    let mut exported = record;
    exported["timestamp"] = "2026-11-17T09:00:00.000Z".into();
    exported["message"]["content"] = "Newer exported copy".into();
    fixture.jsonl("exports/same-session.jsonl", &[exported]);
    fixture.root("claude", ".claude/projects");
    fixture.root("claude", "exports");
    let index = fixture.index();
    assert_eq!(index.sessions.len(), 1);
    assert_eq!(
        Path::new(index.sessions[0].source_path.as_deref().unwrap())
            .canonicalize()
            .unwrap(),
        native.canonicalize().unwrap()
    );
    assert!(index.sessions[0].resumable);
    assert_eq!(
        fixture.transcript(&index.sessions[0].id).messages[0].content,
        "Native conversation"
    );
}

#[test]
fn external_history_becomes_resumable_only_as_configured_native_store() {
    let mut fixture = Fixture::new();
    fixture.jsonl(
        "alternate-config/projects/project/session.jsonl",
        &[fixture.claude("alternate", "Separate native config")],
    );
    fixture.root("claude", "alternate-config/projects");
    assert!(!fixture.index().sessions[0].resumable);
    fixture.service.environment.insert(
        "CLAUDE_CONFIG_DIR".into(),
        fixture
            .home
            .path()
            .join("alternate-config")
            .to_string_lossy()
            .into_owned(),
    );
    let session = &fixture.index().sessions[0];
    assert!(session.resumable);
    assert!(session.resume_note.is_none());
}

#[test]
fn arbitrary_antigravity_export_remains_desktop_import() {
    let mut fixture = Fixture::new();
    fixture.jsonl(
        "exports/brain/agy-copy/.system_generated/logs/transcript.jsonl",
        &[json!({ "type": "user", "cwd": fixture.project, "content": "Copied desktop history" })],
    );
    fixture.root("antigravity", "exports");
    let session = &fixture.index().sessions[0];
    assert_eq!(session.native_id, "agy-copy");
    assert_eq!(session.source_kind, "desktop");
    assert!(!session.resumable);
    assert!(
        session
            .resume_note
            .as_deref()
            .unwrap()
            .contains("outside the active native session store")
    );
}

#[test]
fn missing_project_disables_resume() {
    let mut fixture = Fixture::new();
    let mut record = fixture.claude("deleted", "Old project");
    record["cwd"] = fixture
        .home
        .path()
        .join("missing")
        .to_string_lossy()
        .into_owned()
        .into();
    fixture.jsonl(".claude/projects/deleted/session.jsonl", &[record]);
    let session = &fixture.index().sessions[0];
    assert!(!session.resumable);
    assert_eq!(
        session.resume_note.as_deref(),
        Some("The original project directory is not available on this computer.")
    );
}

#[test]
fn app_server_initializes_pages_all_providers_and_reads_without_resuming() {
    let mut fixture = Fixture::new();
    let log = fixture.fake_codex("current");
    let index = fixture.index();
    assert!(index.warnings.is_empty(), "{:?}", index.warnings);
    assert_eq!(index.sessions.len(), 2);
    assert!(fixture.service.codex.is_none());
    let transcript = fixture.transcript(&index.sessions[0].id);
    assert!(fixture.service.codex.is_none());
    assert_eq!(
        transcript
            .messages
            .iter()
            .map(|message| message.content.as_str())
            .collect::<Vec<_>>(),
        ["Earlier turn", "Latest turn"]
    );
    let requests: Vec<Value> = fs::read_to_string(log)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert!(
        requests
            .iter()
            .any(|request| request["method"] == "initialize")
    );
    assert_eq!(
        requests
            .iter()
            .filter(|request| request["method"] == "initialize")
            .count(),
        2
    );
    assert!(
        requests
            .iter()
            .any(|request| request["method"] == "initialized")
    );
    assert!(
        requests
            .iter()
            .filter(|request| request["method"] == "thread/list")
            .all(|request| request["params"]["modelProviders"] == json!([]))
    );
    assert!(
        requests
            .iter()
            .any(|request| request["method"] == "thread/turns/list"
                && request["params"]["cursor"] == "older-page")
    );
    assert!(
        !requests.iter().any(
            |request| request["method"] == "thread/resume" || request["method"] == "turn/start"
        )
    );
}

#[test]
fn app_server_legacy_history_and_filters_have_visible_compatibility_warnings() {
    for mode in ["legacy", "filters"] {
        let mut fixture = Fixture::new();
        fixture.fake_codex(mode);
        let index = fixture.index();
        assert_eq!(index.sessions.len(), 2, "{:?}", index.warnings);
        if mode == "legacy" {
            let transcript = fixture.transcript(&index.sessions[0].id);
            assert_eq!(transcript.messages[0].content, "Legacy history");
            assert!(transcript.warnings.join(" ").contains("older thread/read"));
        } else {
            assert!(index.warnings.join(" ").contains("fewer thread filters"));
        }
    }
}

#[test]
fn app_server_failure_is_not_respawned_on_every_refresh() {
    let mut fixture = Fixture::new();
    let log = fixture.fake_codex("failure");
    let first = fixture.index();
    let second = fixture.service.index(&fixture.settings, true).unwrap();
    assert!(first.warnings.join(" ").contains("closed"));
    assert!(
        second
            .warnings
            .join(" ")
            .contains("retries after one minute")
    );
    assert_eq!(fs::read_to_string(log).unwrap().lines().count(), 1);
}

#[test]
fn app_server_repeated_cursors_are_bounded_and_invalid_json_is_visible() {
    let mut fixture = Fixture::new();
    fixture.fake_codex("repeat");
    let index = fixture.index();
    assert!(
        index
            .warnings
            .join(" ")
            .contains("repeated a history cursor")
    );
    let transcript = fixture.transcript(&index.sessions[0].id);
    assert_eq!(transcript.truncated, Some(true));
    assert!(
        transcript
            .warnings
            .join(" ")
            .contains("repeated a transcript cursor")
    );
    let mut malformed = Fixture::new();
    malformed.fake_codex("malformed");
    assert!(
        malformed
            .index()
            .warnings
            .join(" ")
            .contains("invalid JSON")
    );
}

#[test]
fn bounded_read_rejects_large_legacy_json_and_marks_partial_jsonl() {
    let fixture = Fixture::new();
    let legacy = fixture.write("session-large.json", "{}");
    File::options()
        .write(true)
        .open(&legacy)
        .unwrap()
        .set_len((MAX_FILE_BYTES + 1024) as u64)
        .unwrap();
    assert!(read_records(&legacy).unwrap_err().contains("32 MiB"));
    let jsonl = fixture.jsonl(
        "session-large.jsonl",
        &[fixture.claude("large", "First message")],
    );
    let mut file = File::options().write(true).open(&jsonl).unwrap();
    file.set_len((MAX_FILE_BYTES + 1024) as u64).unwrap();
    file.seek(SeekFrom::End(0)).unwrap();
    writeln!(file, "\n{}", fixture.claude("large", "Last message")).unwrap();
    let read = read_records(&jsonl).unwrap();
    assert!(read.truncated);
    assert!(read.warnings.join(" ").contains("partial view"));
    assert_eq!(read.records.len(), 2);
}

#[test]
fn dto_serialization_preserves_existing_camel_case_contract() {
    let mut fixture = Fixture::new();
    fixture.jsonl(
        ".claude/projects/project/session.jsonl",
        &[fixture.claude("dto", "Contract")],
    );
    let index = fixture.index();
    let encoded = serde_json::to_value(&index).unwrap();
    let session = &encoded["sessions"][0];
    assert_eq!(session["nativeId"], "dto");
    assert_eq!(session["projectPath"], fixture.project);
    assert_eq!(session["messageCount"], 1);
    assert!(session.get("native_id").is_none());
    assert!(session.get("archived").is_none());
    assert!(encoded.get("scannedAt").is_some());
}
