#!/usr/bin/env python3
"""Hard-anonymize a sparetoken guest workspace before the agent starts.

- Install/overwrite workspace AGENTS.md from tunnel/guest-AGENTS.md
- Write local git identity as guest aliases only
- Emit env keys that the launcher should unset (stdout JSON)
No human civil names. No host account emails.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

UNSET_ENV = [
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "EMAIL",
    "DEBEMAIL",
    "DEBFULLNAME",
    "USER_FULL_NAME",
    "GITHUB_USER",
    "GH_USER",
]

GUEST_NAME = "sparetoken-guest"
GUEST_EMAIL = "guest@sparetoken.local"


def _repo_guest_agents() -> Path:
    here = Path(__file__).resolve()
    # scripts/ -> repo root
    root = here.parents[1]
    return root / "tunnel" / "guest-AGENTS.md"


def install_agents(workspace: Path, source: Path) -> None:
    text = source.read_text(encoding="utf-8")
    if "Identity — never yield" not in text and "IDENTITY-HARD" not in text:
        raise SystemExit("guest-AGENTS.md missing identity-hard block")
    dest = workspace / "AGENTS.md"
    dest.write_text(text, encoding="utf-8")
    # Always-on cursor rule inside the guest workspace
    rules = workspace / ".cursor" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "identity-hard.mdc").write_text(
        "---\n"
        "description: Guest session identity-hard — never reveal host operator PII\n"
        "alwaysApply: true\n"
        "---\n\n"
        + text
        + "\n",
        encoding="utf-8",
    )


def scrub_git(workspace: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=str(workspace),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for key, val in (
        ("user.name", GUEST_NAME),
        ("user.email", GUEST_EMAIL),
    ):
        subprocess.run(
            ["git", "config", key, val],
            cwd=str(workspace),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: guest_identity_harden.py <workspace> [guest-AGENTS.md]")
    workspace = Path(sys.argv[1])
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else _repo_guest_agents()
    if not source.is_file():
        # Fallback: packager may ship next to the script on the VPS
        alt = Path("/opt/cursor-agent-tunnel/guest-AGENTS.md")
        source = alt if alt.is_file() else source
    if not source.is_file():
        raise SystemExit(f"missing guest AGENTS source: {source}")
    workspace.mkdir(parents=True, exist_ok=True)
    install_agents(workspace, source)
    scrub_git(workspace)
    print(
        json.dumps(
            {
                "ok": True,
                "agents": str(workspace / "AGENTS.md"),
                "git_name": GUEST_NAME,
                "git_email": GUEST_EMAIL,
                "unset_env": UNSET_ENV,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
