#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env. Add OPENROUTER_API_KEY and AGENT_API_TOKEN, then rerun."
  exit 0
fi

python -m unittest discover -s tests -v
exec python run_server.py
