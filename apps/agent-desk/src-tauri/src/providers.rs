use crate::launch_plan::validate_profile_compatibility;
use crate::secrets::SecretStore;
use crate::types::{DeskResult, ModelCatalog, ModelInfo, ProviderProfile, ProviderStatus};
use chrono::{SecondsFormat, Utc};
use regex::Regex;
use reqwest::Url;
use reqwest::blocking::Client;
use reqwest::header::{ACCEPT, AUTHORIZATION, HeaderMap, HeaderValue};
use serde_json::Value;
use std::collections::HashMap;
use std::io::Read;
use std::sync::{Arc, Mutex, OnceLock};
use std::time::{Duration, Instant};

const CATALOG_LIMIT: usize = 4 * 1024 * 1024;
const AGENTS: [&str; 4] = ["claude", "codex", "gemini", "antigravity"];

pub fn endpoint(value: &str) -> DeskResult<Url> {
    let url = Url::parse(value).map_err(|_| "Enter a complete HTTP or HTTPS endpoint URL.")?;
    if !["http", "https"].contains(&url.scheme())
        || url.host_str().is_none()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
    {
        return Err(
            "Endpoints must use HTTP or HTTPS without credentials, a query, or a fragment.".into(),
        );
    }
    Ok(url)
}

pub fn validate_profile(mut profile: ProviderProfile) -> DeskResult<ProviderProfile> {
    static ENV_NAME: OnceLock<Regex> = OnceLock::new();
    static SECRET_NAME: OnceLock<Regex> = OnceLock::new();
    static SECRET_VALUE: OnceLock<Regex> = OnceLock::new();
    static RUNTIME_ENV: OnceLock<Regex> = OnceLock::new();
    let env_name = ENV_NAME.get_or_init(|| Regex::new(r"^[A-Za-z_][A-Za-z0-9_]*$").unwrap());
    let secret_name = SECRET_NAME.get_or_init(|| {
        Regex::new(r"(?i)(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTHORIZATION)").unwrap()
    });
    let secret_value = SECRET_VALUE.get_or_init(|| {
        Regex::new(r"(?:sk-(?:or-|ant-)?[A-Za-z0-9_-]{12,}|-----BEGIN .*PRIVATE KEY-----)").unwrap()
    });
    let runtime_env = RUNTIME_ENV.get_or_init(|| Regex::new(r"(?i)^(?:NODE_OPTIONS|ELECTRON_|LD_|DYLD_|PATH$|PATHEXT$|HOME$|USERPROFILE$|SHELL$|COMSPEC$|BASH_ENV$|ENV$)").unwrap());
    if profile.id.is_empty()
        || profile.id.len() > 80
        || !profile.id.as_bytes()[0].is_ascii_alphanumeric()
        || !profile
            .id
            .bytes()
            .all(|value| value.is_ascii_alphanumeric() || value == b'_' || value == b'-')
    {
        return Err("Use a valid profile identifier with at most 80 letters, numbers, hyphens or underscores.".into());
    }
    profile.name = profile.name.trim().to_owned();
    if profile.name.is_empty() || profile.name.len() > 100 {
        return Err("A profile needs a name of at most 100 characters.".into());
    }
    if !AGENTS.contains(&profile.agent.as_str()) {
        return Err("Unknown coding agent.".into());
    }
    if !["native", "local-proxy", "openrouter", "deepseek", "custom"]
        .contains(&profile.provider.as_str())
    {
        return Err("Unknown model provider.".into());
    }
    if !["native", "anthropic", "openai-responses", "gemini"].contains(&profile.route.as_str()) {
        return Err("Unknown provider protocol.".into());
    }
    if let Some(base) = &profile.base_url {
        if base.len() > 2048 {
            return Err("The endpoint URL is too long.".into());
        }
        profile.base_url = Some(endpoint(base)?.as_str().trim_end_matches('/').to_owned());
    }
    if profile.route == "native" && profile.provider != "native" {
        return Err("Choose an API route for a non-native provider.".into());
    }
    if profile.route != "native" && profile.base_url.is_none() {
        return Err("This route needs an endpoint URL.".into());
    }
    validate_profile_compatibility(&profile)?;
    for model in [
        &profile.model,
        &profile.small_model,
        &profile.subagent_model,
    ]
    .into_iter()
    .flatten()
    {
        if model.len() > 200 {
            return Err("Model identifiers may contain at most 200 characters.".into());
        }
    }
    if profile
        .effort
        .as_ref()
        .is_some_and(|value| value.len() > 32)
    {
        return Err("The reasoning effort value is too long.".into());
    }
    if profile
        .settings_file
        .as_ref()
        .is_some_and(|value| value.len() > 4096)
    {
        return Err("The settings overlay path is too long.".into());
    }
    if profile
        .api_key_env
        .as_ref()
        .is_some_and(|value| !env_name.is_match(value) || value.len() > 160)
    {
        return Err("Use a valid API key environment variable name.".into());
    }
    if profile
        .auth_mode
        .as_ref()
        .is_some_and(|value| !["bearer", "api-key"].contains(&value.as_str()))
    {
        return Err("Unknown authentication mode.".into());
    }
    if profile
        .context_window
        .is_some_and(|value| !(1024..=10_000_000).contains(&value))
    {
        return Err("The context window must be between 1024 and 10000000 tokens.".into());
    }
    if profile.env.len() > 80 {
        return Err("A profile may contain at most 80 extra environment settings.".into());
    }
    for (name, value) in &profile.env {
        if ["CLAUDE_CONFIG_DIR", "CODEX_HOME", "GEMINI_CLI_HOME"]
            .iter()
            .any(|candidate| name.eq_ignore_ascii_case(candidate))
        {
            return Err("Agent home overrides belong to the app environment, not individual profiles, so resumed sessions keep their original history store.".into());
        }
        if runtime_env.is_match(name) {
            return Err("Runtime, shell, and executable search environment variables cannot be overridden in a launch profile.".into());
        }
        if !env_name.is_match(name)
            || name == "__proto__"
            || value.len() > 4096
            || value.contains('\0')
        {
            return Err("Invalid environment setting.".into());
        }
        if (secret_name.is_match(name) && !value.is_empty()) || secret_value.is_match(value) {
            return Err("Use the API key field or an environment variable reference for credentials, not extra environment settings.".into());
        }
    }
    for value in std::iter::once(&profile.name).chain(
        [
            &profile.base_url,
            &profile.model,
            &profile.small_model,
            &profile.subagent_model,
            &profile.effort,
            &profile.settings_file,
        ]
        .into_iter()
        .flatten(),
    ) {
        if value.contains('\0') || secret_value.is_match(value) {
            return Err("Profile fields must not contain credentials or null characters.".into());
        }
    }
    profile.has_secret = None;
    Ok(profile)
}

