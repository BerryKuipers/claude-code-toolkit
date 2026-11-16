use crate::types::{SessionMessage, SessionRecord, Transcript};
use chrono::{DateTime, NaiveDate, SecondsFormat, Utc};
use indexmap::IndexMap;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};

pub const MAX_MESSAGES: usize = 5000;
pub const MAX_CONTENT: usize = 80000;

#[derive(Clone, Default)]
pub struct SessionInput {
    pub agent: String,
    pub source_path: String,
    pub source_kind: Option<String>,
    pub modified_at: String,
    pub project_path: Option<String>,
    pub native_id: Option<String>,
    pub title: Option<String>,
    pub archived: bool,
    pub warnings: Vec<String>,
    pub truncated: bool,
}

#[derive(Default)]
pub struct SessionFields {
    pub native_id: Option<String>,
    pub project_path: Option<String>,
    pub source_kind: Option<String>,
    pub title: Option<String>,
    pub created_at: Option<String>,
    pub updated_at: Option<String>,
    pub model: Option<String>,
    pub resume_note: Option<String>,
}

pub fn string(value: &Value) -> &str {
    value.as_str().unwrap_or("")
}

pub fn nonempty(value: &Value) -> Option<String> {
    value
        .as_str()
        .filter(|value| !value.is_empty())
        .map(str::to_owned)
}

pub fn list(value: &Value) -> &[Value] {
    value.as_array().map(Vec::as_slice).unwrap_or(&[])
}

pub fn head(value: &str, limit: usize) -> String {
    value.chars().take(limit).collect()
}

pub fn tail(value: &str, limit: usize) -> String {
    let offset = value
        .char_indices()
        .rev()
        .nth(limit.saturating_sub(1))
        .map(|(offset, _)| offset)
        .unwrap_or(0);
    value[offset..].to_owned()
}

pub fn now() -> String {
    Utc::now().to_rfc3339_opts(SecondsFormat::Millis, true)
}

pub fn date(value: &Value, fallback: &str) -> String {
    let parsed = if let Some(number) = value.as_f64() {
        let millis = if number < 1e11 {
            number * 1000.0
        } else {
            number
        };
        if millis.is_finite() && millis >= i64::MIN as f64 && millis <= i64::MAX as f64 {
            DateTime::from_timestamp_millis(millis as i64)
        } else {
            None
        }
    } else {
        DateTime::parse_from_rfc3339(string(value))
            .ok()
            .map(|time| time.with_timezone(&Utc))
            .or_else(|| {
                NaiveDate::parse_from_str(string(value), "%Y-%m-%d")
                    .ok()
                    .and_then(|date| date.and_hms_opt(0, 0, 0))
                    .map(|date| date.and_utc())
            })
    };
    parsed
        .map(|time| time.to_rfc3339_opts(SecondsFormat::Millis, true))
        .unwrap_or_else(|| fallback.to_owned())
}

fn coalesce<'a>(values: &[&'a Value]) -> &'a Value {
    values
        .iter()
        .copied()
        .find(|value| !value.is_null())
        .unwrap_or(&Value::Null)
}

pub fn content_text(value: &Value) -> String {
    content_at(value, 0)
}

fn content_at(value: &Value, depth: usize) -> String {
    if depth > 8 || value.is_null() {
        return String::new();
    }
    if let Some(text) = value.as_str() {
        return head(text, MAX_CONTENT);
    }
    if let Some(values) = value.as_array() {
        let mut output = String::new();
        for value in values.iter().take(200) {
            let content = content_at(value, depth + 1);
            if !content.is_empty() {
                if !output.is_empty() {
                    output.push('\n');
                }
                output.push_str(&content);
                if output.len() >= MAX_CONTENT * 4 {
                    break;
                }
            }
        }
        return head(&output, MAX_CONTENT);
    }
    if let Some(text) = value["text"].as_str() {
        return head(text, MAX_CONTENT);
    }
    let kind = string(&value["type"]);
    if matches!(kind, "tool_use" | "function_call") {
        let args = coalesce(&[&value["input"], &value["arguments"]]);
        let serialized = if args.is_null() {
            String::new()
        } else {
            args.as_str()
                .map(str::to_owned)
                .unwrap_or_else(|| args.to_string())
        };
        let name = nonempty(&value["name"]).unwrap_or_else(|| "Tool".into());
        return head(
            &if serialized.is_empty() {
                name
            } else {
                format!("{name}\n{serialized}")
            },
            MAX_CONTENT,
        );
    }
    if matches!(kind, "image" | "image_url") || !value["inlineData"].is_null() {
        return "[Image attachment]".into();
    }
    for key in [
        "content",
        "parts",
        "message",
        "output",
        "result",
        "response",
        "markdown",
        "text_delta",
    ] {
        if !value[key].is_null() {
            let text = content_at(&value[key], depth + 1);
            if !text.is_empty() {
                return text;
            }
        }
    }
    String::new()
}

