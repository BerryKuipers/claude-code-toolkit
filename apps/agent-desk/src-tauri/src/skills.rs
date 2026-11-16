use crate::file_store::{
    AgentHomes, TEXT_LIMIT, absolute, approved_anchor, atomic_write, canonical_within,
    display_path, ensure_configured_root, ensure_directory_within, inside, path_key, read_text,
    revision, same_path, set_private_directory, stable_id, write_revision,
};
use crate::types::{AppSettings, DeskResult, SkillDocument, SkillIndex, SkillRecord, SkillRoot};
use serde::de::{self, Deserialize, Deserializer, IgnoredAny, MapAccess, SeqAccess, Visitor};
use std::collections::{HashMap, HashSet};
use std::fmt;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

#[derive(Default)]
struct Frontmatter {
    name: Option<String>,
    description: Option<String>,
}

struct MetadataText(Option<String>);

impl<'de> Deserialize<'de> for MetadataText {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct TextVisitor;
        impl<'de> Visitor<'de> for TextVisitor {
            type Value = MetadataText;
            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a skill metadata value")
            }
            fn visit_str<E: de::Error>(self, value: &str) -> Result<Self::Value, E> {
                Ok(MetadataText(Some(value.chars().take(2000).collect())))
            }
            fn visit_string<E: de::Error>(self, value: String) -> Result<Self::Value, E> {
                self.visit_str(&value)
            }
            fn visit_bool<E: de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(MetadataText(None))
            }
            fn visit_i64<E: de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(MetadataText(None))
            }
            fn visit_u64<E: de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(MetadataText(None))
            }
            fn visit_f64<E: de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(MetadataText(None))
            }
            fn visit_unit<E: de::Error>(self) -> Result<Self::Value, E> {
                Ok(MetadataText(None))
            }
            fn visit_seq<A: SeqAccess<'de>>(
                self,
                mut sequence: A,
            ) -> Result<Self::Value, A::Error> {
                while sequence.next_element::<IgnoredAny>()?.is_some() {}
                Ok(MetadataText(None))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                while map.next_entry::<IgnoredAny, IgnoredAny>()?.is_some() {}
                Ok(MetadataText(None))
            }
        }
        deserializer.deserialize_any(TextVisitor)
    }
}

impl<'de> Deserialize<'de> for Frontmatter {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct MetadataVisitor;
        impl<'de> Visitor<'de> for MetadataVisitor {
            type Value = Frontmatter;
            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a YAML object for skill frontmatter")
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut result = Frontmatter::default();
                let mut fields = HashSet::new();
                while let Some(name) = map.next_key::<String>()? {
                    if !fields.insert(name.clone()) {
                        return Err(de::Error::custom("Duplicate skill frontmatter field."));
                    }
                    match name.as_str() {
                        "name" => {
                            result.name = map
                                .next_value::<MetadataText>()?
                                .0
                                .map(|value| value.chars().take(160).collect())
                        }
                        "description" => result.description = map.next_value::<MetadataText>()?.0,
                        _ => {
                            map.next_value::<IgnoredAny>()?;
                        }
                    }
                }
                Ok(result)
            }
        }
        deserializer.deserialize_map(MetadataVisitor)
    }
}

fn frontmatter(content: &str) -> DeskResult<Frontmatter> {
    let mut lines = content.trim_start_matches('\u{feff}').lines();
    if lines.next().is_none_or(|line| line.trim_end() != "---") {
        return Ok(Frontmatter::default());
    }
    let mut header = String::new();
    for line in lines {
        if line == "---" {
            return serde_yaml_ng::from_str(&header).map_err(|error| {
                format!("Skill frontmatter must be a valid YAML object: {error}")
            });
        }
        header.push_str(line);
        header.push('\n');
    }
    Ok(Frontmatter::default())
}

pub fn validate_skill(content: &str) -> DeskResult<()> {
    if content.trim().is_empty() {
        return Err("Skill content cannot be empty.".into());
    }
    if content.len() > TEXT_LIMIT || content.contains('\0') {
        return Err("Skill content is too large or contains binary data.".into());
    }
    frontmatter(content)?;
    Ok(())
}

pub struct SkillService {
    home: PathBuf,
    data_dir: PathBuf,
    homes: AgentHomes,
    records: Mutex<HashMap<String, SkillRecord>>,
    writes: Mutex<()>,
}