pub fn default_profiles() -> Vec<ProviderProfile> {
    let mut profiles: Vec<_> = [
        ("claude", "Claude · native configuration"),
        ("codex", "Codex · native configuration"),
        ("gemini", "Gemini · native"),
        ("antigravity", "Antigravity · native"),
    ]
    .into_iter()
    .map(|(agent, name)| ProviderProfile {
        id: format!("{agent}-native"),
        name: name.into(),
        agent: agent.into(),
        provider: "native".into(),
        route: "native".into(),
        ..Default::default()
    })
    .collect();
    profiles.push(ProviderProfile {
        id: "claude-local-proxy".into(),
        name: "Claude · local proxy".into(),
        agent: "claude".into(),
        provider: "local-proxy".into(),
        route: "anthropic".into(),
        base_url: Some("http://127.0.0.1:18765".into()),
        auth_mode: Some("bearer".into()),
        env: [
            (
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC".into(),
                "1".into(),
            ),
            (
                "CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK".into(),
                "1".into(),
            ),
            (
                "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY".into(),
                "1".into(),
            ),
        ]
        .into(),
        ..Default::default()
    });
    profiles.push(ProviderProfile {
        id: "claude-openrouter".into(),
        name: "Claude · OpenRouter".into(),
        agent: "claude".into(),
        provider: "openrouter".into(),
        route: "anthropic".into(),
        base_url: Some("https://openrouter.ai/api".into()),
        api_key_env: Some("OPENROUTER_API_KEY".into()),
        auth_mode: Some("bearer".into()),
        env: [(
            "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY".into(),
            "1".into(),
        )]
        .into(),
        ..Default::default()
    });
    profiles.push(ProviderProfile {
        id: "claude-deepseek".into(),
        name: "Claude · DeepSeek".into(),
        agent: "claude".into(),
        provider: "deepseek".into(),
        route: "anthropic".into(),
        base_url: Some("https://api.deepseek.com/anthropic".into()),
        api_key_env: Some("DEEPSEEK_API_KEY".into()),
        auth_mode: Some("bearer".into()),
        ..Default::default()
    });
    profiles
}

pub struct ProviderService {
    client: Client,
    secrets: Arc<Mutex<SecretStore>>,
}

