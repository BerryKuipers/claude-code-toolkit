use crate::file_store::{path_key, read_json, revision};
use crate::types::DeskResult;
use keyring::v1::{Entry, Error as KeyringError};
use std::collections::{HashMap, HashSet};
use std::path::Path;

trait CredentialBackend: Send + Sync {
    fn available(&self) -> bool;
    fn get(&self, id: &str) -> DeskResult<Option<String>>;
    fn set(&self, id: &str, value: &str) -> DeskResult<()>;
    fn delete(&self, id: &str) -> DeskResult<()>;
}

struct OsCredentials {
    service: String,
}

impl OsCredentials {
    fn entry(&self, id: &str) -> DeskResult<Entry> {
        Entry::new(&self.service, id).map_err(|_| {
            "The operating-system credential store is unavailable. Choose session-only storage."
                .into()
        })
    }
}

impl CredentialBackend for OsCredentials {
    fn available(&self) -> bool {
        Entry::store_status().is_ok()
    }

    fn get(&self, id: &str) -> DeskResult<Option<String>> {
        match self.entry(id)?.get_password() {
            Ok(value) => Ok(Some(value)),
            Err(KeyringError::NoEntry) => Ok(None),
            Err(_) => Err("The saved key could not be read from the operating-system credential store. Unlock it or enter a session-only key.".into()),
        }
    }

    fn set(&self, id: &str, value: &str) -> DeskResult<()> {
        self.entry(id)?.set_password(value).map_err(|_| "The operating-system credential store could not save this key. Choose session-only storage.".into())
    }

    fn delete(&self, id: &str) -> DeskResult<()> {
        match self.entry(id)?.delete_credential() {
            Ok(()) | Err(KeyringError::NoEntry) => Ok(()),
            Err(_) => Err("The operating-system credential store could not delete the saved key. Unlock it and try again.".into()),
        }
    }
}

pub struct SecretStore {
    session: HashMap<String, String>,
    legacy_ids: HashSet<String>,
    backend: Box<dyn CredentialBackend>,
}

impl SecretStore {
    pub fn new(data_dir: &Path) -> DeskResult<Self> {
        let namespace = revision(Some(&path_key(data_dir)));
        Self::with_backend(
            data_dir,
            Box::new(OsCredentials {
                service: format!("dev.berry.agentdesk.{}", &namespace[..24]),
            }),
        )
    }

    fn with_backend(data_dir: &Path, backend: Box<dyn CredentialBackend>) -> DeskResult<Self> {
        let legacy: serde_json::Value =
            read_json(&data_dir.join("credentials.json"), serde_json::json!({}))?;
        let object = legacy
            .as_object()
            .ok_or("The legacy credential file is malformed. It was left intact.")?;
        if object.values().any(|value| !value.is_string()) {
            return Err("The legacy credential file is malformed. It was left intact.".into());
        }
        Ok(Self {
            session: HashMap::new(),
            legacy_ids: object.keys().cloned().collect(),
            backend,
        })
    }

    pub fn available(&self) -> bool {
        self.backend.available()
    }

    pub fn has(&self, id: &str) -> bool {
        self.session.contains_key(id)
            || (self.available() && matches!(self.backend.get(id), Ok(Some(_))))
    }

    pub fn get(&self, id: &str) -> DeskResult<Option<String>> {
        if let Some(value) = self.session.get(id) {
            return Ok(Some(value.clone()));
        }
        if self.available()
            && let Some(value) = self.backend.get(id)?
        {
            return Ok(Some(value));
        }
        Ok(None)
    }

    pub fn set(&mut self, id: &str, secret: &str, persist: bool) -> DeskResult<()> {
        validate_id(id)?;
        let secret = secret.trim();
        if secret.is_empty() || secret.len() > 16_384 || secret.contains(['\0', '\r', '\n']) {
            return Err("Enter a valid API key on one line.".into());
        }
        if persist {
            if !self.available() {
                return Err(
                    "Secure operating-system storage is unavailable. Choose session-only storage."
                        .into(),
                );
            }
            self.backend.set(id, secret)?;
            self.session.remove(id);
        } else {
            if self.available() {
                self.backend.delete(id)?;
            }
            self.session.insert(id.to_owned(), secret.to_owned());
        }
        Ok(())
    }

