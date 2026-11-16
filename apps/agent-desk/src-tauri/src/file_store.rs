use crate::types::DeskResult;
use serde::de::DeserializeOwned;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
#[cfg(unix)]
use std::fs::File;
use std::fs::{self, OpenOptions, Permissions};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use std::sync::{Arc, Mutex, OnceLock, Weak};
use uuid::Uuid;

pub const TEXT_LIMIT: usize = 2 * 1024 * 1024;

#[derive(Clone, Debug)]
pub struct AgentHomes {
    pub claude: PathBuf,
    pub codex: PathBuf,
    pub gemini: PathBuf,
    pub configured: Vec<PathBuf>,
}

pub fn revision(content: Option<&str>) -> String {
    content
        .map(|value| format!("{:x}", Sha256::digest(value.as_bytes())))
        .unwrap_or_else(|| "missing".into())
}

pub fn stable_id(prefix: &str, value: &str) -> String {
    format!("{prefix}-{}", &revision(Some(value))[..24])
}

pub fn absolute(path: &Path) -> PathBuf {
    let value = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(path)
    };
    let mut normalized = PathBuf::new();
    for component in value.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                normalized.pop();
            }
            _ => normalized.push(component.as_os_str()),
        }
    }
    normalized
}

pub fn display_path(path: &Path) -> String {
    let value = path.to_string_lossy().into_owned();
    if cfg!(windows) {
        if let Some(rest) = value.strip_prefix(r"\\?\UNC\") {
            return format!(r"\\{rest}");
        }
        if let Some(rest) = value.strip_prefix(r"\\?\") {
            return rest.to_owned();
        }
    }
    value
}

fn comparison_key(value: &str, windows: bool) -> String {
    if windows {
        let value = value.replace('\\', "/").to_lowercase();
        let value = value
            .strip_prefix("//?/unc/")
            .map(|rest| format!("//{rest}"))
            .or_else(|| value.strip_prefix("//?/").map(str::to_owned))
            .unwrap_or(value);
        value.trim_end_matches('/').to_owned()
    } else {
        value.trim_end_matches('/').to_owned()
    }
}

pub fn path_key(path: &Path) -> String {
    comparison_key(&display_path(&absolute(path)), cfg!(windows))
}

pub fn same_path(left: &Path, right: &Path) -> bool {
    path_key(left) == path_key(right)
}

pub fn inside(root: &Path, candidate: &Path) -> bool {
    let root = path_key(root);
    let candidate = path_key(candidate);
    candidate == root
        || candidate.strip_prefix(&root).is_some_and(|suffix| {
            suffix.starts_with(std::path::MAIN_SEPARATOR)
                || (cfg!(windows) && suffix.starts_with('/'))
        })
}

pub fn agent_homes(home: &Path) -> AgentHomes {
    agent_homes_with(home, |name| {
        std::env::var(name).ok().filter(|value| !value.is_empty())
    })
}

pub fn agent_homes_with(home: &Path, env: impl Fn(&str) -> Option<String>) -> AgentHomes {
    let expand = |value: String| {
        absolute(&if value == "~" {
            home.to_path_buf()
        } else if value.starts_with("~/") || value.starts_with("~\\") {
            home.join(&value[2..])
        } else {
            PathBuf::from(value)
        })
    };
    let claude_override = env("CLAUDE_CONFIG_DIR");
    let codex_override = env("CODEX_HOME");
    let gemini_override = env("GEMINI_CLI_HOME");
    let claude = claude_override
        .clone()
        .map(&expand)
        .unwrap_or_else(|| absolute(&home.join(".claude")));
    let codex = codex_override
        .clone()
        .map(&expand)
        .unwrap_or_else(|| absolute(&home.join(".codex")));
    let gemini = gemini_override
        .clone()
        .map(&expand)
        .unwrap_or_else(|| absolute(home))
        .join(".gemini");
    let mut configured = Vec::new();
    if claude_override.is_some() {
        configured.push(claude.clone());
    }
    if codex_override.is_some() {
        configured.push(codex.clone());
    }
    if gemini_override.is_some() {
        configured.push(gemini.clone());
    }
    AgentHomes {
        claude,
        codex,
        gemini,
        configured,
    }
}

pub fn approved_anchor(
    file: &Path,
    home: &Path,
    projects: &[String],
    configured: &[PathBuf],
) -> DeskResult<PathBuf> {
    let mut candidates: Vec<_> = projects
        .iter()
        .map(PathBuf::from)
        .chain(configured.iter().cloned())
        .chain(std::iter::once(home.to_path_buf()))
        .map(|path| absolute(&path))
        .filter(|root| inside(root, file))
        .collect();
    candidates.sort_by_key(|path| std::cmp::Reverse(path.components().count()));
    candidates
        .into_iter()
        .next()
        .ok_or_else(|| "This path is outside the configured agent homes and projects.".into())
}

