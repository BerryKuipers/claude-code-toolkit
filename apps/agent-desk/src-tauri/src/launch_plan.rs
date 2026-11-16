use crate::types::{DeskResult, LaunchRequest, ProviderProfile, SessionRecord};
use reqwest::Url;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct LaunchPlan {
    pub args: Vec<String>,
    pub env: HashMap<String, String>,
    pub cwd: String,
}

pub fn validate_profile_compatibility(profile: &ProviderProfile) -> DeskResult<()> {
    let valid = match profile.agent.as_str() {
        "claude" => matches!(profile.route.as_str(), "native" | "anthropic"),
        "codex" => matches!(profile.route.as_str(), "native" | "openai-responses"),
        "gemini" | "antigravity" => matches!(profile.route.as_str(), "native" | "gemini"),
        _ => false,
    };
    if !valid {
        return Err(format!(
            "{} cannot use the {} protocol. Choose a compatible connection.",
            profile.agent, profile.route
        ));
    }
    if profile.route != "native" {
        let url = Url::parse(
            profile
                .base_url
                .as_deref()
                .filter(|v| !v.is_empty())
                .ok_or("This connection needs a base URL.")?,
        )
        .map_err(|_| "Use a valid HTTP(S) base URL.")?;
        if !matches!(url.scheme(), "http" | "https")
            || !url.username().is_empty()
            || url.password().is_some()
            || url.query().is_some()
            || url.fragment().is_some()
        {
            return Err(
                "Use an HTTP(S) base URL without embedded credentials, query or fragment.".into(),
            );
        }
        if url.scheme() == "http"
            && !matches!(
                url.host_str(),
                Some("localhost" | "127.0.0.1" | "[::1]" | "::1")
            )
            && profile.provider != "custom"
        {
            return Err("Remote provider connections require HTTPS. Select Custom only for an intentional private-network endpoint.".into());
        }
    }
    Ok(())
}

pub fn blocked_env(name: &str) -> bool {
    let upper = name.to_uppercase();
    upper.starts_with("ELECTRON_")
        || upper.starts_with("LD_")
        || upper.starts_with("DYLD_")
        || matches!(
            upper.as_str(),
            "NODE_OPTIONS"
                | "BASH_ENV"
                | "ENV"
                | "COMSPEC"
                | "SHELL"
                | "PATH"
                | "PATHEXT"
                | "HOME"
                | "USERPROFILE"
                | "CLAUDE_CONFIG_DIR"
                | "CODEX_HOME"
                | "GEMINI_CLI_HOME"
        )
}

pub fn clean_environment(parent: &HashMap<String, String>) -> HashMap<String, String> {
    parent
        .iter()
        .filter(|(name, _)| {
            !name.starts_with("ELECTRON_")
                && !matches!(
                    name.as_str(),
                    "NODE_OPTIONS" | "CLAUDECODE" | "CLAUDE_CODE_ENTRYPOINT" | "AGENT_DESK_API_KEY"
                )
        })
        .map(|(k, v)| (k.clone(), v.clone()))
        .collect()
}