fn title_from(messages: &[SessionMessage]) -> String {
    if let Some(message) = messages
        .iter()
        .find(|message| message.role == "user" && !message.content.trim().is_empty())
    {
        let mut inside_tag = false;
        let text: String = message
            .content
            .chars()
            .filter_map(|character| {
                if character == '<' {
                    inside_tag = true;
                    Some(' ')
                } else if character == '>' && inside_tag {
                    inside_tag = false;
                    Some(' ')
                } else if inside_tag {
                    None
                } else {
                    Some(character)
                }
            })
            .collect();
        let title = head(&text.split_whitespace().collect::<Vec<_>>().join(" "), 110);
        if !title.is_empty() {
            return title;
        }
    }
    "Untitled session".into()
}

pub fn session_key(agent: &str, native_id: &str, source_path: &str) -> String {
    let source = if source_path.is_empty() {
        agent
    } else {
        source_path
    };
    let digest = format!("{:x}", Sha256::digest(source.as_bytes()));
    format!("{agent}:{native_id}:{}", &digest[..12])
}

pub fn project_name(project_path: &str) -> String {
    if project_path.is_empty() {
        return "Unknown project".into();
    }
    project_path
        .rsplit(['/', '\\'])
        .find(|part| !part.is_empty())
        .unwrap_or(project_path)
        .to_owned()
}

pub fn make_transcript(
    input: &SessionInput,
    fields: SessionFields,
    all_messages: Vec<SessionMessage>,
) -> Transcript {
    let native_id = fields
        .native_id
        .filter(|value| !value.is_empty())
        .or_else(|| input.native_id.clone())
        .unwrap_or_else(|| {
            input
                .source_path
                .rsplit(['/', '\\'])
                .next()
                .unwrap_or("")
                .trim_end_matches(".jsonl")
                .trim_end_matches(".json")
                .to_owned()
        });
    let project_path = fields
        .project_path
        .filter(|value| !value.is_empty())
        .or_else(|| input.project_path.clone())
        .unwrap_or_default();
    let source_kind = fields
        .source_kind
        .or_else(|| input.source_kind.clone())
        .unwrap_or_else(|| "cli".into());
    let message_count = all_messages.len();
    let messages: Vec<_> = all_messages
        .into_iter()
        .skip(message_count.saturating_sub(MAX_MESSAGES))
        .collect();
    let desktop_import = input.agent == "antigravity" && source_kind != "cli";
    let resume_note = if input.archived {
        Some("This session is archived. Restore it in its native CLI before resuming.".into())
    } else {
        fields.resume_note.or_else(|| if desktop_import {
            Some("Import this conversation through Antigravity CLI /resume → Other. Native import creates a copy.".into())
        } else if project_path.is_empty() {
            Some("The original project directory could not be determined. Add its project mapping before resuming.".into())
        } else { None })
    };
    let visible: Vec<_> = messages
        .iter()
        .filter(|message| matches!(message.role.as_str(), "user" | "assistant"))
        .collect();
    let preview = tail(
        &visible
            .iter()
            .skip(visible.len().saturating_sub(3))
            .map(|message| message.content.as_str())
            .collect::<Vec<_>>()
            .join("\n"),
        2400,
    );
    let session = SessionRecord {
        id: session_key(&input.agent, &native_id, &input.source_path),
        resumable: !native_id.is_empty()
            && !project_path.is_empty()
            && !desktop_import
            && !input.archived,
        native_id,
        agent: input.agent.clone(),
        title: fields
            .title
            .filter(|value| !value.is_empty())
            .or_else(|| input.title.clone())
            .unwrap_or_else(|| title_from(&messages)),
        project_name: project_name(&project_path),
        project_path,
        created_at: fields
            .created_at
            .or_else(|| {
                messages
                    .first()
                    .and_then(|message| message.timestamp.clone())
            })
            .unwrap_or_else(|| input.modified_at.clone()),
        updated_at: fields
            .updated_at
            .or_else(|| {
                messages
                    .last()
                    .and_then(|message| message.timestamp.clone())
            })
            .unwrap_or_else(|| input.modified_at.clone()),
        preview,
        message_count,
        model: fields.model.or_else(|| {
            messages
                .iter()
                .rev()
                .find_map(|message| message.model.clone())
        }),
        source_path: if input.source_path.is_empty() {
            None
        } else {
            Some(input.source_path.clone())
        },
        source_kind,
        resume_note,
        archived: if input.archived { Some(true) } else { None },
    };
    Transcript {
        session,
        messages,
        warnings: input.warnings.clone(),
        truncated: if input.truncated || message_count > MAX_MESSAGES {
            Some(true)
        } else {
            None
        },
    }
}

