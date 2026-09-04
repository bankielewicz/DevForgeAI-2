//! `devforge`: the trust-boundary entry point of the DevForge release
//! (corrective-spec-002 CS-8 and CS-9.3; INSTALLED-LAYOUT.md v2).
//!
//! A statically linked binary (x86_64-unknown-linux-musl, no dynamic loader,
//! so `LD_PRELOAD`/`LD_AUDIT` never run code in this process), no shell, no
//! third-party crates. It determines the release root from the running
//! executable, and:
//!
//! * `checkpoint validate …` execs `/usr/bin/python3 -I -B -P <root>/bin/devforge-checkpoint.py`
//!   with `env_clear()` and exactly `PATH`, `LC_ALL`, `LANG`; the Python
//!   validator inside the release is a temporary delegate (D-CP00-13).
//! * `checkpoint attest …` mints the root-owned closure attestation the
//!   validator's rule S14 consumes, at the fixed location under
//!   `/var/lib/devforge/attest`, from a sanitized `/usr/bin/git`.
//!
//! STAGED CANDIDATE source in DevForgeAI; the installed copy is built and
//! pinned by DevForge (`launcher/BUILD-DIGEST.txt`).

mod sha256;

use std::env;
use std::fs;
use std::io::Write;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

const USAGE: &str = "usage: devforge checkpoint validate --plan <dir> [--diff <base>..<head>] [--json]\n\
       devforge checkpoint attest --repo <checkout> --plan <plan path> --checkpoint <id> \
--base <sha> --head <sha> --authority <id> --review <reference> [--dry-run]";
const ATTEST_ROOT: &str = "/var/lib/devforge/attest";
const ATTESTATION_FORMAT: &str = "devforge-closure-attestation/v1";

fn main() {
    std::process::exit(run());
}

fn usage(message: &str) -> i32 {
    if !message.is_empty() {
        eprintln!("devforge: {message}");
    }
    eprintln!("{USAGE}");
    2
}

fn run() -> i32 {
    let args: Vec<String> = env::args().collect();
    let argv0 = args.first().cloned().unwrap_or_default();
    if !argv0.starts_with('/') {
        eprintln!("devforge: invoke by absolute path (got '{argv0}')");
        return 2;
    }
    let exe = match fs::read_link("/proc/self/exe") {
        Ok(path) if path.is_absolute() => path,
        Ok(path) => {
            eprintln!("devforge: /proc/self/exe is not absolute: {}", path.display());
            return 3;
        }
        Err(err) => {
            eprintln!("devforge: cannot read /proc/self/exe: {err}");
            return 3;
        }
    };
    let bin = match exe.parent() {
        Some(dir) if dir.file_name().map(|n| n == "bin").unwrap_or(false) => dir,
        _ => {
            eprintln!("devforge: the executable must live in <root>/bin (running as {})", exe.display());
            return 3;
        }
    };
    let root = match bin.parent() {
        Some(root) => root.to_path_buf(),
        None => {
            eprintln!("devforge: no release root above {}", bin.display());
            return 3;
        }
    };
    match (args.get(1).map(String::as_str), args.get(2).map(String::as_str)) {
        (Some("checkpoint"), Some("validate")) => exec_validate(&root, &args[2..]),
        (Some("checkpoint"), Some("attest")) => attest(&root, &args[3..]),
        _ => usage(""),
    }
}

/// `checkpoint validate`: exec the distro interpreter on the release's launcher
/// with an explicit minimal environment (CS-8.2, CS-8.4).
fn exec_validate(root: &Path, rest: &[String]) -> i32 {
    let launcher = root.join("bin").join("devforge-checkpoint.py");
    let err = Command::new("/usr/bin/python3")
        .arg("-I")
        .arg("-B")
        .arg("-P")
        .arg(&launcher)
        .args(rest)
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("LC_ALL", "C.UTF-8")
        .env("LANG", "C.UTF-8")
        .exec();
    eprintln!("devforge: cannot execute /usr/bin/python3 on {}: {err}", launcher.display());
    3
}

// ---------------------------------------------------------------- attest

struct AttestArgs {
    repo: PathBuf,
    plan: String,
    checkpoint: String,
    base: String,
    head: String,
    authority: String,
    review: String,
    dry_run: bool,
}

