#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}
python_bin="${script_dir}/.venv/bin/python"

if [[ ! -x "${python_bin}" ]]; then
  python_bin="${script_dir:h}/.venv/bin/python"
fi

if [[ ! -x "${python_bin}" ]]; then
  python_bin=${PYTHON_BIN:-$(command -v python3 || command -v python)}
fi

workflow=${1:-exception-triage}
autonomy_level=${2:-1}
limit=${3:-5}
engine=${4:-rules}

if [[ ! -x "${python_bin}" ]]; then
  echo "Python environment not found at ${python_bin}" >&2
  exit 1
fi

cd "${script_dir}"
exec "${python_bin}" tutorial_agentic_procurement_agent.py \
  --engine "${engine}" \
  --workflow "${workflow}" \
  --autonomy-level "${autonomy_level}" \
  --limit "${limit}"