fn claude_messages(records: &[&Value]) -> Vec<SessionMessage> {
    records
        .iter()
        .enumerate()
        .filter_map(|(index, record)| {
            let message = &record["message"];
            let raw = coalesce(&[&message["content"], &record["content"]]);
            let content = content_text(raw);
            if content.is_empty() {
                return None;
            }
            let role = nonempty(&message["role"]).unwrap_or_else(|| string(&record["type"]).into());
            if !matches!(role.as_str(), "user" | "assistant" | "system" | "tool") {
                return None;
            }
            let tool_result = list(raw).iter().any(|block| block["type"] == "tool_result");
            let tool_name = list(raw)
                .iter()
                .find(|block| block["type"] == "tool_use")
                .and_then(|block| nonempty(&block["name"]));
            Some(SessionMessage {
                id: nonempty(&record["uuid"]).unwrap_or_else(|| format!("message-{index}")),
                role: if tool_result { "tool".into() } else { role },
                content,
                timestamp: nonempty(&record["timestamp"]),
                model: nonempty(&message["model"]),
                tool_name,
            })
        })
        .collect()
}

pub fn parse_claude(records: &[Value], input: &SessionInput) -> Option<Transcript> {
    let relevant: Vec<_> = records
        .iter()
        .filter(|record| {
            record["isSidechain"] != true
                && matches!(
                    string(&record["type"]),
                    "user" | "assistant" | "system" | "tool"
                )
        })
        .collect();
    if relevant.is_empty() {
        return None;
    }
    let mut input = input.clone();
    let native_id = relevant
        .iter()
        .rev()
        .find_map(|record| nonempty(&record["sessionId"]))
        .or_else(|| input.native_id.clone());
    let project_path = relevant
        .iter()
        .rev()
        .find_map(|record| nonempty(&record["cwd"]))
        .or_else(|| input.project_path.clone());
    let title = records.iter().rev().find_map(|record| {
        nonempty(&record["customTitle"]).or_else(|| {
            if record["type"] == "summary" {
                nonempty(&record["summary"])
            } else {
                None
            }
        })
    });
    let mut distinct = IndexMap::new();
    for (index, record) in relevant.iter().enumerate() {
        distinct.insert(
            nonempty(&record["uuid"]).unwrap_or_else(|| format!("record-{index}")),
            *record,
        );
    }
    let mut ordered: Vec<_> = distinct.values().copied().collect();
    if let Some(last) = relevant
        .iter()
        .rev()
        .find(|record| matches!(string(&record["type"]), "user" | "assistant" | "tool"))
        && last.get("parentUuid").is_some()
        && !string(&last["uuid"]).is_empty()
    {
        let nodes: HashMap<_, _> = records
            .iter()
            .filter(|record| !string(&record["uuid"]).is_empty())
            .map(|record| (string(&record["uuid"]), record))
            .collect();
        let mut chain = Vec::new();
        let mut seen = HashSet::new();
        let mut cursor = Some(*last);
        while let Some(record) = cursor {
            if !seen.insert(string(&record["uuid"])) {
                break;
            }
            if record["isSidechain"] != true {
                chain.push(record);
            }
            let parent = string(&record["parentUuid"]);
            if !parent.is_empty() && !nodes.contains_key(parent) {
                input
                    .warnings
                    .push("Some earlier messages are unavailable in this transcript chain.".into());
            }
            cursor = nodes.get(parent).copied();
        }
        chain.reverse();
        ordered = chain;
    }
    let messages = claude_messages(&ordered);
    if messages.is_empty() {
        return None;
    }
    Some(make_transcript(
        &input,
        SessionFields {
            native_id,
            project_path,
            title,
            created_at: Some(date(&relevant[0]["timestamp"], &input.modified_at)),
            updated_at: Some(date(
                &relevant.last().unwrap()["timestamp"],
                &input.modified_at,
            )),
            ..Default::default()
        },
        messages,
    ))
}

