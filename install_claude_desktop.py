from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


SERVER_NAME = "procurement-agent-ai"


def _read_env_value(env_path: Path, key: str) -> str | None:
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def _resolve_oracle_client_path(package_dir: Path) -> str | None:
    candidates: list[str] = []
    env_value = os.getenv("ORACLE_CLIENT_PATH")
    if env_value:
        candidates.append(env_value)

    env_paths = (
        package_dir / ".env",
        package_dir.parent / "DB Test" / ".env",
    )
    for env_path in env_paths:
        value = _read_env_value(env_path, "ORACLE_CLIENT_PATH")
        if value and value != "/absolute/path/to/oracle/instantclient":
            candidates.append(value)

    for pattern in (
        str(Path.home() / "oracle" / "instantclient*"),
        "/opt/oracle/instantclient*",
        "/usr/local/lib/instantclient*",
        "/opt/homebrew/lib/instantclient*",
    ):
        candidates.extend(
            str(path)
            for path in sorted(Path("/").glob(pattern.lstrip("/")))
        )

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_dir() and (path / "libclntsh.dylib").exists():
            return str(path)
    return None


def _resolve_python_bin(package_dir: Path) -> str:
    candidates = [
        package_dir / ".venv" / "bin" / "python",
        package_dir.parent / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    env_python = os.getenv("PYTHON_BIN")
    if env_python:
        candidates.insert(0, Path(env_python).expanduser())

    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise FileNotFoundError(
        "No usable Python executable found for Claude Desktop MCP registration"
    )


def _build_server_config(package_dir: Path) -> dict[str, object]:
    server = package_dir / "tutorial_procurement_mcp_server.py"
    oracle_client_path = _resolve_oracle_client_path(package_dir)
    config: dict[str, object] = {
        "command": _resolve_python_bin(package_dir),
        "args": [str(server)],
    }
    if oracle_client_path:
        config["env"] = {
            "ORACLE_CLIENT_PATH": oracle_client_path,
            "DYLD_LIBRARY_PATH": oracle_client_path,
        }
    return config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register the Procurement MCP server in Claude Desktop."
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    package_dir = Path(__file__).resolve().parent
    claude_dir = Path.home() / "Library" / "Application Support" / "Claude"
    config_path = claude_dir / "claude_desktop_config.json"

    claude_dir.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        data = json.loads(config_path.read_text())
        if not isinstance(data, dict):
            raise ValueError("Claude Desktop config must be a JSON object")
    else:
        data = {}

    mcp_servers = data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}
        data["mcpServers"] = mcp_servers

    mcp_servers[SERVER_NAME] = _build_server_config(package_dir)
    config_path.write_text(json.dumps(data, indent=2) + "\n")

    if not args.quiet:
        print(f"Claude Desktop MCP server '{SERVER_NAME}' is configured.")
        print(f"Config file: {config_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
