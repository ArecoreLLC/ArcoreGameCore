use serde::{Deserialize, Serialize};
use std::{path::Path, process::Command};

/// A repository observation at import, never proof of a screenshot's build.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Iteration {
    pub observed_at: String,
    pub basis: String,
    pub revision: Option<String>,
    pub modified: Option<bool>,
    pub status: String,
}

fn git(path: &Path, args: &[&str]) -> Option<String> {
    let mut command = Command::new("git");
    command.arg("--no-optional-locks").arg("-C").arg(path).args(args);
    // A parent MCP client's Git environment must not redirect the game checkout.
    for (key, _) in std::env::vars_os() {
        if key.to_string_lossy().starts_with("GIT_") { command.env_remove(key); }
    }
    #[cfg(windows)] {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    let output = command.output().ok()?;
    output.status.success().then(|| String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

pub fn observe(path: Option<&str>) -> Iteration {
    let mut result = Iteration {
        observed_at: chrono::Utc::now().to_rfc3339(), basis: "import".into(),
        revision: None, modified: None, status: "unavailable".into(),
    };
    let Some(path) = path.filter(|p| !p.trim().is_empty()).map(Path::new) else { return result };
    if !path.is_dir() || git(path, &["rev-parse", "--is-inside-work-tree"]).as_deref() != Some("true") {
        return result;
    }
    result.revision = git(path, &["rev-parse", "--verify", "HEAD"]);
    result.modified = git(path, &["status", "--porcelain=v1", "--untracked-files=normal"])
        .map(|s| !s.is_empty());
    result.status = if result.revision.is_none() { "no-commit" }
        else if result.modified.is_none() { "status-unavailable" } else { "available" }.into();
    result
}
