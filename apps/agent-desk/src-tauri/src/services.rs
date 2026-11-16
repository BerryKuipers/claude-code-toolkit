use crate::executables::{agent_label, detect_agents, resolve_executable};
use crate::launch_plan::{LaunchPlan, build_launch_plan, clean_environment};
use crate::secrets::SecretStore;
use crate::sessions::SessionService;
use crate::terminals::TerminalService;
use crate::types::*;
use crate::workspace::WorkspaceService;
use serde::Deserialize;
use serde::de::DeserializeOwned;
use serde_json::Value;
#[cfg(test)]
use serde_json::json;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct Services {
    pub workspace: WorkspaceService,
    pub sessions: Mutex<SessionService>,
    pub terminals: TerminalService,
    pub secrets: Arc<Mutex<SecretStore>>,
    pub home: PathBuf,
    installs: Mutex<Option<InstallCache>>,
}

struct InstallCache {
    commands: HashMap<String, String>,
    checked_at: Instant,
    agents: Vec<AgentInstall>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Edit {
    id: String,
    content: String,
    revision: String,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct CreateSkill {
    root_id: String,
    name: String,
    content: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SkillToggle {
    id: String,
    enabled: bool,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct SecretInput {
    profile_id: String,
    secret: String,
    persist: bool,
}

impl Services {
    pub fn new(home: PathBuf, data_dir: PathBuf) -> DeskResult<Self> {
        std::fs::create_dir_all(&data_dir).map_err(|e| e.to_string())?;
        let secrets = Arc::new(Mutex::new(SecretStore::new(&data_dir)?));
        Ok(Self {
            workspace: WorkspaceService::new(home.clone(), data_dir, secrets.clone())?,
            sessions: Mutex::new(SessionService::new(home.clone())),
            terminals: TerminalService::new(),
            secrets,
            home,
            installs: Mutex::new(None),
        })
    }

    pub fn dispatch(&self, method: &str, args: Vec<Value>) -> DeskResult<Value> {
        let count = match method {
            "bootstrap" | "skills" | "configs" | "terminals" | "proxyStart" => 0,
            "terminalWrite" => 2,
            "terminalResize" => 3,
            "sessions" if args.is_empty() => 0,
            "sessions" | "transcript" | "readSkill" | "saveSkill" | "createSkill"
            | "setSkillEnabled" | "saveConfig" | "saveSettings" | "saveProfile"
            | "deleteProfile" | "saveSecret" | "deleteSecret" | "models" | "probe" | "launch"
            | "terminalSnapshot" | "terminalClose" | "proxyAuthenticate" | "proxyMonitor" => 1,
            _ => return Err("Unknown desktop operation.".into()),
        };
        if args.len() != count {
            return Err("Invalid desktop request arguments.".into());
        }
        match method {
            "bootstrap" => self.bootstrap().and_then(serialize),
            "sessions" => {
                let refresh = if args.is_empty() {
                    false
                } else {
                    argument::<bool>(&args, 0)?
                };
                self.sessions
                    .lock()
                    .map_err(|e| e.to_string())?
                    .index(&self.workspace.settings(), refresh)
                    .and_then(serialize)
            }
            "transcript" => self.transcript(&identifier(&args, 0)?).and_then(serialize),
            "skills" => self.workspace.skills().and_then(serialize),
            "readSkill" => self
                .workspace
                .read_skill(&identifier(&args, 0)?)
                .and_then(serialize),
            "saveSkill" => {
                let input: Edit = argument(&args, 0)?;
                validate_edit(&input)?;
                self.workspace
                    .save_skill(&input.id, &input.content, &input.revision)
                    .and_then(serialize)
            }
            "createSkill" => {
                let input: CreateSkill = argument(&args, 0)?;
                text(&input.root_id, 512)?;
                text(&input.name, 120)?;
                text(&input.content, 2_000_000)?;
                self.workspace
                    .create_skill(&input.root_id, &input.name, &input.content)
                    .and_then(serialize)
            }
            "setSkillEnabled" => {
                let input: SkillToggle = argument(&args, 0)?;
                text(&input.id, 512)?;
                self.workspace.set_skill_enabled(&input.id, input.enabled)?;
                Ok(Value::Null)
            }
            "configs" => self.workspace.configs().and_then(serialize),
            "saveConfig" => {
                let input: Edit = argument(&args, 0)?;
                validate_edit(&input)?;
                self.workspace
                    .save_config(&input.id, &input.content, &input.revision)
                    .and_then(serialize)
            }
            "saveSettings" => self
                .workspace
                .save_settings(argument(&args, 0)?)
                .and_then(serialize),
            "saveProfile" => self
                .workspace
                .save_profile(argument(&args, 0)?)
                .and_then(serialize),
            "deleteProfile" => {
                let id = identifier(&args, 0)?;
                self.workspace.delete_profile(&id)?;
                self.secrets
                    .lock()
                    .map_err(|e| e.to_string())?
                    .delete(&id)?;
                Ok(Value::Null)
            }
            "saveSecret" => {
                let input: SecretInput = argument(&args, 0)?;
                text(&input.profile_id, 512)?;
                text(&input.secret, 16_384)?;
                if !self
                    .workspace
                    .profiles()?
                    .iter()
                    .any(|p| p.id == input.profile_id)
                {
                    return Err("Save the connection profile before adding its key.".into());
                }
                self.secrets.lock().map_err(|e| e.to_string())?.set(
                    &input.profile_id,
                    &input.secret,
                    input.persist,
                )?;
                Ok(Value::Null)
            }
            "deleteSecret" => {
                self.secrets
                    .lock()
                    .map_err(|e| e.to_string())?
                    .delete(&identifier(&args, 0)?)?;
                Ok(Value::Null)
            }
            "models" => self
                .workspace
                .models(&identifier(&args, 0)?)
                .and_then(serialize),
            "probe" => self
                .workspace
                .probe(&identifier(&args, 0)?)
                .and_then(serialize),
            "launch" => self.launch(argument(&args, 0)?).and_then(serialize),
            "terminals" => serialize(self.terminals.list()),
            "terminalSnapshot" => self
                .terminals
                .snapshot(&identifier(&args, 0)?)
                .and_then(serialize),
            "terminalWrite" => {
                self.terminals
                    .write(&identifier(&args, 0)?, &argument::<String>(&args, 1)?)?;
                Ok(Value::Null)
            }
            "terminalResize" => {
                self.terminals.resize(
                    &identifier(&args, 0)?,
                    argument(&args, 1)?,
                    argument(&args, 2)?,
                )?;
                Ok(Value::Null)
            }
            "terminalClose" => {
                self.terminals.close(&identifier(&args, 0)?)?;
                Ok(Value::Null)
            }
            "proxyStart" => self.proxy_start().and_then(serialize),
            "proxyAuthenticate" => self
                .proxy_authenticate(&identifier(&args, 0)?)
                .and_then(serialize),
            "proxyMonitor" => self.workspace.proxy_monitor(&identifier(&args, 0)?),
            _ => Err("Unknown desktop operation.".into()),
        }
    }

    pub fn bootstrap(&self) -> DeskResult<Bootstrap> {
        let settings = self.workspace.settings();
        let agents = {
            let mut cache = self.installs.lock().map_err(|e| e.to_string())?;
            if !cache.as_ref().is_some_and(|cache| {
                cache.commands == settings.agent_commands
                    && cache.checked_at.elapsed() < Duration::from_secs(60)
            }) {
                *cache = Some(InstallCache {
                    commands: settings.agent_commands.clone(),
                    checked_at: Instant::now(),
                    agents: detect_agents(&settings, &self.home),
                });
            }
            cache.as_ref().unwrap().agents.clone()
        };
        let profiles = self.workspace.profiles()?;
        let secrets = self.secrets.lock().map_err(|e| e.to_string())?;
        Ok(Bootstrap {
            settings,
            profiles,
            agents,
            skill_roots: self.workspace.skill_roots()?,
            app_version: env!("CARGO_PKG_VERSION").into(),
            platform: if cfg!(windows) {
                "win32"
            } else if cfg!(target_os = "macos") {
                "darwin"
            } else {
                "linux"
            }
            .into(),
            home: self.home.to_string_lossy().into_owned(),
            secure_storage_available: secrets.available(),
            warnings: secrets.warnings(),
        })
    }

    pub fn transcript(&self, id: &str) -> DeskResult<Transcript> {
        self.sessions
            .lock()
            .map_err(|e| e.to_string())?
            .transcript(&self.workspace.settings(), id)
    }

    pub fn launch(&self, request: LaunchRequest) -> DeskResult<TerminalInfo> {
        text(&request.project_path, 32_768)?;
        for id in [&request.profile_id, &request.session_id]
            .into_iter()
            .flatten()
        {
            text(id, 512)?;
            if id.is_empty() {
                return Err("An identifier is required.".into());
            }
        }
        let settings = self.workspace.settings();
        let profile_id = request
            .profile_id
            .as_deref()
            .unwrap_or(&settings.default_profile_id);
        let profile = self
            .workspace
            .profiles()?
            .into_iter()
            .find(|p| p.id == profile_id)
            .ok_or("Choose an existing connection profile.")?;
        let session = if let Some(id) = &request.session_id {
            self.sessions
                .lock()
                .map_err(|e| e.to_string())?
                .index(&settings, false)?
                .sessions
                .into_iter()
                .find(|s| &s.id == id)
        } else {
            None
        };
        let key = self
            .secrets
            .lock()
            .map_err(|e| e.to_string())?
            .get(&profile.id)?;
        let plan = build_launch_plan(
            &request,
            &profile,
            &std::env::vars().collect(),
            key.as_deref(),
            session.as_ref(),
        )?;
        if !Path::new(&plan.cwd).is_absolute() || !Path::new(&plan.cwd).is_dir() {
            return Err("Choose an existing absolute project folder.".into());
        }
        if let Some(path) = profile.settings_file.as_ref().filter(|s| !s.is_empty())
            && (!Path::new(path).is_absolute() || !Path::new(path).is_file())
        {
            return Err("The additional settings file must use an existing absolute path.".into());
        }
        let command = settings
            .agent_commands
            .get(&request.agent)
            .ok_or("Unknown agent command.")?;
        let executable = resolve_executable(command, &plan.env, &self.home)?;
        if !settings.projects.contains(&plan.cwd) {
            let mut next = settings.clone();
            next.projects.push(plan.cwd.clone());
            if next.projects.len() > 100 {
                next.projects.remove(0);
            }
            self.workspace.save_settings(next)?;
        }
        self.terminals.launch(
            &executable,
            &plan,
            TerminalInfo {
                agent: request.agent.clone(),
                title: session
                    .as_ref()
                    .map(|s| s.title.clone())
                    .unwrap_or_else(|| {
                        format!("{} · {}", agent_label(&request.agent), profile.name)
                    }),
                profile_id: Some(profile.id),
                session_id: session.map(|s| s.id),
                ..Default::default()
            },
        )
    }

    fn proxy_start(&self) -> DeskResult<TerminalInfo> {
        if let Some(active) = self
            .terminals
            .list()
            .into_iter()
            .find(|item| item.agent == "proxy" && item.status == "running")
        {
            return Ok(active);
        }
        self.proxy_command(
            vec!["serve".into(), "--no-monitor".into()],
            "Local model proxy".into(),
        )
    }

    fn proxy_authenticate(&self, provider: &str) -> DeskResult<TerminalInfo> {
        if !matches!(provider, "codex" | "kimi" | "grok" | "cursor") {
            return Err("Unsupported proxy authentication provider.".into());
        }
        self.proxy_command(
            vec![
                provider.into(),
                "auth".into(),
                if provider == "grok" {
                    "device"
                } else {
                    "login"
                }
                .into(),
            ],
            format!("Proxy · {provider} sign-in"),
        )
    }

    fn proxy_command(&self, args: Vec<String>, title: String) -> DeskResult<TerminalInfo> {
        let env = clean_environment(&std::env::vars().collect());
        let executable =
            resolve_executable(&self.workspace.settings().proxy_command, &env, &self.home)?;
        self.terminals.launch(
            &executable,
            &LaunchPlan {
                args,
                env,
                cwd: self.home.to_string_lossy().into_owned(),
            },
            TerminalInfo {
                agent: "proxy".into(),
                title,
                ..Default::default()
            },
        )
    }

    pub fn close(&self) {
        self.terminals.dispose();
        if let Ok(mut sessions) = self.sessions.lock() {
            sessions.close();
        }
    }
}

pub fn argument<T: DeserializeOwned>(args: &[Value], index: usize) -> DeskResult<T> {
    serde_json::from_value(
        args.get(index)
            .cloned()
            .ok_or("Missing desktop request argument.")?,
    )
    .map_err(|e| format!("Invalid desktop request: {e}"))
}

pub fn identifier(args: &[Value], index: usize) -> DeskResult<String> {
    let value: String = argument(args, index)?;
    text(&value, 512)?;
    if value.is_empty() {
        return Err("An identifier is required.".into());
    }
    Ok(value)
}

pub fn text(value: &str, max: usize) -> DeskResult<()> {
    if value.len() > max || value.contains('\0') {
        return Err("Text is too large or contains an invalid character.".into());
    }
    Ok(())
}

fn validate_edit(edit: &Edit) -> DeskResult<()> {
    text(&edit.id, 512)?;
    text(&edit.revision, 512)?;
    text(&edit.content, 2_000_000)
}
fn serialize<T: serde::Serialize>(value: T) -> DeskResult<Value> {
    serde_json::to_value(value).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dispatch_rejects_unknown_commands_extra_arguments_and_unowned_paths() {
        let root = tempfile::tempdir().unwrap();
        let services = Services::new(root.path().join("home"), root.path().join("data")).unwrap();
        assert!(
            services
                .dispatch("executeShell", vec![json!("bad")])
                .is_err()
        );
        assert!(services.dispatch("terminals", vec![json!(1)]).is_err());
        assert!(services.dispatch("sessions", vec![json!("true")]).is_err());
        assert!(services.dispatch("sessions", vec![Value::Null]).is_err());
        for id in [String::new(), "a".repeat(513), "invalid\0id".into()] {
            let mut request = LaunchRequest {
                agent: "claude".into(),
                project_path: root.path().to_string_lossy().into_owned(),
                profile_id: Some(id.clone()),
                ..Default::default()
            };
            assert!(services.launch(request.clone()).is_err());
            request.profile_id = None;
            request.session_id = Some(id);
            assert!(services.launch(request).is_err());
        }
        assert!(
            services
                .dispatch("readSkill", vec![json!("/etc/passwd")])
                .is_err()
        );
        assert!(
            services
                .dispatch("terminalResize", vec![json!("id"), json!(90.5), json!(40)])
                .is_err()
        );
        assert!(
            services
                .dispatch(
                    "saveSecret",
                    vec![json!({"profileId":"missing", "secret":"test", "persist":false})]
                )
                .is_err()
        );
    }
}