impl SkillService {
    pub fn new(home: PathBuf, data_dir: PathBuf, homes: AgentHomes) -> Self {
        Self {
            home,
            data_dir,
            homes,
            records: Mutex::new(HashMap::new()),
            writes: Mutex::new(()),
        }
    }

    pub fn roots(&self, settings: &AppSettings) -> Vec<SkillRoot> {
        let mut roots = Vec::new();
        let mut push = |path: PathBuf, agent: &str, scope: &str, writable: bool| {
            let path = absolute(&path);
            roots.push(SkillRoot {
                id: stable_id("root", &path_key(&path)),
                path: display_path(&path),
                agent: agent.into(),
                scope: scope.into(),
                writable,
            });
        };
        push(self.homes.claude.join("skills"), "claude", "user", true);
        push(self.homes.codex.join("skills"), "codex", "user", true);
        push(self.homes.gemini.join("skills"), "gemini", "user", true);
        push(
            self.home.join(".gemini/antigravity/skills"),
            "antigravity",
            "user",
            true,
        );
        push(
            self.home.join(".gemini/antigravity/global_skills"),
            "antigravity",
            "user",
            true,
        );
        push(self.home.join(".agents/skills"), "shared", "shared", true);
        let plugins = [
            (self.homes.claude.join("plugins"), "claude"),
            (self.homes.codex.join("plugins"), "codex"),
        ];
        for (path, agent) in &plugins {
            push(path.clone(), agent, "plugin", false);
        }
        for project in &settings.projects {
            for (subdirectory, agent, scope) in [
                (".claude/skills", "claude", "project"),
                (".codex/skills", "codex", "project"),
                (".gemini/skills", "gemini", "project"),
                (".agent/skills", "antigravity", "project"),
                (".agents/skills", "shared", "shared"),
            ] {
                push(Path::new(project).join(subdirectory), agent, scope, true);
            }
        }
        for directory in &settings.skill_directories {
            let plugin = plugins
                .iter()
                .find(|(root, _)| inside(root, Path::new(directory)));
            push(
                directory.into(),
                plugin.map(|(_, agent)| *agent).unwrap_or("shared"),
                if plugin.is_some() { "plugin" } else { "shared" },
                plugin.is_none(),
            );
        }
        let mut positions = HashMap::new();
        let mut unique = Vec::new();
        for root in roots {
            let key = path_key(Path::new(&root.path));
            if let Some(index) = positions.get(&key) {
                unique[*index] = root;
            } else {
                positions.insert(key, unique.len());
                unique.push(root);
            }
        }
        unique
    }

    fn anchor(&self, path: &Path, settings: &AppSettings) -> DeskResult<PathBuf> {
        let configured: Vec<_> = self
            .homes
            .configured
            .iter()
            .cloned()
            .chain(settings.skill_directories.iter().map(PathBuf::from))
            .collect();
        approved_anchor(path, &self.home, &settings.projects, &configured)
    }

    fn writable_roots(&self, roots: &[SkillRoot], settings: &AppSettings) -> Vec<PathBuf> {
        let plugins: Vec<_> = roots
            .iter()
            .filter(|root| root.scope == "plugin")
            .map(|root| {
                fs::canonicalize(&root.path).unwrap_or_else(|_| absolute(Path::new(&root.path)))
            })
            .collect();
        roots
            .iter()
            .filter(|root| root.writable)
            .filter_map(|root| {
                let canonical = fs::canonicalize(&root.path).ok()?;
                let anchor = self.anchor(Path::new(&root.path), settings).ok()?;
                let expected = fs::canonicalize(&anchor)
                    .ok()?
                    .join(relative_descendant(&anchor, Path::new(&root.path)).ok()?);
                (same_path(&canonical, &expected)
                    && !plugins.iter().any(|plugin| inside(plugin, &canonical)))
                .then_some(canonical)
            })
            .collect()
    }

