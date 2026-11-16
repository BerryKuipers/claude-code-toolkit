use crate::file_store::{
    AgentHomes, TEXT_LIMIT, absolute, agent_homes, approved_anchor, atomic_write, canonical_within,
    display_path, ensure_configured_root, ensure_directory_within, inside, optional_text, path_key,
    read_json, revision, same_path, set_private_directory, stable_id, write_revision,
};
use crate::providers::{ProviderService, default_profiles, validate_profile};
use crate::secrets::SecretStore;
use crate::skills::SkillService;
use crate::types::*;
use serde::Serialize;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, RwLock};

const AGENTS: [&str; 4] = ["claude", "codex", "gemini", "antigravity"];

pub fn default_settings() -> AppSettings {
    AppSettings {
        theme: "system".into(),
        font_size: 13,
        terminal_scrollback: 10_000,
        default_profile_id: "claude-native".into(),
        projects: Vec::new(),
        history_roots: Vec::new(),
        skill_directories: Vec::new(),
        agent_commands: [
            ("claude".into(), "claude".into()),
            ("codex".into(), "codex".into()),
            ("gemini".into(), "gemini".into()),
            ("antigravity".into(), "agy".into()),
        ]
        .into(),
        proxy_command: "claude-code-proxy".into(),
        scan_on_start: true,
        auto_refresh_seconds: 30,
    }
}

fn directory(value: &str) -> DeskResult<()> {
    if value.is_empty()
        || value.len() > 4096
        || value.contains('\0')
        || !Path::new(value).is_absolute()
    {
        return Err("Choose an absolute directory path of at most 4096 characters.".into());
    }
    Ok(())
}

fn command(value: &mut String) -> DeskResult<()> {
    *value = value.trim().to_owned();
    if value.is_empty() || value.len() > 4096 || value.contains(['\0', '\r', '\n']) {
        return Err("A command must be a single executable name or path.".into());
    }
    Ok(())
}

fn validate_settings(mut settings: AppSettings) -> DeskResult<AppSettings> {
    if !["system", "light", "dark"].contains(&settings.theme.as_str()) {
        return Err("Choose a supported appearance theme.".into());
    }
    if !(10..=26).contains(&settings.font_size) {
        return Err("The font size must be between 10 and 26.".into());
    }
    if !(1000..=100_000).contains(&settings.terminal_scrollback) {
        return Err("Terminal scrollback must be between 1000 and 100000 lines.".into());
    }
    if settings.default_profile_id.len() > 80 || settings.default_profile_id.contains('\0') {
        return Err("Invalid default profile identifier.".into());
    }
    if settings.projects.len() > 100
        || settings.history_roots.len() > 60
        || settings.skill_directories.len() > 50
    {
        return Err("Too many registered projects, history roots, or skill directories.".into());
    }
    if settings.auto_refresh_seconds > 3600
        || (settings.auto_refresh_seconds != 0 && settings.auto_refresh_seconds < 10)
    {
        return Err("Automatic refresh must be off or between 10 and 3600 seconds.".into());
    }
    for value in settings.projects.iter().chain(&settings.skill_directories) {
        directory(value)?;
    }
    let mut history_ids = HashSet::new();
    for root in &mut settings.history_roots {
        if root.id.is_empty()
            || root.id.len() > 100
            || root.id.contains('\0')
            || !AGENTS.contains(&root.agent.as_str())
        {
            return Err("Invalid history root identifier or agent.".into());
        }
        if !history_ids.insert(root.id.clone()) {
            return Err("History root IDs must be unique.".into());
        }
        directory(&root.path)?;
        root.path = display_path(&absolute(Path::new(&root.path)));
    }
    if settings.agent_commands.len() != AGENTS.len() {
        return Err("Set one executable for each coding agent.".into());
    }
    for agent in AGENTS {
        command(
            settings
                .agent_commands
                .get_mut(agent)
                .ok_or("Set one executable for each coding agent.")?,
        )?;
    }
    command(&mut settings.proxy_command)?;
    for directories in [&mut settings.projects, &mut settings.skill_directories] {
        let mut seen = HashSet::new();
        *directories = directories
            .iter()
            .map(|value| absolute(Path::new(value)))
            .filter(|path| seen.insert(path_key(path)))
            .map(|path| display_path(&path))
            .collect();
    }
    Ok(settings)
}