pub fn parse_codex(records: &[Value], input: &SessionInput) -> Option<Transcript> {
    let metadata = &records
        .iter()
        .find(|record| record["type"] == "session_meta")?["payload"];
    if metadata
        .as_object()
        .map(|value| value.is_empty())
        .unwrap_or(true)
    {
        return None;
    }
    if metadata["source"]
        .as_object()
        .map(|source| {
            source.keys().any(|key| {
                key.to_ascii_lowercase()
                    .replace(['_', '-'], "")
                    .contains("subagent")
            })
        })
        .unwrap_or(false)
    {
        return None;
    }
    let context = records
        .iter()
        .rev()
        .find(|record| record["type"] == "turn_context")
        .map(|record| &record["payload"])
        .unwrap_or(&Value::Null);
    let has_messages = records
        .iter()
        .any(|record| record["type"] == "response_item" && record["payload"]["type"] == "message");
    let mut messages = Vec::new();
    for (index, record) in records.iter().enumerate() {
        let payload = &record["payload"];
        if record["type"] == "response_item" {
            let kind = string(&payload["type"]);
            let role = if matches!(
                kind,
                "function_call" | "custom_tool_call" | "function_call_output"
            ) {
                "tool"
            } else {
                string(&payload["role"])
            };
            if !matches!(role, "user" | "assistant" | "system" | "tool") {
                continue;
            }
            let content = if kind == "function_call" {
                content_text(payload)
            } else {
                content_text(coalesce(&[
                    &payload["content"],
                    &payload["output"],
                    &payload["input"],
                ]))
            };
            if content.is_empty() {
                continue;
            }
            messages.push(SessionMessage {
                id: nonempty(&payload["id"]).unwrap_or_else(|| format!("response-{index}")),
                role: role.into(),
                content,
                timestamp: nonempty(&record["timestamp"]),
                model: None,
                tool_name: nonempty(&payload["name"]),
            });
        } else if record["type"] == "event_msg"
            && !has_messages
            && matches!(string(&payload["type"]), "user_message" | "agent_message")
        {
            let content = content_text(&payload["message"]);
            if !content.is_empty() {
                messages.push(SessionMessage {
                    id: format!("event-{index}"),
                    role: if payload["type"] == "user_message" {
                        "user"
                    } else {
                        "assistant"
                    }
                    .into(),
                    content,
                    timestamp: nonempty(&record["timestamp"]),
                    model: None,
                    tool_name: None,
                });
            }
        }
    }
    Some(make_transcript(
        input,
        SessionFields {
            native_id: nonempty(&metadata["id"])
                .or_else(|| nonempty(&metadata["session_id"]))
                .or_else(|| input.native_id.clone()),
            project_path: nonempty(&context["cwd"])
                .or_else(|| nonempty(&metadata["cwd"]))
                .or_else(|| input.project_path.clone()),
            model: nonempty(&context["model"]).or_else(|| nonempty(&metadata["model"])),
            title: nonempty(&metadata["thread_name"])
                .or_else(|| nonempty(&metadata["name"]))
                .or_else(|| input.title.clone()),
            source_kind: Some(
                match string(&metadata["source"]) {
                    "vscode" => "ide",
                    "appServer" => "desktop",
                    _ => "cli",
                }
                .into(),
            ),
            created_at: Some(date(&metadata["timestamp"], &input.modified_at)),
            updated_at: Some(date(
                records
                    .last()
                    .map(|record| &record["timestamp"])
                    .unwrap_or(&Value::Null),
                &input.modified_at,
            )),
            ..Default::default()
        },
        messages,
    ))
}

fn add_gemini_message(messages: &mut IndexMap<String, Value>, counter: &mut usize, value: &Value) {
    if !matches!(
        string(&value["type"]),
        "user" | "gemini" | "assistant" | "info" | "error" | "warning"
    ) {
        return;
    }
    let id = nonempty(&value["id"]).unwrap_or_else(|| {
        let id = format!("message-{counter}");
        *counter += 1;
        id
    });
    messages.insert(id, value.clone());
}

