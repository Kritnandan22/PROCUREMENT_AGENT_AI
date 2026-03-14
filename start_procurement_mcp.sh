#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}
cd "${script_dir}"

python_bin="${script_dir}/.venv/bin/python"

if [[ ! -x "${python_bin}" ]]; then
  python_bin="${script_dir:h}/.venv/bin/python"
fi

if [[ ! -x "${python_bin}" ]]; then
  python_bin=${PYTHON_BIN:-$(command -v python3 || command -v python)}
fi

if [[ -z "${python_bin:-}" || ! -x "${python_bin}" ]]; then
  echo "Python was not found. Install Python 3.11+ or set PYTHON_BIN." >&2
  exit 1
fi

if [[ ! -f ".env" ]]; then
  if [[ -f ".env.example" ]]; then
    cp ".env.example" ".env"
    echo "Created .env from .env.example. Review ORACLE_CLIENT_PATH and credentials before first use." >&2
  else
    echo ".env is missing and .env.example was not found." >&2
    exit 1
  fi
fi

resolve_oracle_client_path() {
  local configured_path=""
  local shared_env="${script_dir:h}/DB Test/.env"

  if [[ -f ".env" ]]; then
    configured_path=$(awk -F= '/^ORACLE_CLIENT_PATH=/{print $2}' .env | tail -1)
  fi

  if [[ -n "${configured_path}" && "${configured_path}" != "/absolute/path/to/oracle/instantclient" && -d "${configured_path}" ]]; then
    export ORACLE_CLIENT_PATH="${configured_path}"
    return
  fi

  if [[ -f "${shared_env}" ]]; then
    configured_path=$(awk -F= '/^ORACLE_CLIENT_PATH=/{print $2}' "${shared_env}" | tail -1)
    if [[ -n "${configured_path}" && -d "${configured_path}" ]]; then
      export ORACLE_CLIENT_PATH="${configured_path}"
      return
    fi
  fi

  local candidate
  for candidate in "$HOME"/oracle/instantclient* /opt/oracle/instantclient* /usr/local/lib/instantclient* /opt/homebrew/lib/instantclient*; do
    if [[ -d "${candidate}" && -e "${candidate}/libclntsh.dylib" ]]; then
      export ORACLE_CLIENT_PATH="${candidate}"
      return
    fi
  done
}

resolve_oracle_client_path

if ! "${python_bin}" -c "import oracledb, dotenv, openpyxl, mcp" >/dev/null 2>&1; then
  echo "Installing required Python packages..." >&2
  "${python_bin}" -m pip install -r requirements.txt
fi

transport=${1:-stdio}

if [[ "${transport}" == "sse" ]]; then
  exec "${python_bin}" tutorial_procurement_mcp_server.py --sse
fi

exec "${python_bin}" tutorial_procurement_mcp_server.py