fn parse_attest_args(rest: &[String]) -> Result<AttestArgs, String> {
    let mut repo = None;
    let mut plan = None;
    let mut checkpoint = None;
    let mut base = None;
    let mut head = None;
    let mut authority = None;
    let mut review = None;
    let mut dry_run = false;
    let mut i = 0;
    while i < rest.len() {
        let flag = rest[i].as_str();
        if flag == "--dry-run" {
            dry_run = true;
            i += 1;
            continue;
        }
        let value = rest.get(i + 1).ok_or_else(|| format!("{flag} needs a value"))?.clone();
        match flag {
            "--repo" => repo = Some(PathBuf::from(value)),
            "--plan" => plan = Some(value),
            "--checkpoint" => checkpoint = Some(value),
            "--base" => base = Some(value),
            "--head" => head = Some(value),
            "--authority" => authority = Some(value),
            "--review" => review = Some(value),
            other => return Err(format!("unknown option {other}")),
        }
        i += 2;
    }
    let plan = plan.ok_or("--plan is required")?;
    if plan.starts_with('/') || plan.split('/').any(|part| part.is_empty() || part == "." || part == "..") {
        return Err("--plan must be a repository-relative path without `.` or `..` segments".into());
    }
    let checkpoint = checkpoint.ok_or("--checkpoint is required")?;
    if !safe_component(&checkpoint) {
        return Err("--checkpoint must be a bare checkpoint id ([A-Za-z0-9_][A-Za-z0-9._-]*)".into());
    }
    Ok(AttestArgs {
        repo: repo.ok_or("--repo is required")?,
        plan,
        checkpoint,
        base: base.ok_or("--base is required")?,
        head: head.ok_or("--head is required")?,
        authority: authority.ok_or("--authority is required")?,
        review: review.ok_or("--review is required")?,
        dry_run,
    })
}

/// A sanitized Git subprocess: absolute executable, explicit environment,
/// no inherited variable (CS-7.1). `safe.directory` names only the repository
/// the human passed, because the attestation is minted as uid 0 over a checkout
/// owned by the agent user.
fn git(repo: &Path, args: &[&str]) -> Result<Vec<u8>, String> {
    let output = Command::new("/usr/bin/git")
        .arg("-c")
        .arg(format!("safe.directory={}", repo.display()))
        .arg("-C")
        .arg(repo)
        .args(args)
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("HOME", "/nonexistent")
        .env("LC_ALL", "C")
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_SYSTEM", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_TERMINAL_PROMPT", "0")
        .stdin(Stdio::null())
        .output()
        .map_err(|err| format!("cannot run /usr/bin/git: {err}"))?;
    if !output.status.success() {
        return Err(format!(
            "git {}: {}",
            args.first().unwrap_or(&""),
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(output.stdout)
}

fn git_line(repo: &Path, args: &[&str]) -> Result<String, String> {
    let out = git(repo, args)?;
    Ok(String::from_utf8_lossy(&out).trim().to_string())
}

/// CS-9.7: a string that may become one path component under the root-owned
/// attestation directory. Never absolute, never `.`/`..`, never empty.
fn safe_component(value: &str) -> bool {
    !value.is_empty()
        && !value.starts_with('.')
        && value.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '.' || c == '-')
}

fn plan_id_from_readme(readme: &str) -> Option<String> {
    for line in readme.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("| Plan ID |") {
            let mut ticks = trimmed.match_indices('`').map(|(i, _)| i);
            if let (Some(a), Some(b)) = (ticks.next(), ticks.next()) {
                return Some(trimmed[a + 1..b].to_string());
            }
        }
    }
    None
}

fn json_string(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// UTC timestamp `YYYY-MM-DDTHH:MM:SSZ` without a date crate (civil-from-days).
fn utc_now() -> String {
    let secs = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0) as i64;
    let days = secs.div_euclid(86_400);
    let rem = secs.rem_euclid(86_400);
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{y:04}-{m:02}-{d:02}T{:02}:{:02}:{:02}Z", rem / 3600, (rem % 3600) / 60, rem % 60)
}

fn attest(root: &Path, rest: &[String]) -> i32 {
    let args = match parse_attest_args(rest) {
        Ok(args) => args,
        Err(message) => return usage(&message),
    };
    let uid = fs::metadata("/proc/self").map(|m| m.uid()).unwrap_or(u32::MAX);
    if !args.dry_run && uid != 0 {
        eprintln!("devforge: attest requires uid 0 (running as uid {uid}); use --dry-run to print the document");
        return 2;
    }
    match mint_with_meta(root, &args, uid) {
        Ok((document, meta)) => {
            let digest = sha256::hex(document.as_bytes());
            if args.dry_run {
                print!("{document}");
                return 0;
            }
            match store(&document, &args, &meta) {
                Ok(path) => {
                    println!("attestation written: {}", path.display());
                    println!("attestation sha256: {digest}");
                    0
                }
                Err(message) => {
                    eprintln!("devforge: {message}");
                    1
                }
            }
        }
        Err(message) => {
            eprintln!("devforge: {message}");
            1
        }
    }
}