fn patch_gemini_message(messages: &mut IndexMap<String, Value>, update: &Value) {
    let Some(existing) = messages.get_mut(string(&update["id"])) else {
        return;
    };
    if let Some(content) = update.get("content") {
        existing["content"] = content.clone();
    }
    for tool_patch in list(&update["toolCalls"]) {
        if let Some(result) = tool_patch.get("result")
            && let Some(tools) = existing["toolCalls"].as_array_mut()
            && let Some(tool) = tools.iter_mut().find(|tool| tool["id"] == tool_patch["id"])
        {
            tool["result"] = result.clone();
        }
    }
}

pub fn parse_gemini(records: &[Value], input: &SessionInput) -> Option<Transcript> {
    let mut metadata = serde_json::Map::new();
    let mut messages = IndexMap::new();
    let mut counter = 0;
    for record in records {
        if record["sessionId"].is_string() {
            if let Some(record) = record.as_object() {
                metadata.extend(
                    record
                        .iter()
                        .filter(|(key, _)| key.as_str() != "messages")
                        .map(|(key, value)| (key.clone(), value.clone())),
                );
            }
            for message in list(&record["messages"]) {
                add_gemini_message(&mut messages, &mut counter, message);
            }
        } else if let Some(patch) = record["$set"].as_object() {
            if let Some(replacement) = patch.get("messages").and_then(Value::as_array) {
                messages.clear();
                for message in replacement {
                    add_gemini_message(&mut messages, &mut counter, message);
                }
            }
            metadata.extend(
                patch
                    .iter()
                    .filter(|(key, _)| key.as_str() != "messages")
                    .map(|(key, value)| (key.clone(), value.clone())),
            );
        } else if let Some(target) = record["$rewindTo"].as_str() {
            if let Some(index) = messages.get_index_of(target) {
                messages.truncate(index);
            } else {
                messages.clear();
            }
        } else if !record["$patch"].is_null() {
            let patch = &record["$patch"];
            patch_gemini_message(&mut messages, patch);
            for update in list(&patch["updates"]) {
                patch_gemini_message(&mut messages, update);
            }
            for id in list(&patch["removeIds"]) {
                messages.shift_remove(string(id));
            }
            if let Some(order) = patch["orderIds"].as_array() {
                let ordered: Vec<_> = order
                    .iter()
                    .filter_map(|id| messages.shift_remove_entry(string(id)))
                    .collect();
                messages.extend(ordered);
            }
        } else {
            add_gemini_message(&mut messages, &mut counter, record);
        }
    }
    let metadata = Value::Object(metadata);
    if string(&metadata["sessionId"]).is_empty() || metadata["kind"] == "subagent" {
        return None;
    }
    let mut parsed = Vec::new();
    for (id, message) in messages {
        let content = content_text(coalesce(&[&message["displayContent"], &message["content"]]));
        let role = match string(&message["type"]) {
            "user" => "user",
            "gemini" | "assistant" => "assistant",
            _ => "system",
        };
        if !content.is_empty() {
            parsed.push(SessionMessage {
                id: id.clone(),
                role: role.into(),
                content,
                timestamp: nonempty(&message["timestamp"]),
                model: nonempty(&message["model"]),
                tool_name: None,
            });
        }
        for (index, tool) in list(&message["toolCalls"]).iter().enumerate() {
            let result = content_text(&tool["result"]);
            let body = if result.is_empty() {
                tool.get("args")
                    .cloned()
                    .unwrap_or_else(|| serde_json::json!({}))
                    .to_string()
            } else {
                result
            };
            let name = nonempty(&tool["name"]).unwrap_or_else(|| "Tool".into());
            parsed.push(SessionMessage {
                id: nonempty(&tool["id"]).unwrap_or_else(|| format!("{id}-tool-{index}")),
                role: "tool".into(),
                content: head(&format!("{name}\n{body}"), MAX_CONTENT),
                timestamp: nonempty(&tool["timestamp"]),
                model: None,
                tool_name: nonempty(&tool["name"]),
            });
        }
    }
    Some(make_transcript(
        input,
        SessionFields {
            native_id: nonempty(&metadata["sessionId"]),
            project_path: nonempty(&metadata["cwd"]).or_else(|| input.project_path.clone()),
            title: nonempty(&metadata["summary"]),
            created_at: Some(date(&metadata["startTime"], &input.modified_at)),
            updated_at: Some(date(&metadata["lastUpdated"], &input.modified_at)),
            ..Default::default()
        },
        parsed,
    ))
}