    pub fn list(&self, settings: &AppSettings) -> DeskResult<SkillIndex> {
        let roots = self.roots(settings);
        let writable = self.writable_roots(&roots, settings);
        let mut skills = Vec::new();
        let mut warnings = Vec::new();
        let mut visited = 0usize;
        let mut reached_limit = false;
        for root in &roots {
            let context = (|| -> DeskResult<_> {
                let anchor = self.anchor(Path::new(&root.path), settings)?;
                let canonical_anchor =
                    fs::canonicalize(&anchor).map_err(|error| error.to_string())?;
                let linked = fs::symlink_metadata(&root.path)
                    .map_err(|error| error.to_string())?
                    .file_type()
                    .is_symlink();
                Ok((anchor, canonical_anchor, linked))
            })();
            let (anchor, canonical_anchor, linked) = match context {
                Ok(context) => context,
                Err(_) => {
                    if Path::new(&root.path).exists() {
                        add_warning(&mut warnings, format!("Could not read {}.", root.path));
                    }
                    continue;
                }
            };
            let mut seen = HashSet::new();
            let mut pending = vec![(
                PathBuf::from(&root.path),
                if root.scope == "plugin" { 8 } else { 4 },
                linked,
            )];
            while let Some((directory, depth, inherited_link)) = pending.pop() {
                visited += 1;
                if visited > 12_000 || skills.len() >= 3000 {
                    reached_limit = true;
                    break;
                }
                let canonical = match fs::canonicalize(&directory) {
                    Ok(path) => path,
                    Err(_) => {
                        add_warning(
                            &mut warnings,
                            format!("Could not read {}.", display_path(&directory)),
                        );
                        continue;
                    }
                };
                if !seen.insert(path_key(&canonical)) {
                    continue;
                }
                let entries = match fs::read_dir(&directory) {
                    Ok(entries) => entries,
                    Err(_) => {
                        add_warning(
                            &mut warnings,
                            format!("Could not read {}.", display_path(&directory)),
                        );
                        continue;
                    }
                };
                let entries: Vec<_> = entries.take(12_001).filter_map(Result::ok).collect();
                if entries.len() > 12_000 {
                    reached_limit = true;
                }
                let expected = canonical_anchor.join(relative_descendant(&anchor, &directory)?);
                let linked = inherited_link || !same_path(&canonical, &expected);
                let mut found_skill = false;
                for entry in &entries {
                    let filename = entry.file_name();
                    if filename != "SKILL.md" && filename != "SKILL.md.disabled" {
                        continue;
                    }
                    if !entry
                        .file_type()
                        .is_ok_and(|kind| kind.is_file() || kind.is_symlink())
                    {
                        continue;
                    }
                    found_skill = true;
                    if skills.len() >= 3000 {
                        reached_limit = true;
                        break;
                    }
                    let file = entry.path();
                    let record = (|| -> DeskResult<SkillRecord> {
                        let target = fs::canonicalize(&file).map_err(|error| error.to_string())?;
                        let metadata = frontmatter(&read_text(&file, TEXT_LIMIT)?)?;
                        Ok(SkillRecord {
                            id: stable_id(
                                "skill",
                                &format!("{}:{}", root.id, path_key(&directory.join("SKILL.md"))),
                            ),
                            name: metadata
                                .name
                                .filter(|value| !value.is_empty())
                                .unwrap_or_else(|| {
                                    directory
                                        .file_name()
                                        .unwrap_or_default()
                                        .to_string_lossy()
                                        .into_owned()
                                }),
                            description: metadata.description.unwrap_or_default(),
                            path: display_path(&file),
                            agent: root.agent.clone(),
                            scope: root.scope.clone(),
                            root_id: root.id.clone(),
                            editable: root.writable
                                && writable.iter().any(|root| inside(root, &target)),
                            linked: linked || entry.file_type().is_ok_and(|kind| kind.is_symlink()),
                            disabled: Some(filename == "SKILL.md.disabled"),
                        })
                    })();
                    match record {
                        Ok(record) => skills.push(record),
                        Err(error) => add_warning(
                            &mut warnings,
                            format!("Could not read {}: {error}", display_path(&file)),
                        ),
                    }
                }
                if found_skill || depth == 0 {
                    continue;
                }
                for entry in entries.into_iter().rev() {
                    if visited + pending.len() >= 12_000 {
                        reached_limit = true;
                        break;
                    }
                    let name = entry.file_name().to_string_lossy().into_owned();
                    if name.starts_with('.')
                        || ["node_modules", "__pycache__", "dist", "build"].contains(&name.as_str())
                    {
                        continue;
                    }
                    let kind = match entry.file_type() {
                        Ok(kind) => kind,
                        Err(_) => continue,
                    };
                    if kind.is_dir() {
                        pending.push((entry.path(), depth - 1, linked));
                    } else if kind.is_symlink()
                        && fs::metadata(entry.path()).is_ok_and(|metadata| metadata.is_dir())
                    {
                        pending.push((entry.path(), depth - 1, true));
                    }
                }
            }
            if visited > 12_000 || skills.len() >= 3000 {
                break;
            }
        }
        if reached_limit {
            add_warning(
                &mut warnings,
                "The scan reached its safety limit. Use more specific skill directories.".into(),
            );
        }
        skills.sort_by_cached_key(|skill| skill.name.to_lowercase());
        *self
            .records
            .lock()
            .map_err(|_| "The skill index is unavailable.")? = skills
            .iter()
            .map(|skill| (skill.id.clone(), skill.clone()))
            .collect();
        Ok(SkillIndex {
            skills,
            roots,
            warnings,
        })
    }

