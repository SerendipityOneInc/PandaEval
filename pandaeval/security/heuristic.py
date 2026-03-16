"""Heuristic security scanner for skill files.

Scans SKILL.md and all accompanying files for known threat patterns
across 5 categories: destructive commands, data exfiltration,
credential access, code obfuscation, and supply chain attacks.

Returns a score (0-10) and categorized findings.
"""

import re
from pathlib import Path


# --- Threat pattern definitions ---
# Each entry: (regex, description, category)
# Categories: destructive, exfiltration, credential, obfuscation, supply_chain

THREAT_PATTERNS = {
    "destructive": {
        "weight": 3,  # points deducted per hit
        "max_deduction": 6,
        "patterns": [
            (r"rm\s+-rf\s+/(?!\w)", "rm -rf /"),
            (r"rm\s+-rf\s+~/", "rm -rf ~/"),
            (r"rm\s+-rf\s+\$HOME", "rm -rf $HOME"),
            (r"\bmkfs\b", "mkfs (format filesystem)"),
            (r"\bdd\s+if=", "dd if= (raw disk write)"),
            (r"DROP\s+TABLE", "DROP TABLE"),
            (r"DROP\s+DATABASE", "DROP DATABASE"),
            (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", "fork bomb"),
            (r">\s*/dev/sd[a-z]", "overwrite block device"),
            (r"\bfind\s+/\s+-delete\b", "find / -delete"),
            (r"shutil\.rmtree\s*\(\s*['\"/]", "shutil.rmtree on root path"),
        ],
    },
    "exfiltration": {
        "weight": 2,
        "max_deduction": 4,
        "patterns": [
            (r"curl\s+.*(-d|--data|-X\s*POST)\s+.*https?://", "curl POST to external URL"),
            (r"discord\.com/api/webhooks", "Discord webhook"),
            (r"hooks\.slack\.com", "Slack webhook"),
            (r"api\.telegram\.org", "Telegram API"),
            (r"urllib\.request\.urlopen\s*\(.*Request\(", "urllib POST request"),
            (r"\bnc\s+-[a-z]*\s+\d+", "netcat connection"),
        ],
    },
    "credential": {
        "weight": 2,
        "max_deduction": 4,
        "patterns": [
            # Actual read operations on credential files — covers:
            #   open()/read/cat/cp style:  open("~/.aws/credentials")
            #   pathlib style:             Path.home().joinpath(".aws","credentials").read_text()
            #   read_text/read_bytes on credential paths
            (r"(open|read|cat|head|tail|less|more|cp|scp|rsync)\s*[\(\s].{0,80}(~/\.ssh/id_|\.ssh/id_)", "SSH private key read"),
            (r"(open|read|cat|head|tail|less|more|cp|scp|rsync)\s*[\(\s].{0,80}(~/\.aws/credentials|\.aws.{0,20}credentials)", "AWS credentials read"),
            (r"(open|read|cat|head|tail|less|more|cp|scp|rsync)\s*[\(\s].{0,80}/etc/shadow", "/etc/shadow read"),
            (r"(open|read|cat|head|tail|less|more|cp|scp|rsync)\s*[\(\s].{0,80}(~/\.gnupg/|\.gnupg)", "GPG keyring read"),
            # pathlib / Path().read_text() patterns for credential files
            (r"(\.aws.{0,30}credentials|\.ssh.{0,20}id_|/etc/shadow|\.gnupg).{0,80}\.(read_text|read_bytes)\s*\(", "pathlib read of credential file"),
            (r"(chmod|chown|echo\s.*>>?)\s.*/etc/sudoers", "sudoers modification"),
            (r"(cat|open|read)\s*[\(\s].{0,80}\.env\b", "reading .env file"),
            (r"keychain\s+(get|dump|export)", "keychain extraction"),
            (r"security\s+find-(generic|internet)-password", "macOS keychain query"),
        ],
    },
    "obfuscation": {
        "weight": 3,
        "max_deduction": 6,
        "patterns": [
            (r"eval\s*\(.*base64", "eval + base64"),
            (r"exec\s*\(.*decode", "exec + decode"),
            (r"String\.fromCharCode", "String.fromCharCode"),
            (r"\\x[0-9a-fA-F]{2}.*\\x[0-9a-fA-F]{2}.*eval", "hex + eval"),
            (r"atob\s*\(", "atob() decoding"),
            (r"compile\s*\(.*exec", "compile + exec"),
        ],
    },
    "supply_chain": {
        "weight": 2,
        "max_deduction": 4,
        "patterns": [
            (r"curl\s+.*\|\s*(ba)?sh", "curl | bash"),
            (r"wget\s+.*\|\s*(ba)?sh", "wget | sh"),
            (r"pip\s+install\s+.*--index-url\s+(?!https://pypi)", "non-PyPI pip index"),
            (r"npm\s+install\s+.*--registry\s+(?!https://registry\.npmjs)", "non-default npm registry"),
            (r"docker\s+run\s+.*--privileged", "privileged docker container"),
        ],
    },
}

_SENSITIVE_LOCAL_DATA_RE = re.compile(
    r"(/etc/shadow|~?/\.aws/credentials|~?/\.ssh/id_(rsa|ed25519|ecdsa)|~?/\.gnupg/|\.env\b)",
    re.IGNORECASE,
)
_SENSITIVE_NETWORK_CALLS = (
    "requests.post(",
    "httpx.post(",
    "session.post(",
    "client.post(",
)
_SENSITIVE_NETWORK_RE = re.compile(
    r"requests\.request\s*\(\s*['\"]POST['\"]",
    re.IGNORECASE,
)


_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "env"}
_TEXT_EXTS = {".py", ".sh", ".js", ".ts", ".md", ".txt", ".yaml", ".yml", ".toml"}