    pub fn delete(&mut self, id: &str) -> DeskResult<()> {
        validate_id(id)?;
        if self.available() {
            self.backend.delete(id)?;
        }
        self.session.remove(id);
        self.legacy_ids.remove(id);
        Ok(())
    }

    pub fn warnings(&self) -> Vec<String> {
        if self.legacy_ids.iter().any(|id| !self.has(id)) {
            vec!["Keys saved by the previous Electron version remain encrypted in the preserved credentials.json file. Re-enter those profile keys in Agent Desk or use existing API key environment variables.".into()]
        } else {
            Vec::new()
        }
    }

    #[cfg(test)]
    pub(crate) fn memory_only(data_dir: &Path) -> DeskResult<Self> {
        Self::with_backend(data_dir, Box::new(TestCredentials::default()))
    }
}

fn validate_id(id: &str) -> DeskResult<()> {
    if id.is_empty()
        || id.len() > 120
        || !id
            .bytes()
            .all(|value| value.is_ascii_alphanumeric() || value == b'_' || value == b'-')
    {
        return Err("Invalid profile identifier.".into());
    }
    Ok(())
}

#[cfg(test)]
#[derive(Default)]
struct TestCredentials {
    enabled: bool,
    values: std::sync::Mutex<HashMap<String, String>>,
}

#[cfg(test)]
impl CredentialBackend for TestCredentials {
    fn available(&self) -> bool {
        self.enabled
    }
    fn get(&self, id: &str) -> DeskResult<Option<String>> {
        Ok(self.values.lock().unwrap().get(id).cloned())
    }
    fn set(&self, id: &str, value: &str) -> DeskResult<()> {
        self.values.lock().unwrap().insert(id.into(), value.into());
        Ok(())
    }
    fn delete(&self, id: &str) -> DeskResult<()> {
        self.values.lock().unwrap().remove(id);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn session_only_keys_never_create_plaintext_files() {
        let directory = tempfile::tempdir().unwrap();
        let mut store = SecretStore::memory_only(directory.path()).unwrap();
        assert!(!store.available());
        store.set("profile", "a-private-value", false).unwrap();
        assert_eq!(
            store.get("profile").unwrap().as_deref(),
            Some("a-private-value")
        );
        assert!(store.has("profile"));
        assert!(store.set("other", "value", true).is_err());
        assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 0);
        store.delete("profile").unwrap();
        assert_eq!(store.get("profile").unwrap(), None);
    }

    #[test]
    fn persistent_and_session_keys_replace_each_other_in_the_native_store() {
        let directory = tempfile::tempdir().unwrap();
        let mut store = SecretStore::with_backend(
            directory.path(),
            Box::new(TestCredentials {
                enabled: true,
                ..Default::default()
            }),
        )
        .unwrap();
        store.set("profile", "persistent", true).unwrap();
        assert_eq!(
            store.backend.get("profile").unwrap().as_deref(),
            Some("persistent")
        );
        store.set("profile", "temporary", false).unwrap();
        assert_eq!(store.backend.get("profile").unwrap(), None);
        assert_eq!(store.get("profile").unwrap().as_deref(), Some("temporary"));
        store.set("profile", "replacement", true).unwrap();
        assert!(!store.session.contains_key("profile"));
        assert_eq!(
            store.get("profile").unwrap().as_deref(),
            Some("replacement")
        );
    }

    #[test]
    fn legacy_ciphertext_is_preserved_and_never_treated_as_a_usable_key() {
        let directory = tempfile::tempdir().unwrap();
        let legacy = r#"{"profile":"electron-encrypted-data"}"#;
        fs::write(directory.path().join("credentials.json"), legacy).unwrap();
        let mut store = SecretStore::memory_only(directory.path()).unwrap();
        assert!(!store.has("profile"));
        assert_eq!(store.get("profile").unwrap(), None);
        assert!(!store.warnings().is_empty());
        store.set("profile", "new-session-key", false).unwrap();
        assert!(store.warnings().is_empty());
        assert_eq!(
            fs::read_to_string(directory.path().join("credentials.json")).unwrap(),
            legacy
        );
    }
}