impl ProviderService {
    pub fn new(secrets: Arc<Mutex<SecretStore>>) -> DeskResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(10))
            .connect_timeout(Duration::from_secs(10))
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .map_err(|_| "Could not initialize provider connections.")?;
        Ok(Self { client, secrets })
    }

    fn key(&self, profile: &ProviderProfile) -> DeskResult<Option<String>> {
        let saved = self
            .secrets
            .lock()
            .map_err(|_| "The credential store is unavailable.")?
            .get(&profile.id)?;
        Ok(saved.or_else(|| {
            profile
                .api_key_env
                .as_ref()
                .and_then(|name| std::env::var(name).ok())
                .filter(|value| !value.is_empty())
        }))
    }

    fn request(
        &self,
        url: &str,
        profile: &ProviderProfile,
        public: bool,
        force_bearer: bool,
    ) -> DeskResult<Value> {
        let url = endpoint(url)?;
        let key = if public { None } else { self.key(profile)? };
        let headers = request_headers(profile, key.as_deref(), force_bearer)?;
        let mut response = self
            .client
            .get(url)
            .headers(headers)
            .send()
            .map_err(|error| {
                if error.is_timeout() {
                    "The endpoint request reached its timeout.".to_owned()
                } else {
                    "Could not reach the selected endpoint. Check its URL and network connection."
                        .to_owned()
                }
            })?;
        if !response.status().is_success() {
            return Err(http_error(response.status().as_u16()));
        }
        if response
            .content_length()
            .is_some_and(|size| size > CATALOG_LIMIT as u64)
        {
            return Err("Model catalogue response is too large.".into());
        }
        let mut bytes = Vec::with_capacity(
            response
                .content_length()
                .unwrap_or(0)
                .min(CATALOG_LIMIT as u64) as usize,
        );
        response
            .by_ref()
            .take((CATALOG_LIMIT + 1) as u64)
            .read_to_end(&mut bytes)
            .map_err(|_| "Could not read the endpoint response before its timeout.")?;
        if bytes.len() > CATALOG_LIMIT {
            return Err("Model catalogue response is too large.".into());
        }
        serde_json::from_slice(&bytes).map_err(|_| "The endpoint did not return valid JSON.".into())
    }

    pub fn catalog_url(&self, profile: &ProviderProfile) -> DeskResult<String> {
        catalog_url(profile)
    }

    pub fn models(&self, profile: &ProviderProfile) -> DeskResult<ModelCatalog> {
        let started = Instant::now();
        if profile.route == "native" {
            return Ok(ModelCatalog { models: Vec::new(), source: "Native CLI".into(), verified_at: now(), latency_ms: 0, warnings: vec!["Native profiles use the installed CLI’s model picker, configuration and environment. Its provider can be a subscription, direct API or gateway. A model ID can still be saved in this profile.".into()] });
        }
        let source = catalog_url(profile)?;
        let public = profile.provider == "openrouter"
            && endpoint(&source)?.host_str() == Some("openrouter.ai");
        let response = self.request(&source, profile, public, profile.provider == "deepseek")?;
        let (models, warnings) = normalize_catalog(response, public)?;
        Ok(ModelCatalog {
            models,
            source,
            verified_at: now(),
            latency_ms: started.elapsed().as_millis() as u64,
            warnings,
        })
    }

    pub fn probe(&self, profile: &ProviderProfile) -> ProviderStatus {
        let started = Instant::now();
        let outcome = (|| -> DeskResult<(String, Option<usize>)> {
            if profile.route == "native" {
                return Err("Native profiles inherit the installed CLI’s configuration, provider and authentication. Open the agent and use its account/status command to verify access.".into());
            }
            let base = endpoint(profile.base_url.as_deref().unwrap_or_default())?;
            if profile.provider == "local-proxy" {
                let response = self.request(
                    &format!("{}/healthz", base.as_str().trim_end_matches('/')),
                    profile,
                    true,
                    false,
                )?;
                if response.get("ok").and_then(Value::as_bool) != Some(true) {
                    return Err("The proxy did not return a successful health check.".into());
                }
                return Ok((
                    "Proxy is running. This liveness check does not verify its upstream accounts."
                        .into(),
                    None,
                ));
            }
            if profile.provider == "openrouter" && base.host_str() == Some("openrouter.ai") {
                if self.key(profile)?.is_none() {
                    return Err("Add an API key or set its environment variable before testing authenticated access.".into());
                }
                let response = self.request(
                    &format!("{}/api/v1/key", base.origin().ascii_serialization()),
                    profile,
                    false,
                    true,
                )?;
                if response.get("data").is_none() {
                    return Err("The endpoint returned an unexpected account response.".into());
                }
                return Ok((
                    "OpenRouter accepted this API key. No generation was requested.".into(),
                    None,
                ));
            }
            let catalog = self.models(profile)?;
            Ok(("The model catalogue responded. A generation was not requested; model access and tool compatibility can still differ.".into(), Some(catalog.models.len())))
        })();
        let (ok, message, model_count) = match outcome {
            Ok((message, count)) => (true, message, count),
            Err(message) => (false, message, None),
        };
        ProviderStatus {
            ok,
            message,
            model_count,
            checked_at: now(),
            latency_ms: started.elapsed().as_millis() as u64,
        }
    }

    pub fn proxy_monitor(&self, profile: &ProviderProfile) -> DeskResult<Value> {
        if profile.provider != "local-proxy" {
            return Err("The monitor is available for a local proxy profile.".into());
        }
        let url = endpoint(profile.base_url.as_deref().unwrap_or_default())?;
        self.request(
            &format!("{}/monitor", url.as_str().trim_end_matches('/')),
            profile,
            true,
            false,
        )
    }
}