pub fn ensure_configured_root(root: &Path) -> DeskResult<PathBuf> {
    let mut ancestor = absolute(root);
    loop {
        match fs::metadata(&ancestor) {
            Ok(metadata) if metadata.is_dir() => break,
            Ok(_) => return Err("The configured agent home is not a directory.".into()),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                if !ancestor.pop() {
                    return Err("Cannot find the configured agent home.".into());
                }
            }
            Err(error) => return Err(format!("Cannot access the configured agent home: {error}")),
        }
    }
    ensure_directory_within(root, &ancestor)
}

pub fn read_text(file: &Path, limit: usize) -> DeskResult<String> {
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.custom_flags(libc::O_NONBLOCK);
    }
    let handle = options
        .open(file)
        .map_err(|error| format!("Cannot read {}: {error}", display_path(file)))?;
    let metadata = handle.metadata().map_err(|error| error.to_string())?;
    if !metadata.is_file() {
        return Err("The selected path is not a regular file.".into());
    }
    if metadata.len() > limit as u64 {
        return Err(format!(
            "File exceeds the {} KiB editor limit.",
            limit / 1024
        ));
    }
    let mut bytes = Vec::with_capacity((metadata.len() as usize).min(limit));
    handle
        .take((limit + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|error| error.to_string())?;
    if bytes.len() > limit {
        return Err("File changed beyond the editor size limit while reading.".into());
    }
    if bytes.contains(&0) {
        return Err("Binary files cannot be edited.".into());
    }
    String::from_utf8(bytes).map_err(|_| "The selected file is not valid UTF-8 text.".into())
}

pub fn optional_text(file: &Path) -> DeskResult<Option<String>> {
    match fs::metadata(file) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(format!("Cannot read {}: {error}", display_path(file))),
        Ok(_) => read_text(file, TEXT_LIMIT).map(Some),
    }
}

pub fn canonical_within(
    file: &Path,
    roots: &[PathBuf],
    allow_missing: bool,
) -> DeskResult<PathBuf> {
    let canonical = match fs::canonicalize(file) {
        Ok(path) => path,
        Err(error) if allow_missing && error.kind() == std::io::ErrorKind::NotFound => {
            let parent = file
                .parent()
                .ok_or("The selected file has no parent directory.")?;
            let parent = fs::canonicalize(parent).map_err(|error| error.to_string())?;
            parent.join(
                file.file_name()
                    .ok_or("The selected path has no file name.")?,
            )
        }
        Err(error) => return Err(format!("Cannot resolve the selected file: {error}")),
    };
    if !roots
        .iter()
        .filter_map(|root| fs::canonicalize(root).ok())
        .any(|root| inside(&root, &canonical))
    {
        return Err("This path points outside its approved directory.".into());
    }
    Ok(canonical)
}

pub fn ensure_directory_within(directory: &Path, anchor: &Path) -> DeskResult<PathBuf> {
    let directory = absolute(directory);
    let anchor = absolute(anchor);
    if !inside(&anchor, &directory) {
        return Err("Directory is outside its approved root.".into());
    }
    let canonical_anchor = fs::canonicalize(&anchor).map_err(|error| error.to_string())?;
    let mut current = canonical_anchor.clone();
    for part in directory.components().skip(anchor.components().count()) {
        current.push(part.as_os_str());
        match fs::create_dir(&current) {
            Ok(()) => set_private_directory(&current)?,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(error) => return Err(error.to_string()),
        }
        let metadata = fs::symlink_metadata(&current).map_err(|error| error.to_string())?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err("A destination directory is a link or is not a directory. Choose its original location.".into());
        }
        let canonical = fs::canonicalize(&current).map_err(|error| error.to_string())?;
        if !inside(&canonical_anchor, &canonical) {
            return Err("Destination directory escaped its approved root.".into());
        }
    }
    Ok(current)
}

pub fn set_private_directory(path: &Path) -> DeskResult<()> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, Permissions::from_mode(0o700))
            .map_err(|error| error.to_string())?;
    }
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}

pub fn atomic_write(file: &Path, content: &str) -> DeskResult<()> {
    atomic_write_checked(file, content, None, || Ok(()))
}