    fn find(&self, id: &str, settings: &AppSettings) -> DeskResult<SkillRecord> {
        let cached = self
            .records
            .lock()
            .map_err(|_| "The skill index is unavailable.")?
            .get(id)
            .cloned();
        if let Some(record) = cached
            && self
                .roots(settings)
                .iter()
                .any(|root| root.id == record.root_id)
        {
            return Ok(record);
        }
        self.list(settings)?
            .skills
            .into_iter()
            .find(|skill| skill.id == id)
            .ok_or_else(|| "Skill is no longer available. Refresh the list.".into())
    }

    pub fn read(&self, id: &str, settings: &AppSettings) -> DeskResult<SkillDocument> {
        let skill = self.find(id, settings)?;
        let content = read_text(Path::new(&skill.path), TEXT_LIMIT)?;
        Ok(SkillDocument {
            revision: revision(Some(&content)),
            skill,
            content,
        })
    }

    pub fn save(
        &self,
        id: &str,
        content: &str,
        expected_revision: &str,
        settings: &AppSettings,
    ) -> DeskResult<SkillDocument> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The skill write lock is unavailable.")?;
        validate_skill(content)?;
        let skill = self.find(id, settings)?;
        let roots = self.roots(settings);
        if !skill.editable
            || !roots
                .iter()
                .any(|root| root.id == skill.root_id && root.writable)
        {
            return Err(
                "Installed plugin skills are read-only. Create a personal copy to customize one."
                    .into(),
            );
        }
        write_revision(
            Path::new(&skill.path),
            content,
            expected_revision,
            &self.writable_roots(&roots, settings),
            &self.data_dir.join("backups/skills"),
        )?;
        self.list(settings)?;
        self.read(id, settings)
    }

    pub fn create(
        &self,
        root_id: &str,
        name: &str,
        content: &str,
        settings: &AppSettings,
    ) -> DeskResult<SkillDocument> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The skill write lock is unavailable.")?;
        if name.is_empty()
            || name.len() > 80
            || !name.as_bytes()[0].is_ascii_alphanumeric()
            || !name.bytes().all(|value| {
                value.is_ascii_lowercase()
                    || value.is_ascii_digit()
                    || value == b'_'
                    || value == b'-'
            })
        {
            return Err(
                "Use a lowercase name with letters, numbers, hyphens, or underscores.".into(),
            );
        }
        validate_skill(content)?;
        let root = self
            .roots(settings)
            .into_iter()
            .find(|root| root.id == root_id && root.writable)
            .ok_or("Choose a writable personal or project skills directory.")?;
        let root_path = Path::new(&root.path);
        let explicit = settings
            .skill_directories
            .iter()
            .any(|directory| same_path(Path::new(directory), root_path));
        if explicit
            && fs::symlink_metadata(root_path)
                .map_err(|error| error.to_string())?
                .file_type()
                .is_symlink()
        {
            return Err("Create the skill in the linked directory’s original location.".into());
        }
        let destination = prospective_canonical(root_path)?;
        if self
            .roots(settings)
            .iter()
            .filter(|root| root.scope == "plugin")
            .any(|plugin| {
                let path = fs::canonicalize(&plugin.path)
                    .unwrap_or_else(|_| absolute(Path::new(&plugin.path)));
                inside(&path, &destination)
            })
        {
            return Err(
                "Installed plugin skills are read-only. Create a personal copy to customize one."
                    .into(),
            );
        }
        let anchor = if explicit {
            root_path.to_path_buf()
        } else {
            approved_anchor(
                root_path,
                &self.home,
                &settings.projects,
                &self.homes.configured,
            )?
        };
        if self
            .homes
            .configured
            .iter()
            .any(|root| same_path(root, &anchor))
        {
            ensure_configured_root(&anchor)?;
        }
        ensure_directory_within(root_path, &anchor)?;
        let canonical_root = fs::canonicalize(root_path).map_err(|error| error.to_string())?;
        let directory = canonical_root.join(name);
        match fs::create_dir(&directory) {
            Ok(()) => set_private_directory(&directory)?,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                return Err("A skill with this directory name already exists.".into());
            }
            Err(error) => return Err(error.to_string()),
        }
        if !inside(
            &canonical_root,
            &fs::canonicalize(&directory).map_err(|error| error.to_string())?,
        ) {
            return Err("The selected directory changed. Refresh and try again.".into());
        }
        atomic_write(&directory.join("SKILL.md"), content)?;
        let record = self
            .list(settings)?
            .skills
            .into_iter()
            .find(|skill| {
                skill.root_id == root.id
                    && Path::new(&skill.path)
                        .parent()
                        .and_then(Path::file_name)
                        .is_some_and(|value| value == name)
            })
            .ok_or(
                "The skill was created but the directory could not be indexed. Refresh the list.",
            )?;
        self.read(&record.id, settings)
    }

    pub fn set_enabled(&self, id: &str, enabled: bool, settings: &AppSettings) -> DeskResult<()> {
        let _guard = self
            .writes
            .lock()
            .map_err(|_| "The skill write lock is unavailable.")?;
        self.list(settings)?;
        let skill = self.find(id, settings)?;
        let roots = self.roots(settings);
        if !skill.editable
            || !roots
                .iter()
                .any(|root| root.id == skill.root_id && root.writable)
        {
            return Err(
                "Installed plugin skills are read-only. Manage their plugin in agent settings."
                    .into(),
            );
        }
        if skill.linked {
            return Err("Change the enabled state at this linked skill’s original location. This avoids disabling it for other agents.".into());
        }
        if skill.disabled.unwrap_or(false) != enabled {
            return Ok(());
        }
        let writable = self.writable_roots(&roots, settings);
        let source = canonical_within(Path::new(&skill.path), &writable, false)?;
        let target = source
            .parent()
            .ok_or("The skill has no parent directory.")?
            .join(if enabled {
                "SKILL.md"
            } else {
                "SKILL.md.disabled"
            });
        if fs::symlink_metadata(&target).is_ok() {
            return Err("Both enabled and disabled versions already exist. Resolve the duplicate before switching.".into());
        }
        canonical_within(&target, &writable, true)?;
        fs::rename(source, target).map_err(|error| error.to_string())?;
        self.list(settings)?;
        Ok(())
    }
}