fn now() -> String {
    Utc::now().to_rfc3339_opts(SecondsFormat::Millis, true)
}

pub fn catalog_url(profile: &ProviderProfile) -> DeskResult<String> {
    let url = endpoint(profile.base_url.as_deref().unwrap_or_default())?;
    if profile.provider == "openrouter" && url.host_str() == Some("openrouter.ai") {
        return Ok(format!(
            "{}/api/v1/models",
            url.origin().ascii_serialization()
        ));
    }
    if profile.provider == "deepseek" && url.host_str() == Some("api.deepseek.com") {
        return Ok(format!("{}/models", url.origin().ascii_serialization()));
    }
    static VERSION: OnceLock<Regex> = OnceLock::new();
    let base = url.as_str().trim_end_matches('/');
    Ok(format!(
        "{base}{}",
        if VERSION
            .get_or_init(|| Regex::new(r"/v\d+(?:beta)?$").unwrap())
            .is_match(base)
        {
            "/models"
        } else {
            "/v1/models"
        }
    ))
}

fn request_headers(
    profile: &ProviderProfile,
    secret: Option<&str>,
    force_bearer: bool,
) -> DeskResult<HeaderMap> {
    let mut headers = HeaderMap::new();
    headers.insert(ACCEPT, HeaderValue::from_static("application/json"));
    if let Some(secret) = secret {
        let name = if profile.route == "gemini" {
            "x-goog-api-key"
        } else if profile.auth_mode.as_deref() == Some("api-key") && !force_bearer {
            "x-api-key"
        } else {
            AUTHORIZATION.as_str()
        };
        let value = if name == AUTHORIZATION.as_str() {
            format!("Bearer {secret}")
        } else {
            secret.to_owned()
        };
        let mut value = HeaderValue::from_str(&value)
            .map_err(|_| "The selected API key contains invalid header characters.")?;
        value.set_sensitive(true);
        headers.insert(
            reqwest::header::HeaderName::from_bytes(name.as_bytes()).unwrap(),
            value,
        );
    }
    if profile.route == "anthropic" {
        headers.insert("anthropic-version", HeaderValue::from_static("2023-06-01"));
    }
    Ok(headers)
}

fn http_error(status: u16) -> String {
    if status == 401 || status == 403 {
        format!(
            "Authentication was rejected (HTTP {status}). Check the selected endpoint and API key."
        )
    } else {
        format!("Endpoint returned HTTP {status}.")
    }
}

fn number(value: Option<&Value>) -> Option<f64> {
    value
        .and_then(|value| {
            value
                .as_f64()
                .or_else(|| value.as_str().and_then(|text| text.parse().ok()))
        })
        .filter(|value| value.is_finite() && *value >= 0.0)
}