pub fn parse_antigravity(records: &[Value], input: &SessionInput) -> Option<Transcript> {
    let mut messages: Vec<SessionMessage> = Vec::new();
    let mut native_id = input.native_id.clone();
    let mut project_path = input.project_path.clone();
    let mut title = input.title.clone();
    let mut model = None;
    for (index, row) in records.iter().enumerate() {
        let record = if row["step_update"]
            .as_object()
            .map(|value| !value.is_empty())
            .unwrap_or(false)
        {
            &row["step_update"]
        } else {
            row
        };
        let mut metadata = serde_json::Map::new();
        for value in [&row["metadata"], &row["init"], record] {
            if let Some(value) = value.as_object() {
                metadata.extend(value.clone());
            }
        }
        let metadata = Value::Object(metadata);
        native_id = nonempty(&metadata["conversation_id"])
            .or_else(|| nonempty(&metadata["conversationId"]))
            .or(native_id);
        project_path = nonempty(&metadata["cwd"])
            .or_else(|| list(&metadata["workspacePaths"]).first().and_then(nonempty))
            .or(project_path);
        title = nonempty(&metadata["conversation_title"])
            .or_else(|| nonempty(&metadata["title"]))
            .or(title);
        model = nonempty(&metadata["modelName"])
            .or_else(|| nonempty(&metadata["model"]))
            .or_else(|| nonempty(&metadata["model"]["id"]))
            .or(model);
        let kind = nonempty(&record["type"])
            .or_else(|| nonempty(&record["step_type"]))
            .or_else(|| nonempty(&record["role"]))
            .or_else(|| nonempty(&row["event"]))
            .unwrap_or_default()
            .to_ascii_lowercase();
        let nested = &record["message"];
        let role = nonempty(&nested["role"])
            .or_else(|| nonempty(&record["role"]))
            .unwrap_or_else(|| {
                if kind.contains("user_input") || kind.contains("user_message") || kind == "user" {
                    "user".into()
                } else if kind.contains("agent_response")
                    || kind.contains("assistant")
                    || kind.contains("model_response")
                    || kind == "gemini"
                {
                    "assistant".into()
                } else if kind.contains("tool") || kind.contains("command") {
                    "tool".into()
                } else {
                    String::new()
                }
            });
        if !matches!(role.as_str(), "user" | "assistant" | "system" | "tool") {
            continue;
        }
        let content = content_text(coalesce(&[
            &record["content"],
            &nested["content"],
            &record["text"],
            &record["text_delta"],
            &record["user_input"],
            &record["agent_response"],
            &record["result"],
            &record["message"],
        ]));
        if content.is_empty() {
            continue;
        }
        let step_id = record["step_index"]
            .as_i64()
            .map(|index| format!("step-{index}"));
        if let Some(existing) = step_id
            .as_ref()
            .and_then(|id| messages.iter_mut().find(|message| &message.id == id))
            .filter(|_| record["text_delta"].is_string())
        {
            existing.content = head(&format!("{}{content}", existing.content), MAX_CONTENT);
        } else {
            messages.push(SessionMessage {
                id: nonempty(&record["id"])
                    .or(step_id)
                    .unwrap_or_else(|| format!("message-{index}")),
                role,
                content,
                timestamp: nonempty(&record["timestamp"]).or_else(|| nonempty(&row["timestamp"])),
                model: model.clone(),
                tool_name: nonempty(&record["tool_name"]).or_else(|| nonempty(&record["toolName"])),
            });
        }
    }
    if native_id.as_deref().unwrap_or("").is_empty() && messages.is_empty() {
        return None;
    }
    let mut transcript = make_transcript(
        input,
        SessionFields {
            native_id,
            project_path,
            title,
            model,
            ..Default::default()
        },
        messages,
    );
    if transcript.messages.is_empty() {
        transcript.warnings.push("This Antigravity transcript has no recognized message records. Use the native CLI to inspect this conversation.".into());
    }
    Some(transcript)
}
