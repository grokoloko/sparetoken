#!/usr/bin/env bash
# Commit / push only as sparetoken-shop. Never personal gh. Never company git.
# Usage: git-as-sparetoken.sh <git-args...>
#        git-as-sparetoken.sh commit -m "why"
#        git-as-sparetoken.sh push origin HEAD
#        git-as-sparetoken.sh push-alive   # current branch + main
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export GIT_AUTHOR_NAME=sparetoken
export GIT_AUTHOR_EMAIL=sparetoken-shop@users.noreply.github.com
export GIT_COMMITTER_NAME=sparetoken
export GIT_COMMITTER_EMAIL=sparetoken-shop@users.noreply.github.com

git config core.hooksPath .githooks

KEY=""
for candidate in \
  "$ROOT/.anon-secrets/deploy-key/sparetoken_shop_ed25519" \
  "${HOME}/.ssh/sparetoken_shop_ed25519"; do
  if [[ -f "$candidate" ]]; then
    KEY="$candidate"
    break
  fi
done

if [[ -n "$KEY" ]]; then
  export GIT_SSH_COMMAND="ssh -i ${KEY} -o IdentitiesOnly=yes -o BatchMode=yes"
fi

cmd="${1:?usage: git-as-sparetoken.sh <git-args>}"
shift || true

case "$cmd" in
  push-alive)
    git push origin HEAD
    git push origin HEAD:main
    ;;
  *)
    git "$cmd" "$@"
    ;;
esac