fn persisted_settings(path: &Path) -> DeskResult<AppSettings> {
    let saved: Value = read_json(path, json!({}))?;
    let object = saved
        .as_object()
        .ok_or("Settings storage is invalid. Existing files were left intact.")?;
    let mut merged = serde_json::to_value(default_settings()).map_err(|error| error.to_string())?;
    let defaults = merged.as_object_mut().unwrap();
    for (key, value) in object {
        if key == "agentCommands" {
            let commands = value
                .as_object()
                .ok_or("The stored agent commands are invalid.")?;
            let existing = defaults.get_mut(key).unwrap().as_object_mut().unwrap();
            for agent in AGENTS {
                if let Some(command) = commands.get(agent) {
                    existing.insert(agent.into(), command.clone());
                }
            }
        } else if defaults.contains_key(key) {
            defaults.insert(key.clone(), value.clone());
        }
    }
    let settings = serde_json::from_value(merged)
        .map_err(|_| "Settings storage is invalid. Existing files were left intact.")?;
    validate_settings(settings)
}

fn json_text(value: &impl Serialize) -> DeskResult<String> {
    serde_json::to_string_pretty(value)
        .map(|value| format!("{value}\n"))
        .map_err(|error| error.to_string())
}

struct WorkspaceState {
    settings: AppSettings,
    profiles: Vec<ProviderProfile>,
}

struct ConfigSpec {
    document: ConfigDocument,
    root: PathBuf,
}

pub struct WorkspaceService {
    home: PathBuf,
    data_dir: PathBuf,
    homes: AgentHomes,
    state: RwLock<WorkspaceState>,
    writes: Mutex<()>,
    secrets: Arc<Mutex<SecretStore>>,
    providers: ProviderService,
    skill_service: SkillService,
}

impl WorkspaceService {
    pub fn new(
        home: PathBuf,
        data_dir: PathBuf,
        secrets: Arc<Mutex<SecretStore>>,
    ) -> DeskResult<Self> {
        let homes = agent_homes(&home);
        Self::new_with_homes(home, data_dir, secrets, homes)
    }

    pub(crate) fn new_with_homes(
        home: PathBuf,
        data_dir: PathBuf,
        secrets: Arc<Mutex<SecretStore>>,
        homes: AgentHomes,
    ) -> DeskResult<Self> {
        fs::create_dir_all(&data_dir).map_err(|error| error.to_string())?;
        set_private_directory(&data_dir)?;
        let mut settings = persisted_settings(&data_dir.join("settings.json"))?;
        let profiles: Vec<ProviderProfile> =
            read_json(&data_dir.join("profiles.json"), default_profiles())?;
        if profiles.len() > 200 {
            return Err("Profile storage is invalid. Existing files were left intact.".into());
        }
        let profiles: Vec<_> = profiles
            .into_iter()
            .map(validate_profile)
            .collect::<DeskResult<_>>()?;
        if profiles
            .iter()
            .map(|profile| &profile.id)
            .collect::<HashSet<_>>()
            .len()
            != profiles.len()
        {
            return Err("Profile storage contains duplicate IDs.".into());
        }
        if !profiles
            .iter()
            .any(|profile| profile.id == settings.default_profile_id)
        {
            settings.default_profile_id = profiles
                .first()
                .map(|profile| profile.id.clone())
                .unwrap_or_default();
        }
        let providers = ProviderService::new(secrets.clone())?;
        let skill_service = SkillService::new(home.clone(), data_dir.clone(), homes.clone());
        Ok(Self {
            home,
            data_dir,
            homes,
            state: RwLock::new(WorkspaceState { settings, profiles }),
            writes: Mutex::new(()),
            secrets,
            providers,
            skill_service,
        })
    }

    pub fn settings(&self) -> AppSettings {
        self.state
            .read()
            .unwrap_or_else(std::sync::PoisonError::into_inner)
            .settings
            .clone()
    }

    fn with_secret_status(&self, mut profile: ProviderProfile) -> DeskResult<ProviderProfile> {
        profile.has_secret = Some(
            self.secrets
                .lock()
                .map_err(|_| "The credential store is unavailable.")?
                .has(&profile.id)
                || profile
                    .api_key_env
                    .as_ref()
                    .and_then(|name| std::env::var(name).ok())
                    .is_some_and(|value| !value.is_empty()),
        );
        Ok(profile)
    }