fn normalize_catalog(response: Value, public: bool) -> DeskResult<(Vec<ModelInfo>, Vec<String>)> {
    let entries = response
        .get("data")
        .or_else(|| response.get("models"))
        .and_then(Value::as_array)
        .ok_or("Endpoint did not return a supported model catalogue.")?;
    let mut models = Vec::new();
    let mut positions: HashMap<String, usize> = HashMap::new();
    for entry in entries.iter().take(5000) {
        let Some(id) = entry.get("id").and_then(Value::as_str).or_else(|| {
            entry
                .get("name")
                .and_then(Value::as_str)
                .map(|name| name.strip_prefix("models/").unwrap_or(name))
        }) else {
            continue;
        };
        if id.is_empty() || id.len() > 300 {
            continue;
        }
        let context = number(
            entry
                .get("context_length")
                .or_else(|| entry.get("context_window"))
                .or_else(|| entry.get("inputTokenLimit")),
        );
        let pricing = entry.get("pricing");
        let input = number(pricing.and_then(|value| value.get("prompt")));
        let output = number(pricing.and_then(|value| value.get("completion")));
        let name = entry
            .get("display_name")
            .or_else(|| entry.get("displayName"))
            .or_else(|| entry.get("name"))
            .and_then(Value::as_str)
            .unwrap_or(id);
        let model = ModelInfo {
            id: id.into(),
            name: name.chars().take(300).collect(),
            context_window: context
                .filter(|value| *value > 0.0 && *value <= u64::MAX as f64)
                .map(|value| value as u64),
            input_price: input
                .map(|value| value * 1_000_000.0)
                .filter(|value| value.is_finite()),
            output_price: output
                .map(|value| value * 1_000_000.0)
                .filter(|value| value.is_finite()),
            free: input
                .zip(output)
                .map(|(input, output)| input == 0.0 && output == 0.0),
        };
        if let Some(index) = positions.get(id) {
            models[*index] = model;
        } else {
            positions.insert(id.to_owned(), models.len());
            models.push(model);
        }
    }
    let mut warnings = Vec::new();
    if response.get("has_more").and_then(Value::as_bool) == Some(true) || entries.len() > 5000 {
        warnings.push(
            "The endpoint returned a partial catalogue. You can enter an exact model ID manually."
                .into(),
        );
    }
    if public {
        warnings.push("OpenRouter’s public catalogue is not proof of tool compatibility or access on your account. Prices shown are per million tokens.".into());
    }
    Ok((models, warnings))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn documented_gateways_and_native_defaults_stay_distinct() {
        let profiles = default_profiles();
        assert_eq!(
            catalog_url(&profiles[4]).unwrap(),
            "http://127.0.0.1:18765/v1/models"
        );
        assert_eq!(
            catalog_url(&profiles[5]).unwrap(),
            "https://openrouter.ai/api/v1/models"
        );
        assert_eq!(
            catalog_url(&profiles[6]).unwrap(),
            "https://api.deepseek.com/models"
        );
        assert!(profiles.iter().all(|profile| profile.model.is_none()));
        for profile in profiles {
            validate_profile(profile).unwrap();
        }
    }

    #[test]
    fn catalog_prices_free_flags_context_and_partial_results_are_honest() {
        let (models, warnings) = normalize_catalog(serde_json::json!({"has_more":true,"data":[
            {"id":"vendor/coder","context_length":200000,"pricing":{"prompt":"0.000002","completion":"0.000008"}},
            {"id":"vendor/free","pricing":{"prompt":"0","completion":"0"}},
            {"id":"vendor/unknown"}
        ]}), true).unwrap();
        assert_eq!(models[0].input_price, Some(2.0));
        assert_eq!(models[0].output_price, Some(8.0));
        assert_eq!(models[0].context_window, Some(200000));
        assert_eq!(models[1].free, Some(true));
        assert_eq!(models[2].free, None);
        assert_eq!(warnings.len(), 2);
        assert!(normalize_catalog(serde_json::json!({"hello":1}), false).is_err());
    }

    #[test]
    fn public_catalogs_have_no_credential_and_authentication_headers_are_sensitive() {
        let profile = &default_profiles()[5];
        assert!(
            !request_headers(profile, None, false)
                .unwrap()
                .contains_key(AUTHORIZATION)
        );
        let headers = request_headers(profile, Some("private-value"), false).unwrap();
        assert_eq!(headers.get(AUTHORIZATION).unwrap(), "Bearer private-value");
        assert!(headers.get(AUTHORIZATION).unwrap().is_sensitive());
        assert!(http_error(401).contains("401"));
    }

    #[test]
    fn profile_validation_rejects_secrets_runtime_changes_and_incompatible_routes() {
        for name in ["OPENROUTER_API_KEY", "NODE_OPTIONS", "CODEX_HOME"] {
            let mut profile = default_profiles().remove(0);
            profile.env.insert(name.into(), "value".into());
            assert!(validate_profile(profile).is_err());
        }
        let mut profile = default_profiles().remove(0);
        profile.provider = "custom".into();
        profile.route = "openai-responses".into();
        profile.base_url = Some("https://example.com".into());
        assert!(validate_profile(profile).is_err());
        assert!(endpoint("https://user:secret@example.com").is_err());
        assert!(endpoint("https://example.com?key=secret").is_err());
    }
}