def _read_all_files(skill_dir):
    """Read all text files in the skill directory, returning per-file content list."""
    base = Path(skill_dir)
    files = []

    skill_md = base / "SKILL.md"
    if skill_md.is_file():
        try:
            files.append(skill_md.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass

    for f in base.rglob("*"):
        if any(part in _SKIP_DIRS for part in f.parts):
            continue
        if f.is_file() and f.suffix in _TEXT_EXTS and f != skill_md and f.stat().st_size < 500_000:
            try:
                files.append(f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    return files


def _extract_call_slice(content, start, max_chars=600):
    """Extract a best-effort function call slice starting at start."""
    end = min(len(content), start + max_chars)
    depth = 0
    saw_open_paren = False

    for idx in range(start, end):
        char = content[idx]
        if char == "(":
            depth += 1
            saw_open_paren = True
        elif char == ")" and saw_open_paren:
            depth -= 1
            if depth == 0:
                return content[start:idx + 1]

    return content[start:end]


def _has_network_call(text):
    """Check if text contains any network send call."""
    lowered = text.lower()
    for marker in _SENSITIVE_NETWORK_CALLS:
        if marker in lowered:
            return True
    if _SENSITIVE_NETWORK_RE.search(text):
        return True
    return False


def _find_sensitive_network_calls(content):
    """Detect network calls that include sensitive local data.

    Two detection modes:
      1. Direct: sensitive path appears inside a network call's arguments.
      2. Proximity (per-file): a code-level credential read and a network
         send co-occur in the same file content, indicating two-step
         read-then-send patterns.
    """
    findings = []
    lowered = content.lower()
    found = False

    # --- Mode 1: sensitive path directly inside call arguments ---
    for marker in _SENSITIVE_NETWORK_CALLS:
        if found:
            break
        start = 0
        while True:
            idx = lowered.find(marker, start)
            if idx == -1:
                break
            call_text = _extract_call_slice(content, idx)
            if _SENSITIVE_LOCAL_DATA_RE.search(call_text):
                findings.append("network send with sensitive local data")
                found = True
                break
            start = idx + len(marker)

    if not found:
        for m in _SENSITIVE_NETWORK_RE.finditer(content):
            call_text = _extract_call_slice(content, m.start())
            if _SENSITIVE_LOCAL_DATA_RE.search(call_text):
                findings.append("network send with sensitive local data")
                found = True
                break

    return findings


# Code-level credential read pattern (not just path mention in docs)
_CREDENTIAL_READ_RE = re.compile(
    r"(open|read_text|read_bytes|cat|cp|scp)\s*[\(\s].{0,120}"
    r"(\.aws.{0,30}credentials|\.ssh.{0,20}id_|/etc/shadow|\.gnupg)"
    r"|"
    r"(\.aws.{0,30}credentials|\.ssh.{0,20}id_|/etc/shadow|\.gnupg)"
    r".{0,120}(read_text|read_bytes|read)\s*\(",
    re.IGNORECASE,
)


def _find_per_file_exfiltration(file_contents):
    """Detect two-step credential-read-then-send within individual files.

    Only triggers when a code-level credential read (open/read_text/cat)
    and a network send call both appear in the same file.
    """
    for content in file_contents:
        if _CREDENTIAL_READ_RE.search(content) and _has_network_call(content):
            return [{"category": "exfiltration", "pattern": "credential read + network send in same file"}]
    return []


def heuristic_scan(skill_dir):
    """Run heuristic security scan on a skill directory.

    Args:
        skill_dir: Path to skill directory containing SKILL.md.

    Returns:
        dict with keys:
            score: int 0-10 (10 = no threats found)
            findings: list of dicts with category, pattern, description
            category_scores: dict mapping category -> deduction applied
            notes: list of human-readable notes
    """
    file_contents = _read_all_files(skill_dir)
    content = "\n".join(file_contents)
    if not content.strip():
        return {
            "score": 5,
            "findings": [],
            "category_scores": {},
            "notes": ["No readable content found in skill directory"],
        }

    score = 10
    findings = []
    category_scores = {}

    for category, config in THREAT_PATTERNS.items():
        hits = 0
        for pat, desc in config["patterns"]:
            if re.search(pat, content, re.IGNORECASE | re.DOTALL):
                hits += 1
                findings.append({
                    "category": category,
                    "pattern": desc,
                })
        if category == "exfiltration":
            # Mode 1: direct — sensitive path inside network call args
            for desc in _find_sensitive_network_calls(content):
                hits += 1
                findings.append({
                    "category": category,
                    "pattern": desc,
                })
            # Mode 2: per-file — credential read + network send in same file
            if hits == 0:
                for f in _find_per_file_exfiltration(file_contents):
                    hits += 1
                    findings.append(f)
        deduction = min(config["max_deduction"], hits * config["weight"])
        category_scores[category] = deduction
        score -= deduction

    score = max(0, score)
    notes = [f"[heuristic:{f['category']}] {f['pattern']}" for f in findings]
    if not findings:
        notes.append("No heuristic threat patterns detected")

    return {
        "score": score,
        "findings": findings,
        "category_scores": category_scores,
        "notes": notes,
    }