fn atomic_write_checked(
    file: &Path,
    content: &str,
    permissions: Option<Permissions>,
    before_commit: impl FnOnce() -> DeskResult<()>,
) -> DeskResult<()> {
    if content.len() > TEXT_LIMIT {
        return Err("Content exceeds the editor size limit.".into());
    }
    let parent = file
        .parent()
        .ok_or("The destination has no parent directory.")?;
    fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    let filename = file
        .file_name()
        .ok_or("The destination has no file name.")?
        .to_string_lossy();
    let temporary = parent.join(format!(".{filename}.{}.tmp", Uuid::new_v4()));
    let result = (|| {
        let mut options = OpenOptions::new();
        options.write(true).create_new(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        let mut handle = options
            .open(&temporary)
            .map_err(|error| error.to_string())?;
        if let Some(permissions) = permissions {
            handle
                .set_permissions(permissions)
                .map_err(|error| error.to_string())?;
        }
        handle
            .write_all(content.as_bytes())
            .map_err(|error| error.to_string())?;
        handle.sync_all().map_err(|error| error.to_string())?;
        drop(handle);
        before_commit()?;
        fs::rename(&temporary, file).map_err(|error| error.to_string())?;
        #[cfg(unix)]
        if let Ok(parent) = File::open(parent) {
            let _ = parent.sync_all();
        }
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

type WriteLocks = Mutex<HashMap<String, Weak<Mutex<()>>>>;
static FILE_WRITES: OnceLock<WriteLocks> = OnceLock::new();

pub fn write_revision(
    file: &Path,
    content: &str,
    expected_revision: &str,
    roots: &[PathBuf],
    backup_dir: &Path,
) -> DeskResult<String> {
    let canonical = canonical_within(file, roots, true)?;
    let key = path_key(&canonical);
    let lock = {
        let mut locks = FILE_WRITES
            .get_or_init(|| Mutex::new(HashMap::new()))
            .lock()
            .map_err(|_| "The file write lock is unavailable.")?;
        locks.retain(|_, lock| lock.strong_count() > 0);
        if let Some(lock) = locks.get(&key).and_then(Weak::upgrade) {
            lock
        } else {
            let lock = Arc::new(Mutex::new(()));
            locks.insert(key, Arc::downgrade(&lock));
            lock
        }
    };
    let _guard = lock
        .lock()
        .map_err(|_| "The file write lock is unavailable.")?;
    let current = optional_text(&canonical)?;
    if revision(current.as_deref()) != expected_revision {
        return Err("This file changed outside Agent Desk. Reload it before saving.".into());
    }
    let permissions = if let Some(current) = &current {
        let backup = backup_dir.join(format!(
            "{}-{}-{}",
            chrono::Utc::now().timestamp_millis(),
            Uuid::new_v4(),
            canonical.file_name().unwrap_or_default().to_string_lossy()
        ));
        atomic_write(&backup, current)?;
        Some(
            fs::metadata(&canonical)
                .map_err(|error| error.to_string())?
                .permissions(),
        )
    } else {
        None
    };
    atomic_write_checked(&canonical, content, permissions, || {
        if !same_path(&canonical_within(file, roots, true)?, &canonical) {
            return Err("The destination changed while saving. Reload it.".into());
        }
        if revision(optional_text(&canonical)?.as_deref()) != expected_revision {
            return Err("This file changed while saving. Reload it.".into());
        }
        Ok(())
    })?;
    Ok(revision(Some(content)))
}

pub fn read_json<T: DeserializeOwned>(file: &Path, fallback: T) -> DeskResult<T> {
    match optional_text(file)? {
        None => Ok(fallback),
        Some(content) => serde_json::from_str(&content).map_err(|_| {
            format!(
                "Cannot read {}: invalid JSON. Your existing file was left intact.",
                file.file_name().unwrap_or_default().to_string_lossy()
            )
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Barrier;

    #[test]
    fn path_identity_preserves_boundaries_and_platform_semantics() {
        assert_eq!(
            comparison_key(r"C:\Users\Berry\Skills\", true),
            comparison_key("c:/users/berry/skills", true)
        );
        assert_eq!(
            comparison_key(r"\\?\UNC\Server\Share\Skills", true),
            comparison_key(r"\\server\share\skills", true)
        );
        assert_ne!(
            comparison_key("/home/Berry", false),
            comparison_key("/home/berry", false)
        );
        let directory = tempfile::tempdir().unwrap();
        assert!(inside(directory.path(), &directory.path().join("a/../b")));
        assert!(!inside(
            &directory.path().join("a"),
            &directory.path().join("ab")
        ));
        assert_ne!(revision(None), revision(Some("")));
    }

    #[test]
    fn concurrent_edits_with_one_revision_only_commit_once() {
        let directory = tempfile::tempdir().unwrap();
        let file = directory.path().join("settings.json");
        fs::write(&file, "original").unwrap();
        let barrier = Arc::new(Barrier::new(2));
        let jobs: Vec<_> = ["first", "second"]
            .into_iter()
            .map(|content| {
                let barrier = barrier.clone();
                let file = file.clone();
                let root = directory.path().to_path_buf();
                std::thread::spawn(move || {
                    barrier.wait();
                    write_revision(
                        &file,
                        content,
                        &revision(Some("original")),
                        std::slice::from_ref(&root),
                        &root.join("backups"),
                    )
                })
            })
            .collect();
        let results: Vec<_> = jobs.into_iter().map(|job| job.join().unwrap()).collect();
        assert_eq!(
            results.iter().filter(|result| result.is_ok()).count(),
            1,
            "Write results: {results:?}"
        );
        let backups: Vec<_> = fs::read_dir(directory.path().join("backups"))
            .unwrap()
            .collect();
        assert_eq!(backups.len(), 1);
        assert_eq!(
            fs::read_to_string(backups[0].as_ref().unwrap().path()).unwrap(),
            "original"
        );
    }

    #[test]
    fn a_missing_revision_does_not_overwrite_a_new_empty_file() {
        let directory = tempfile::tempdir().unwrap();
        let file = directory.path().join("new.json");
        fs::write(&file, "").unwrap();
        let error = write_revision(
            &file,
            "replacement",
            "missing",
            &[directory.path().into()],
            &directory.path().join("backups"),
        )
        .unwrap_err();
        assert!(
            error.contains("changed outside"),
            "Unexpected write error: {error}"
        );
        assert_eq!(fs::read_to_string(file).unwrap(), "");
    }

    #[cfg(unix)]
    #[test]
    fn approved_root_aliases_resolve_before_containment_but_child_links_cannot_escape() {
        use std::os::unix::fs::symlink;
        let directory = tempfile::tempdir().unwrap();
        let original = directory.path().join("original");
        let alias = directory.path().join("alias");
        let outside = directory.path().join("outside");
        fs::create_dir(&original).unwrap();
        fs::create_dir(&outside).unwrap();
        symlink(&original, &alias).unwrap();
        let file = alias.join("settings.json");
        fs::write(&file, "original").unwrap();
        assert_eq!(
            canonical_within(&file, std::slice::from_ref(&alias), false).unwrap(),
            fs::canonicalize(&file).unwrap()
        );
        write_revision(
            &file,
            "changed",
            &revision(Some("original")),
            std::slice::from_ref(&alias),
            &directory.path().join("backups"),
        )
        .unwrap();
        assert_eq!(
            fs::read_to_string(original.join("settings.json")).unwrap(),
            "changed"
        );
        let new_file = alias.join("new.json");
        assert_eq!(
            canonical_within(&new_file, std::slice::from_ref(&alias), true).unwrap(),
            fs::canonicalize(&original).unwrap().join("new.json")
        );
        write_revision(
            &new_file,
            "created",
            "missing",
            std::slice::from_ref(&alias),
            &directory.path().join("backups"),
        )
        .unwrap();
        assert_eq!(
            fs::read_to_string(original.join("new.json")).unwrap(),
            "created"
        );
        symlink(&outside, original.join("escape")).unwrap();
        fs::write(outside.join("keep.json"), "untouched").unwrap();
        assert!(
            canonical_within(
                &alias.join("escape/keep.json"),
                std::slice::from_ref(&alias),
                false
            )
            .unwrap_err()
            .contains("outside")
        );
        assert!(
            write_revision(
                &alias.join("escape/keep.json"),
                "replacement",
                &revision(Some("untouched")),
                std::slice::from_ref(&alias),
                &directory.path().join("backups")
            )
            .is_err()
        );
        assert!(
            canonical_within(
                &alias.join("escape/new.json"),
                std::slice::from_ref(&alias),
                true
            )
            .is_err()
        );
        assert_eq!(
            fs::read_to_string(outside.join("keep.json")).unwrap(),
            "untouched"
        );
        assert!(!outside.join("new.json").exists());
    }

    #[cfg(unix)]
    #[test]
    fn a_named_pipe_is_rejected_without_waiting_for_a_writer() {
        use std::ffi::CString;
        use std::os::unix::ffi::OsStrExt;
        let directory = tempfile::tempdir().unwrap();
        let path = directory.path().join("not-a-text-file");
        let name = CString::new(path.as_os_str().as_bytes()).unwrap();
        assert_eq!(unsafe { libc::mkfifo(name.as_ptr(), 0o600) }, 0);
        assert!(
            read_text(&path, TEXT_LIMIT)
                .unwrap_err()
                .contains("regular file")
        );
    }

    #[test]
    fn configured_agent_homes_keep_gemini_parent_semantics() {
        let directory = tempfile::tempdir().unwrap();
        let root = directory.path().join("external");
        let homes = agent_homes_with(directory.path(), |name| match name {
            "CLAUDE_CONFIG_DIR" => Some(display_path(&root.join("claude"))),
            "CODEX_HOME" => Some(display_path(&root.join("codex"))),
            "GEMINI_CLI_HOME" => Some(display_path(&root.join("google"))),
            _ => None,
        });
        assert_eq!(homes.gemini, root.join("google/.gemini"));
        assert_eq!(homes.configured.len(), 3);
    }
}