pub fn build_launch_plan(
    request: &LaunchRequest,
    profile: &ProviderProfile,
    parent: &HashMap<String, String>,
    secret: Option<&str>,
    session: Option<&SessionRecord>,
) -> DeskResult<LaunchPlan> {
    validate_profile_compatibility(profile)?;
    if request.agent != profile.agent {
        return Err("The selected profile belongs to a different agent.".into());
    }
    if request.session_id.is_some() && !session.is_some_and(|s| s.agent == request.agent) {
        return Err(
            "The selected session no longer exists for this agent. Refresh the session list."
                .into(),
        );
    }
    if let Some(session) = session {
        if !session.resumable {
            return Err(session
                .resume_note
                .clone()
                .unwrap_or_else(|| "This session cannot be resumed directly.".into()));
        }
        if session.native_id.is_empty()
            || session.native_id.starts_with('-')
            || session.native_id.chars().any(char::is_control)
            || session.native_id.len() > 512
        {
            return Err("This session has an invalid native identifier.".into());
        }
    }
    let mut env = clean_environment(parent);
    if request.agent == "claude" && profile.route != "native" {
        for key in [
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL",
            "CLAUDE_CODE_SUBAGENT_MODEL",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
            "CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK",
            "CLAUDE_PROVIDER",
            "CLAUDE_PROXY_ACTIVE",
            "CLAUDE_PROXY_URL",
        ] {
            env.remove(key);
        }
    } else if matches!(request.agent.as_str(), "gemini" | "antigravity")
        && profile.route != "native"
    {
        for key in ["GOOGLE_GEMINI_BASE_URL", "GEMINI_API_KEY", "GOOGLE_API_KEY"] {
            env.remove(key);
        }
    }
    for (key, value) in &profile.env {
        let mut chars = key.chars();
        if !chars
            .next()
            .is_some_and(|c| c.is_ascii_alphabetic() || c == '_')
            || !chars.all(|c| c.is_ascii_alphanumeric() || c == '_')
            || blocked_env(key)
        {
            return Err(format!(
                "The environment variable '{key}' cannot be set by a profile."
            ));
        }
        if value.contains('\0') {
            return Err(format!(
                "The environment variable '{key}' contains an invalid character."
            ));
        }
        env.insert(key.clone(), value.clone());
    }
    let key = secret.filter(|v| !v.is_empty()).or_else(|| {
        profile
            .api_key_env
            .as_ref()
            .and_then(|name| parent.get(name))
            .filter(|v| !v.is_empty())
            .map(String::as_str)
    });
    let mut args = Vec::new();
    let cwd = session
        .map(|s| s.project_path.as_str())
        .unwrap_or(&request.project_path)
        .to_string();
    if cwd.is_empty() || cwd.contains('\0') {
        return Err("Choose a project folder before starting a session.".into());
    }
    if request
        .prompt
        .as_ref()
        .is_some_and(|s| s.len() > 200_000 || s.contains('\0'))
    {
        return Err("The initial prompt is too large or contains an invalid character.".into());
    }
    let mut pair = |flag: &str, value: &str| {
        args.push(flag.to_string());
        args.push(value.to_string());
    };
    match request.agent.as_str() {
        "claude" => {
            if let Some(session) = session {
                pair("--resume", &session.native_id);
            }
            if let Some(model) = profile.model.as_deref().filter(|s| !s.is_empty()) {
                pair("--model", model);
            }
            if let Some(effort) = profile.effort.as_deref().filter(|s| !s.is_empty()) {
                pair("--effort", effort);
            }
            if let Some(settings) = profile.settings_file.as_deref().filter(|s| !s.is_empty()) {
                pair("--settings", settings);
            }
            if profile.route == "anthropic" {
                let base = profile.base_url.as_ref().unwrap();
                if key.is_none() && profile.provider != "local-proxy" {
                    return Err("Add an API key or set the API key environment variable for this connection.".into());
                }
                let api_key = profile.auth_mode.as_deref() == Some("api-key");
                env.insert("ANTHROPIC_BASE_URL".into(), base.clone());
                env.insert(
                    "ANTHROPIC_API_KEY".into(),
                    if api_key { key.unwrap_or("") } else { "" }.into(),
                );
                env.insert(
                    "ANTHROPIC_AUTH_TOKEN".into(),
                    if api_key {
                        ""
                    } else {
                        key.unwrap_or(if profile.provider == "local-proxy" {
                            "unused"
                        } else {
                            ""
                        })
                    }
                    .into(),
                );
                env.insert("CLAUDE_PROVIDER".into(), profile.provider.clone());
                env.insert("CLAUDE_PROXY_URL".into(), base.clone());
                for name in [
                    "CLAUDE_PROXY_ACTIVE",
                    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
                    "CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK",
                ] {
                    env.insert(name.into(), "1".into());
                }
                if let Some(model) = profile.model.as_ref().filter(|s| !s.is_empty()) {
                    for name in [
                        "ANTHROPIC_MODEL",
                        "ANTHROPIC_DEFAULT_OPUS_MODEL",
                        "ANTHROPIC_DEFAULT_SONNET_MODEL",
                    ] {
                        env.insert(name.into(), model.clone());
                    }
                }
            } else if let Some(key) = key {
                env.insert("ANTHROPIC_API_KEY".into(), key.into());
            }
            if let Some(model) = profile.small_model.as_ref().filter(|s| !s.is_empty()) {
                for name in [
                    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                    "ANTHROPIC_SMALL_FAST_MODEL",
                ] {
                    env.insert(name.into(), model.clone());
                }
            }
            if let Some(model) = profile.subagent_model.as_ref().filter(|s| !s.is_empty()) {
                env.insert("CLAUDE_CODE_SUBAGENT_MODEL".into(), model.clone());
            }
            if let Some(context) = profile.context_window {
                env.insert("CLAUDE_CODE_MAX_CONTEXT_TOKENS".into(), context.to_string());
            }
            if let Some(prompt) = request.prompt.as_deref().filter(|s| !s.is_empty()) {
                pair("--", prompt);
            }
        }
        "codex" => {
            if let Some(session) = session {
                pair("resume", &session.native_id);
            }
            if let Some(model) = profile.model.as_deref().filter(|s| !s.is_empty()) {
                pair("-m", model);
            }
            if let Some(effort) = profile.effort.as_deref().filter(|s| !s.is_empty()) {
                pair(
                    "-c",
                    &format!(
                        "model_reasoning_effort={}",
                        serde_json::to_string(effort).unwrap()
                    ),
                );
            }
            if profile.route == "openai-responses" {
                env.insert("AGENT_DESK_API_KEY".into(), key.unwrap_or("").into());
                pair("-c", "model_provider=\"agent_desk\"");
                pair("-c", "model_providers.agent_desk.name=\"Agent Desk\"");
                pair(
                    "-c",
                    &format!(
                        "model_providers.agent_desk.base_url={}",
                        serde_json::to_string(profile.base_url.as_deref().unwrap()).unwrap()
                    ),
                );
                pair("-c", "model_providers.agent_desk.wire_api=\"responses\"");
                if key.is_some() {
                    pair(
                        "-c",
                        "model_providers.agent_desk.env_key=\"AGENT_DESK_API_KEY\"",
                    );
                }
            }
            if let Some(prompt) = request.prompt.as_deref().filter(|s| !s.is_empty()) {
                pair("--", prompt);
            }
        }
        "gemini" | "antigravity" => {
            if let Some(session) = session {
                pair(
                    if request.agent == "gemini" {
                        "--resume"
                    } else {
                        "--conversation"
                    },
                    &session.native_id,
                );
            }
            if let Some(model) = profile.model.as_deref().filter(|s| !s.is_empty()) {
                pair("--model", model);
            }
            if request.agent == "antigravity"
                && let Some(effort) = profile.effort.as_deref().filter(|s| !s.is_empty())
            {
                pair("--effort", effort);
            }
            if profile.route == "gemini" {
                env.insert(
                    "GOOGLE_GEMINI_BASE_URL".into(),
                    profile.base_url.as_ref().unwrap().clone(),
                );
                env.insert(
                    "GEMINI_API_KEY".into(),
                    key.ok_or("This Gemini-compatible connection needs an API key.")?
                        .into(),
                );
            }
            if let Some(prompt) = request.prompt.as_deref().filter(|s| !s.is_empty()) {
                if request.agent == "gemini" {
                    args.push(format!("--prompt-interactive={prompt}"));
                } else {
                    pair("-i", prompt);
                }
            }
        }
        _ => return Err("Unknown agent.".into()),
    }
    env.insert("TERM".into(), "xterm-256color".into());
    env.insert("COLORTERM".into(), "truecolor".into());
    Ok(LaunchPlan { args, env, cwd })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn profile(agent: &str) -> ProviderProfile {
        ProviderProfile {
            id: "native".into(),
            name: "Native".into(),
            agent: agent.into(),
            provider: "native".into(),
            route: "native".into(),
            ..Default::default()
        }
    }
    fn request(agent: &str) -> LaunchRequest {
        LaunchRequest {
            agent: agent.into(),
            project_path: "/projects/with spaces".into(),
            ..Default::default()
        }
    }

    #[test]
    fn native_preserves_credentials_and_routing_together_without_mutating_parent() {
        let parent = HashMap::from([
            ("ANTHROPIC_BASE_URL".into(), "http://existing".into()),
            ("ANTHROPIC_AUTH_TOKEN".into(), "existing-key".into()),
            ("CLAUDECODE".into(), "1".into()),
        ]);
        let plan =
            build_launch_plan(&request("claude"), &profile("claude"), &parent, None, None).unwrap();
        assert_eq!(
            plan.env.get("ANTHROPIC_BASE_URL"),
            parent.get("ANTHROPIC_BASE_URL")
        );
        assert_eq!(
            plan.env.get("ANTHROPIC_AUTH_TOKEN"),
            parent.get("ANTHROPIC_AUTH_TOKEN")
        );
        assert!(!plan.env.contains_key("CLAUDECODE"));
        assert!(parent.contains_key("CLAUDECODE"));
    }

    #[test]
    fn prompts_are_single_arguments_and_native_defaults_do_not_bypass_agent_permissions() {
        for agent in ["claude", "codex", "gemini", "antigravity"] {
            assert!(
                build_launch_plan(
                    &request(agent),
                    &profile(agent),
                    &HashMap::new(),
                    None,
                    None
                )
                .unwrap()
                .args
                .is_empty()
            );
        }
        let prompt = "--dangerously-skip-permissions; $(touch /tmp/unwanted)";
        let request = LaunchRequest {
            prompt: Some(prompt.into()),
            ..request("claude")
        };
        assert_eq!(
            build_launch_plan(&request, &profile("claude"), &HashMap::new(), None, None)
                .unwrap()
                .args,
            vec!["--", prompt]
        );
    }

    #[test]
    fn direct_routing_requires_keys_and_cleans_stale_auth() {
        let mut p = profile("claude");
        p.provider = "openrouter".into();
        p.route = "anthropic".into();
        p.base_url = Some("https://openrouter.ai/api".into());
        assert!(
            build_launch_plan(&request("claude"), &p, &HashMap::new(), None, None)
                .unwrap_err()
                .contains("API key")
        );
        let plan = build_launch_plan(
            &request("claude"),
            &p,
            &HashMap::from([("ANTHROPIC_API_KEY".into(), "stale".into())]),
            Some("test-key"),
            None,
        )
        .unwrap();
        assert_eq!(plan.env["ANTHROPIC_AUTH_TOKEN"], "test-key");
        assert_eq!(plan.env["ANTHROPIC_API_KEY"], "");
        p.provider = "local-proxy".into();
        p.base_url = Some("http://127.0.0.1:18765".into());
        assert_eq!(
            build_launch_plan(&request("claude"), &p, &HashMap::new(), None, None)
                .unwrap()
                .env["ANTHROPIC_AUTH_TOKEN"],
            "unused"
        );
    }

    #[test]
    fn custom_codex_uses_secret_environment_reference_and_keeps_the_key_out_of_arguments() {
        let mut p = profile("codex");
        p.route = "openai-responses".into();
        p.provider = "custom".into();
        p.base_url = Some("https://example.test/v1".into());
        p.effort = Some("medium".into());
        let plan = build_launch_plan(
            &request("codex"),
            &p,
            &HashMap::new(),
            Some("test-secret"),
            None,
        )
        .unwrap();
        assert_eq!(plan.env["AGENT_DESK_API_KEY"], "test-secret");
        assert!(!plan.args.join(" ").contains("test-secret"));
        assert!(
            plan.args
                .contains(&"model_reasoning_effort=\"medium\"".into())
        );
    }

    #[test]
    fn environment_injection_and_store_overrides_are_rejected() {
        for name in [
            "NODE_OPTIONS",
            "PATH",
            "LD_PRELOAD",
            "CODEX_HOME",
            "CLAUDE_CONFIG_DIR",
            "GEMINI_CLI_HOME",
        ] {
            let mut p = profile("claude");
            p.env.insert(name.into(), "value".into());
            assert!(
                build_launch_plan(&request("claude"), &p, &HashMap::new(), None, None)
                    .unwrap_err()
                    .contains("cannot be set")
            );
        }
        let mut p = profile("claude");
        p.route = "openai-responses".into();
        assert!(validate_profile_compatibility(&p).is_err());
        p.route = "anthropic".into();
        p.base_url = Some("https://key:secret@example.test".into());
        assert!(validate_profile_compatibility(&p).is_err());
    }

    #[test]
    fn resume_uses_owned_native_session_and_rejects_flag_identifiers_or_imports() {
        let mut session = SessionRecord {
            native_id: "abc".into(),
            agent: "claude".into(),
            project_path: "/original/project".into(),
            resumable: true,
            ..Default::default()
        };
        let r = LaunchRequest {
            session_id: Some("owned-id".into()),
            ..request("claude")
        };
        let plan = build_launch_plan(
            &r,
            &profile("claude"),
            &HashMap::new(),
            None,
            Some(&session),
        )
        .unwrap();
        assert_eq!(plan.args, vec!["--resume", "abc"]);
        assert_eq!(plan.cwd, "/original/project");
        assert!(build_launch_plan(&r, &profile("claude"), &HashMap::new(), None, None).is_err());
        session.native_id = "--unsafe".into();
        assert!(
            build_launch_plan(
                &r,
                &profile("claude"),
                &HashMap::new(),
                None,
                Some(&session)
            )
            .is_err()
        );
        session.native_id = "abc".into();
        session.resumable = false;
        assert!(
            build_launch_plan(
                &r,
                &profile("claude"),
                &HashMap::new(),
                None,
                Some(&session)
            )
            .is_err()
        );
    }

    #[test]
    fn gemini_prompt_keeps_the_agent_interactive() {
        let r = LaunchRequest {
            prompt: Some("review this".into()),
            ..request("gemini")
        };
        assert_eq!(
            build_launch_plan(&r, &profile("gemini"), &HashMap::new(), None, None)
                .unwrap()
                .args,
            vec!["--prompt-interactive=review this"]
        );
    }
}
