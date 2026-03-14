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
transport=${1:-stdio}

if [[ ! -x "${python_bin}" ]]; then
  echo "Python environment not found at ${python_bin}" >&2
  exit 1
fi

cd "${script_dir}"
if [[ "${transport}" == "sse" ]]; then
  exec "${python_bin}" tutorial_procurement_mcp_server.py --sse
fi

exec "${python_bin}" tutorial_procurement_mcp_server.py