    pub fn profiles(&self) -> DeskResult<Vec<ProviderProfile>> {
        let profiles = self
            .state
            .read()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles
            .clone();
        profiles
            .into_iter()
            .map(|profile| self.with_secret_status(profile))
            .collect()
    }

    pub fn get_profile(&self, id: &str) -> DeskResult<ProviderProfile> {
        self.state
            .read()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles
            .iter()
            .find(|profile| profile.id == id)
            .cloned()
            .ok_or_else(|| "Profile does not exist.".into())
    }

    pub fn save_settings(&self, settings: AppSettings) -> DeskResult<AppSettings> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The workspace write lock is unavailable.")?;
        let settings = validate_settings(settings)?;
        self.get_profile(&settings.default_profile_id)
            .map_err(|_| "Choose an existing default profile.")?;
        atomic_write(&self.data_dir.join("settings.json"), &json_text(&settings)?)?;
        self.state
            .write()
            .map_err(|_| "The workspace state is unavailable.")?
            .settings = settings.clone();
        Ok(settings)
    }

    pub fn save_profile(&self, profile: ProviderProfile) -> DeskResult<ProviderProfile> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The workspace write lock is unavailable.")?;
        let profile = validate_profile(profile)?;
        let mut profiles = self
            .state
            .read()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles
            .clone();
        if let Some(index) = profiles.iter().position(|item| item.id == profile.id) {
            profiles[index] = profile.clone();
        } else {
            if profiles.len() >= 200 {
                return Err("The profile limit has been reached.".into());
            }
            profiles.push(profile.clone());
        }
        atomic_write(&self.data_dir.join("profiles.json"), &json_text(&profiles)?)?;
        self.state
            .write()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles = profiles;
        self.with_secret_status(profile)
    }

    pub fn delete_profile(&self, id: &str) -> DeskResult<()> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The workspace write lock is unavailable.")?;
        let (mut profiles, mut settings) = {
            let state = self
                .state
                .read()
                .map_err(|_| "The workspace state is unavailable.")?;
            (state.profiles.clone(), state.settings.clone())
        };
        if !profiles.iter().any(|profile| profile.id == id) {
            return Err("Profile does not exist.".into());
        }
        if profiles.len() == 1 {
            return Err("Keep at least one launch profile.".into());
        }
        profiles.retain(|profile| profile.id != id);
        if settings.default_profile_id == id {
            settings.default_profile_id = profiles[0].id.clone();
            atomic_write(&self.data_dir.join("settings.json"), &json_text(&settings)?)?;
            self.state
                .write()
                .map_err(|_| "The workspace state is unavailable.")?
                .settings = settings;
        }
        atomic_write(&self.data_dir.join("profiles.json"), &json_text(&profiles)?)?;
        self.state
            .write()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles = profiles;
        Ok(())
    }

    pub fn skill_roots(&self) -> DeskResult<Vec<SkillRoot>> {
        Ok(self.skill_service.roots(&self.settings()))
    }
    pub fn skills(&self) -> DeskResult<SkillIndex> {
        self.skill_service.list(&self.settings())
    }
    pub fn read_skill(&self, id: &str) -> DeskResult<SkillDocument> {
        self.skill_service.read(id, &self.settings())
    }
    pub fn save_skill(&self, id: &str, content: &str, revision: &str) -> DeskResult<SkillDocument> {
        self.skill_service
            .save(id, content, revision, &self.settings())
    }
    pub fn create_skill(
        &self,
        root_id: &str,
        name: &str,
        content: &str,
    ) -> DeskResult<SkillDocument> {
        self.skill_service
            .create(root_id, name, content, &self.settings())
    }
    pub fn set_skill_enabled(&self, id: &str, enabled: bool) -> DeskResult<()> {
        self.skill_service
            .set_enabled(id, enabled, &self.settings())
    }
    pub fn models(&self, profile_id: &str) -> DeskResult<ModelCatalog> {
        self.providers.models(&self.get_profile(profile_id)?)
    }
    pub fn probe(&self, profile_id: &str) -> DeskResult<ProviderStatus> {
        Ok(self.providers.probe(&self.get_profile(profile_id)?))
    }
    pub fn proxy_monitor(&self, profile_id: &str) -> DeskResult<Value> {
        self.providers.proxy_monitor(&self.get_profile(profile_id)?)
    }

    fn config_specs(&self, settings: &AppSettings) -> DeskResult<Vec<ConfigSpec>> {
        let mut specs = Vec::new();
        let mut push = |agent: &str, label: String, path: PathBuf, root: PathBuf, format: &str| {
            let path = display_path(&absolute(&path));
            specs.push(ConfigSpec {
                document: ConfigDocument {
                    id: stable_id("config", &path),
                    agent: agent.into(),
                    label,
                    path,
                    format: format.into(),
                    ..Default::default()
                },
                root,
            });
        };
        for (agent, label, root, name, format) in [
            (
                "claude",
                "Claude Code settings",
                &self.homes.claude,
                "settings.json",
                "json",
            ),
            (
                "claude",
                "Claude Code keybindings",
                &self.homes.claude,
                "keybindings.json",
                "json",
            ),
            (
                "claude",
                "Claude Code instructions",
                &self.homes.claude,
                "CLAUDE.md",
                "markdown",
            ),
            (
                "codex",
                "Codex settings",
                &self.homes.codex,
                "config.toml",
                "toml",
            ),
            (
                "codex",
                "Codex instructions",
                &self.homes.codex,
                "AGENTS.md",
                "markdown",
            ),
            (
                "gemini",
                "Gemini settings",
                &self.homes.gemini,
                "settings.json",
                "json",
            ),
            (
                "gemini",
                "Gemini instructions",
                &self.homes.gemini,
                "GEMINI.md",
                "markdown",
            ),
        ] {
            push(agent, label.into(), root.join(name), root.clone(), format);
        }
        let antigravity = self.home.join(".gemini/antigravity-cli");
        push(
            "antigravity",
            "Antigravity CLI settings".into(),
            antigravity.join("settings.json"),
            antigravity.clone(),
            "json",
        );
        push(
            "antigravity",
            "Antigravity CLI keybindings".into(),
            antigravity.join("keybindings.json"),
            antigravity,
            "json",
        );
        for project in &settings.projects {
            let project = PathBuf::from(project);
            let name = project.file_name().unwrap_or_default().to_string_lossy();
            for (agent, label, file, format) in [
                ("claude", "Claude settings", ".claude/settings.json", "json"),
                (
                    "claude",
                    "local Claude settings",
                    ".claude/settings.local.json",
                    "json",
                ),
                ("claude", "Claude instructions", "CLAUDE.md", "markdown"),
                ("codex", "agent instructions", "AGENTS.md", "markdown"),
                ("codex", "Codex settings", ".codex/config.toml", "toml"),
                ("gemini", "Gemini settings", ".gemini/settings.json", "json"),
            ] {
                push(
                    agent,
                    format!("{name} · {label}"),
                    project.join(file),
                    project.clone(),
                    format,
                );
            }
        }
        let profile_root = self.homes.claude.join("profiles");
        let allowed: Vec<_> = std::iter::once(profile_root.clone())
            .chain(settings.projects.iter().map(PathBuf::from))
            .collect();
        for profile in &self
            .state
            .read()
            .map_err(|_| "The workspace state is unavailable.")?
            .profiles
        {
            if let Some(file) = &profile.settings_file {
                let path = Path::new(file);
                if path.is_absolute()
                    && path
                        .extension()
                        .is_some_and(|extension| extension == "json")
                    && let Some(root) = allowed.iter().find(|root| inside(root, path))
                {
                    push(
                        &profile.agent,
                        format!("{} · settings overlay", profile.name),
                        path.into(),
                        root.clone(),
                        "json",
                    );
                }
            }
        }
        match fs::read_dir(&profile_root) {
            Ok(entries) => {
                for entry in entries.take(100) {
                    let entry = entry.map_err(
                        |_| "Could not list Claude profile overlays. Check directory permissions.",
                    )?;
                    if !entry.file_type().is_ok_and(|kind| kind.is_file())
                        || entry
                            .path()
                            .extension()
                            .is_none_or(|extension| extension != "json")
                    {
                        continue;
                    }
                    let filename = entry.file_name().to_string_lossy().into_owned();
                    let name = filename
                        .strip_suffix(".settings.json")
                        .or_else(|| filename.strip_suffix(".json"))
                        .unwrap_or(&filename);
                    push(
                        "claude",
                        format!("Claude profile · {name}"),
                        entry.path(),
                        profile_root.clone(),
                        "json",
                    );
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(_) => {
                return Err(
                    "Could not list Claude profile overlays. Check directory permissions.".into(),
                );
            }
        }
        let mut positions = HashMap::new();
        let mut unique = Vec::new();
        for spec in specs {
            let key = path_key(Path::new(&spec.document.path));
            if let Some(index) = positions.get(&key) {
                unique[*index] = spec;
            } else {
                positions.insert(key, unique.len());
                unique.push(spec);
            }
        }
        Ok(unique)
    }

    pub fn configs(&self) -> DeskResult<Vec<ConfigDocument>> {
        let settings = self.settings();
        self.config_specs(&settings)?
            .into_iter()
            .map(|spec| {
                let content = (|| -> DeskResult<Option<String>> {
                    let file = Path::new(&spec.document.path);
                    match fs::symlink_metadata(file) {
                        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                            return Ok(None);
                        }
                        Err(error) => return Err(error.to_string()),
                        Ok(_) => {}
                    }
                    let anchor = approved_anchor(
                        file,
                        &self.home,
                        &settings.projects,
                        &self.homes.configured,
                    )?;
                    let canonical_anchor =
                        fs::canonicalize(anchor).map_err(|error| error.to_string())?;
                    let root = fs::canonicalize(&spec.root).map_err(|error| error.to_string())?;
                    if !inside(&canonical_anchor, &root) {
                        return Err(
                            "Configuration directory points outside its home or project.".into(),
                        );
                    }
                    let canonical = canonical_within(file, &[root], false)?;
                    optional_text(&canonical)
                })()
                .map_err(|error| format!("Cannot read {}: {error}", spec.document.label))?;
                Ok(ConfigDocument {
                    exists: content.is_some(),
                    revision: revision(content.as_deref()),
                    content: content.unwrap_or_default(),
                    ..spec.document
                })
            })
            .collect()
    }

    pub fn save_config(
        &self,
        id: &str,
        content: &str,
        expected_revision: &str,
    ) -> DeskResult<ConfigDocument> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The workspace write lock is unavailable.")?;
        let settings = self.settings();
        let spec = self
            .config_specs(&settings)?
            .into_iter()
            .find(|spec| spec.document.id == id)
            .ok_or("This configuration file is not in the approved workspace.")?;
        if content.len() > TEXT_LIMIT || content.contains('\0') {
            return Err("Configuration must be text within the editor size limit.".into());
        }
        if spec.document.format == "json" {
            let value: Value = serde_json::from_str(content)
                .map_err(|_| "The configuration is not valid JSON.")?;
            if !value.is_object()
                && !(value.is_array() && spec.document.path.ends_with("keybindings.json"))
            {
                return Err("Settings must be a JSON object.".into());
            }
        } else if spec.document.format == "toml" {
            toml::from_str::<toml::Value>(content)
                .map_err(|_| "The configuration is not valid TOML.")?;
        }
        let file = Path::new(&spec.document.path);
        let anchor = approved_anchor(file, &self.home, &settings.projects, &self.homes.configured)?;
        if self
            .homes
            .configured
            .iter()
            .any(|root| same_path(root, &anchor))
        {
            ensure_configured_root(&anchor)?;
        }
        let canonical_root = ensure_directory_within(&spec.root, &anchor)?;
        ensure_directory_within(
            file.parent()
                .ok_or("The configuration has no parent directory.")?,
            &anchor,
        )?;
        let revision = write_revision(
            file,
            content,
            expected_revision,
            &[canonical_root],
            &self.data_dir.join("backups/configs"),
        )?;
        Ok(ConfigDocument {
            exists: true,
            content: content.into(),
            revision,
            ..spec.document
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::file_store::agent_homes_with;
    use std::sync::Barrier;

    fn fixture() -> (tempfile::TempDir, WorkspaceService) {
        let root = tempfile::tempdir().unwrap();
        let home = root.path().join("home");
        fs::create_dir(&home).unwrap();
        let data = root.path().join("data");
        let secrets = Arc::new(Mutex::new(SecretStore::memory_only(&data).unwrap()));
        let homes = agent_homes_with(&home, |_| None);
        let service = WorkspaceService::new_with_homes(home, data, secrets, homes).unwrap();
        (root, service)
    }

    fn config(service: &WorkspaceService, label: &str) -> ConfigDocument {
        service
            .configs()
            .unwrap()
            .into_iter()
            .find(|item| item.label == label)
            .unwrap()
    }

    #[test]
    fn existing_settings_and_profiles_survive_reopening_without_persisted_credentials() {
        let (directory, service) = fixture();
        let mut profile = service.get_profile("claude-native").unwrap();
        profile.id = "personal".into();
        profile.name = "My configuration".into();
        profile.model = Some("chosen-model".into());
        service.save_profile(profile).unwrap();
        service
            .secrets
            .lock()
            .unwrap()
            .set("personal", "fixture-key", false)
            .unwrap();
        let mut settings = service.settings();
        settings.theme = "dark".into();
        settings.default_profile_id = "personal".into();
        service.save_settings(settings).unwrap();
        let persisted = fs::read_to_string(directory.path().join("data/profiles.json")).unwrap();
        assert!(!persisted.contains("fixture-key") && !persisted.contains("hasSecret"));
        assert!(
            service
                .profiles()
                .unwrap()
                .into_iter()
                .find(|profile| profile.id == "personal")
                .unwrap()
                .has_secret
                .unwrap()
        );
        let reopened = WorkspaceService::new_with_homes(
            service.home.clone(),
            service.data_dir.clone(),
            service.secrets.clone(),
            service.homes.clone(),
        )
        .unwrap();
        assert_eq!(reopened.settings().theme, "dark");
        assert_eq!(reopened.settings().default_profile_id, "personal");
        assert_eq!(
            reopened.get_profile("personal").unwrap().model.as_deref(),
            Some("chosen-model")
        );
        reopened.delete_profile("personal").unwrap();
        assert_eq!(reopened.settings().default_profile_id, "claude-native");
    }

    #[test]
    fn partial_legacy_settings_merge_defaults_and_corrupt_storage_is_not_replaced() {
        let (directory, service) = fixture();
        let path = directory.path().join("data/settings.json");
        fs::write(
            &path,
            r#"{"theme":"light","agentCommands":{"claude":"custom-claude"},"oldField":true}"#,
        )
        .unwrap();
        let reopened = WorkspaceService::new_with_homes(
            service.home.clone(),
            service.data_dir.clone(),
            service.secrets.clone(),
            service.homes.clone(),
        )
        .unwrap();
        assert_eq!(
            reopened.settings().agent_commands["claude"],
            "custom-claude"
        );
        assert_eq!(reopened.settings().agent_commands["codex"], "codex");
        fs::write(&path, "not-json").unwrap();
        assert!(
            WorkspaceService::new_with_homes(
                service.home.clone(),
                service.data_dir.clone(),
                service.secrets.clone(),
                service.homes.clone()
            )
            .is_err()
        );
        assert_eq!(fs::read_to_string(path).unwrap(), "not-json");
    }

    #[test]
    fn concurrent_profile_updates_are_serialized_without_losing_either_change() {
        let (_directory, service) = fixture();
        let service = Arc::new(service);
        let barrier = Arc::new(Barrier::new(2));
        let jobs: Vec<_> = ["first", "second"]
            .into_iter()
            .map(|id| {
                let service = service.clone();
                let barrier = barrier.clone();
                std::thread::spawn(move || {
                    let mut profile = service.get_profile("claude-native").unwrap();
                    profile.id = id.into();
                    barrier.wait();
                    service.save_profile(profile).unwrap();
                })
            })
            .collect();
        for job in jobs {
            job.join().unwrap();
        }
        assert!(service.get_profile("first").is_ok() && service.get_profile("second").is_ok());
        let persisted: Vec<ProviderProfile> =
            read_json(&service.data_dir.join("profiles.json"), Vec::new()).unwrap();
        assert_eq!(persisted.len(), 9);
    }

    #[test]
    fn native_configuration_edits_preserve_raw_content_backups_and_revision_conflicts() {
        let (_directory, service) = fixture();
        let selected = config(&service, "Claude Code settings");
        assert!(!selected.exists);
        let original = "{\n  \"customPluginField\": {\"enabled\":true},\n  \"model\": \"old\"\n}\n";
        let first = service
            .save_config(&selected.id, original, &selected.revision)
            .unwrap();
        let changed = original.replace("\"old\"", "\"new\"");
        let saved = service
            .save_config(&selected.id, &changed, &first.revision)
            .unwrap();
        assert_eq!(fs::read_to_string(&selected.path).unwrap(), changed);
        assert_eq!(saved.content, changed);
        let backup = fs::read_dir(service.data_dir.join("backups/configs"))
            .unwrap()
            .next()
            .unwrap()
            .unwrap()
            .path();
        assert_eq!(fs::read_to_string(backup).unwrap(), original);
        assert!(
            service
                .save_config(&selected.id, original, &first.revision)
                .unwrap_err()
                .contains("changed outside")
        );
        assert!(
            service
                .save_config(&selected.id, "[]", &saved.revision)
                .is_err()
        );
        assert!(
            service
                .save_config(&selected.id, "{broken", &saved.revision)
                .is_err()
        );
        let keybindings = config(&service, "Claude Code keybindings");
        service
            .save_config(&keybindings.id, "[]", &keybindings.revision)
            .unwrap();
        let codex = config(&service, "Codex settings");
        assert!(
            service
                .save_config(&codex.id, "model = [\"broken", &codex.revision)
                .is_err()
        );
        service
            .save_config(
                &codex.id,
                "model = \"chosen\"\n[custom]\nenabled = true\n",
                &codex.revision,
            )
            .unwrap();
    }

    #[test]
    fn explicit_agent_homes_outside_home_are_used_for_configs_and_skill_creation() {
        let (directory, service) = fixture();
        let external = directory.path().join("external");
        let homes = agent_homes_with(&service.home, |name| match name {
            "CLAUDE_CONFIG_DIR" => Some(display_path(&external.join("claude"))),
            "CODEX_HOME" => Some(display_path(&external.join("codex"))),
            "GEMINI_CLI_HOME" => Some(display_path(&external.join("google"))),
            _ => None,
        });
        let service = WorkspaceService::new_with_homes(
            service.home.clone(),
            service.data_dir.clone(),
            service.secrets.clone(),
            homes,
        )
        .unwrap();
        for label in ["Claude Code settings", "Codex settings", "Gemini settings"] {
            let document = config(&service, label);
            assert!(inside(&external, Path::new(&document.path)));
            let content = if document.format == "toml" {
                "model = \"fixture\"\n"
            } else {
                "{\"custom\":true}"
            };
            service
                .save_config(&document.id, content, &document.revision)
                .unwrap();
            assert_eq!(fs::read_to_string(document.path).unwrap(), content);
        }
        for agent in ["claude", "codex", "gemini"] {
            let root = service
                .skill_roots()
                .unwrap()
                .into_iter()
                .find(|root| root.agent == agent && root.scope == "user")
                .unwrap();
            let created = service
                .create_skill(&root.id, "fixture", "# Fixture\nDo the work.")
                .unwrap();
            assert!(inside(&external, Path::new(&created.skill.path)));
        }
        assert!(!service.home.join(".claude").exists() && !service.home.join(".codex").exists());
    }

    #[test]
    fn malformed_settings_do_not_replace_a_working_state() {
        let (_directory, service) = fixture();
        let mut settings = service.settings();
        settings.theme = "invalid".into();
        assert!(service.save_settings(settings).is_err());
        assert_eq!(service.settings().theme, "system");
        let mut settings = service.settings();
        settings.projects.push("relative".into());
        assert!(service.save_settings(settings).is_err());
        let mut settings = service.settings();
        settings
            .agent_commands
            .insert("claude".into(), "claude\nmalicious".into());
        assert!(service.save_settings(settings).is_err());
    }

    #[cfg(unix)]
    #[test]
    fn config_links_cannot_escape_the_authorized_home() {
        use std::os::unix::fs::symlink;
        let (directory, service) = fixture();
        let selected = config(&service, "Claude Code settings");
        let outside = directory.path().join("outside");
        fs::create_dir(&outside).unwrap();
        symlink(&outside, service.home.join(".claude")).unwrap();
        assert!(
            service
                .save_config(&selected.id, "{}", &selected.revision)
                .is_err()
        );
        assert!(!outside.join("settings.json").exists());
        fs::write(outside.join("settings.json"), "{\"private\":true}").unwrap();
        assert!(service.configs().unwrap_err().contains("outside"));
    }
}