fn relative_descendant(root: &Path, path: &Path) -> DeskResult<PathBuf> {
    if !inside(root, path) {
        return Err("The skill directory is outside its approved root.".into());
    }
    let root = absolute(root);
    Ok(absolute(path)
        .components()
        .skip(root.components().count())
        .map(|part| part.as_os_str())
        .collect())
}

fn prospective_canonical(path: &Path) -> DeskResult<PathBuf> {
    let mut ancestor = absolute(path);
    loop {
        match fs::canonicalize(&ancestor) {
            Ok(canonical) => return Ok(canonical.join(relative_descendant(&ancestor, path)?)),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                if !ancestor.pop() {
                    return Err("The skill directory has no existing parent.".into());
                }
            }
            Err(error) => return Err(error.to_string()),
        }
    }
}

fn add_warning(warnings: &mut Vec<String>, warning: String) {
    if warnings.len() < 100 {
        warnings.push(warning);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::file_store::agent_homes_with;
    use crate::workspace::default_settings;
    const CONTENT: &str =
        "---\nname: Useful skill\ndescription: Helps with a task\n---\n\nDo the work.\n";

    fn fixture() -> (tempfile::TempDir, SkillService, AppSettings) {
        let root = tempfile::tempdir().unwrap();
        let home = root.path().join("home");
        fs::create_dir(&home).unwrap();
        let homes = agent_homes_with(&home, |_| None);
        let service = SkillService::new(home, root.path().join("data"), homes);
        (root, service, default_settings())
    }

    #[test]
    fn a_skill_can_be_created_edited_disabled_and_restored_without_content_loss() {
        let (_directory, service, settings) = fixture();
        let root = service.roots(&settings).remove(0);
        let created = service
            .create(&root.id, "useful", CONTENT, &settings)
            .unwrap();
        assert!(created.skill.editable);
        assert!(!created.skill.linked);
        let changed = CONTENT.replace("Do the work.", "Finish the task.");
        let saved = service
            .save(&created.skill.id, &changed, &created.revision, &settings)
            .unwrap();
        assert_ne!(saved.revision, created.revision);
        service
            .set_enabled(&created.skill.id, false, &settings)
            .unwrap();
        assert_eq!(
            service
                .read(&created.skill.id, &settings)
                .unwrap()
                .skill
                .disabled,
            Some(true)
        );
        service
            .set_enabled(&created.skill.id, true, &settings)
            .unwrap();
        assert_eq!(
            service.read(&created.skill.id, &settings).unwrap().content,
            changed
        );
    }

    #[test]
    fn traversal_stale_edits_and_invalid_frontmatter_are_rejected() {
        let (_directory, service, settings) = fixture();
        let root = service.roots(&settings).remove(0);
        assert!(
            service
                .create(&root.id, "../outside", CONTENT, &settings)
                .is_err()
        );
        assert!(validate_skill("---\nname: [broken\n---\nbody").is_err());
        assert!(validate_skill("---\n- list\n---\nbody").is_err());
        let created = service
            .create(&root.id, "safe", CONTENT, &settings)
            .unwrap();
        fs::write(&created.skill.path, "External change.").unwrap();
        assert!(
            service
                .save(&created.skill.id, CONTENT, &created.revision, &settings)
                .unwrap_err()
                .contains("changed outside")
        );
        assert_eq!(
            fs::read_to_string(&created.skill.path).unwrap(),
            "External change."
        );
    }

    #[test]
    fn registering_a_plugin_directory_never_makes_it_writable() {
        let (directory, service, mut settings) = fixture();
        let plugin = directory
            .path()
            .join("home/.claude/plugins/cache/plugin/skills");
        fs::create_dir_all(plugin.join("example")).unwrap();
        fs::write(plugin.join("example/SKILL.md"), CONTENT).unwrap();
        settings.skill_directories.push(display_path(&plugin));
        let index = service.list(&settings).unwrap();
        assert!(!index.skills.is_empty());
        assert!(
            index
                .skills
                .iter()
                .all(|skill| !skill.editable && skill.scope == "plugin")
        );
    }

    #[cfg(unix)]
    #[test]
    fn an_alias_ancestor_cannot_create_skills_inside_a_plugin_cache() {
        use std::os::unix::fs::symlink;
        let (directory, service, mut settings) = fixture();
        let plugins = directory.path().join("home/.claude/plugins");
        fs::create_dir_all(plugins.join("cache/example/skills")).unwrap();
        let alias = directory.path().join("alias");
        symlink(&plugins, &alias).unwrap();
        settings
            .skill_directories
            .push(display_path(&alias.join("cache/example/skills")));
        let root = service
            .roots(&settings)
            .into_iter()
            .find(|root| root.path == settings.skill_directories[0])
            .unwrap();
        assert!(
            service
                .create(&root.id, "should-not-exist", CONTENT, &settings)
                .unwrap_err()
                .contains("read-only")
        );
        assert!(
            !plugins
                .join("cache/example/skills/should-not-exist")
                .exists()
        );
    }

    #[cfg(unix)]
    #[test]
    fn linked_skills_are_editable_only_in_registered_roots_and_cannot_be_disabled_through_a_link() {
        use std::os::unix::fs::symlink;
        let (directory, service, settings) = fixture();
        let shared = directory.path().join("home/.agents/skills/task");
        let user = directory.path().join("home/.claude/skills");
        fs::create_dir_all(&shared).unwrap();
        fs::create_dir_all(&user).unwrap();
        fs::write(shared.join("SKILL.md"), CONTENT).unwrap();
        symlink(&shared, user.join("task")).unwrap();
        let linked = service
            .list(&settings)
            .unwrap()
            .skills
            .into_iter()
            .find(|skill| skill.agent == "claude")
            .unwrap();
        assert!(linked.linked && linked.editable);
        let document = service.read(&linked.id, &settings).unwrap();
        service
            .save(
                &linked.id,
                &format!("{CONTENT}Improved."),
                &document.revision,
                &settings,
            )
            .unwrap();
        assert!(
            service
                .set_enabled(&linked.id, false, &settings)
                .unwrap_err()
                .contains("original location")
        );
        assert!(
            fs::read_to_string(shared.join("SKILL.md"))
                .unwrap()
                .contains("Improved.")
        );
        let outside = directory.path().join("outside");
        fs::create_dir(&outside).unwrap();
        fs::write(outside.join("SKILL.md"), CONTENT).unwrap();
        symlink(&outside, user.join("outside")).unwrap();
        let external = service
            .list(&settings)
            .unwrap()
            .skills
            .into_iter()
            .find(|skill| skill.path.contains("outside"))
            .unwrap();
        assert!(!external.editable);
    }
}