struct Minted {
    identity: String,
    plan_id: String,
}

fn mint_with_meta(root: &Path, args: &AttestArgs, uid: u32) -> Result<(String, Minted), String> {
    let repo = git_line(&args.repo, &["rev-parse", "--show-toplevel"])?;
    let repo = PathBuf::from(repo);
    let head = git_line(&repo, &["rev-parse", "--verify", &format!("{}^{{commit}}", args.head)])?;
    let base = git_line(&repo, &["rev-parse", "--verify", &format!("{}^{{commit}}", args.base)])?;
    if base == head || git(&repo, &["merge-base", "--is-ancestor", &base, &head]).is_err() {
        return Err(format!("base {base} is not a proper ancestor of head {head}"));
    }
    let mut roots: Vec<String> = String::from_utf8_lossy(&git(&repo, &["rev-list", "--max-parents=0", &head])?)
        .split_whitespace()
        .map(str::to_string)
        .collect();
    roots.sort();
    if roots.is_empty() {
        return Err("repository has no root commit".into());
    }
    let identity = sha256::hex(roots.join("\n").as_bytes());
    let record_path = format!("{}/checkpoints/{}.yaml", args.plan, args.checkpoint);
    let record = git(&repo, &["cat-file", "blob", &format!("{head}:{record_path}")])
        .map_err(|err| format!("record {record_path} not readable at head {head}: {err}"))?;
    let readme = git(&repo, &["cat-file", "blob", &format!("{head}:{}/README.md", args.plan)])
        .map_err(|err| format!("plan README not readable at head {head}: {err}"))?;
    let plan_id = plan_id_from_readme(&String::from_utf8_lossy(&readme))
        .ok_or("plan README has no `| Plan ID |` row")?;
    if !safe_component(&plan_id) {
        return Err(format!(
            "plan id {plan_id:?} from the README is unsafe as a path component ([A-Za-z0-9_][A-Za-z0-9._-]*); refusing"
        ));
    }
    let identity_file = root.join("RELEASE-IDENTITY.json");
    let release_identity = fs::read(&identity_file)
        .map_err(|err| format!("release identity {} not readable: {err}", identity_file.display()))?;
    let roots_json: Vec<String> = roots.iter().map(|r| json_string(r)).collect();
    let document = format!(
        "{{\n  \"attestation_format\": {},\n  \"repository_identity\": {},\n  \"repository_root_commits\": [{}],\n  \
\"plan_path\": {},\n  \"plan_id\": {},\n  \"checkpoint_id\": {},\n  \"record_path\": {},\n  \
\"base_commit\": {},\n  \"head_commit\": {},\n  \"record_sha256\": {},\n  \"release_root\": {},\n  \
\"release_identity_sha256\": {},\n  \"authority_id\": {},\n  \"review_reference\": {},\n  \
\"minted_at\": {},\n  \"minted_by_uid\": {}\n}}\n",
        json_string(ATTESTATION_FORMAT),
        json_string(&identity),
        roots_json.join(", "),
        json_string(&args.plan),
        json_string(&plan_id),
        json_string(&args.checkpoint),
        json_string(&record_path),
        json_string(&base),
        json_string(&head),
        json_string(&sha256::hex(&record)),
        json_string(&root.display().to_string()),
        json_string(&sha256::hex(&release_identity)),
        json_string(&args.authority),
        json_string(&args.review),
        json_string(&utc_now()),
        uid,
    );
    Ok((document, Minted { identity, plan_id }))
}

/// Write under the fixed root: 0755 directories, a 0644 file created
/// exclusively (an existing attestation is never overwritten; a new review
/// removes it explicitly first).
fn store(document: &str, args: &AttestArgs, meta: &Minted) -> Result<PathBuf, String> {
    let dir = Path::new(ATTEST_ROOT).join(&meta.identity[..32]).join(&meta.plan_id);
    fs::DirBuilder::new()
        .recursive(true)
        .mode(0o755)
        .create(&dir)
        .map_err(|err| format!("cannot create {}: {err}", dir.display()))?;
    let path = dir.join(format!("{}.json", args.checkpoint));
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o644)
        .open(&path)
        .map_err(|err| format!("cannot create {} (an existing attestation is never overwritten; remove it after a new independent review): {err}", path.display()))?;
    file.write_all(document.as_bytes()).map_err(|err| format!("write {}: {err}", path.display()))?;
    file.sync_all().map_err(|err| format!("sync {}: {err}", path.display()))?;
    Ok(path)
}
