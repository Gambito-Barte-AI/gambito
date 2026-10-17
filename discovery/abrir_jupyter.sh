#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Ambiente ausente. Siga a instalação em discovery/README.md.' >&2
  exit 1
fi
exec .venv/bin/python -m jupyter lab discovery/
