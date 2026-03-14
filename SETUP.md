# Oracle EBS MCP Server — Setup Guide

## Prerequisites

- Windows 10/11 (64-bit)
- Python 3.11 or later → https://www.python.org/downloads/
- Internet access (for one-time downloads)

---

## Step 1 — Copy the project files

Copy the following files into a local folder (e.g. `C:\oracle-mcp\`):

```
oracle_mcp_server.py
requirements.txt
.env
```

---

## Step 2 — Add the hosts file entry

This maps the Oracle EBS hostname to the correct IP so Python can resolve it.

1. Open **Notepad as Administrator**
   - Press `Win`, type `Notepad`, right-click → **Run as administrator**

2. Open the hosts file:
   - File → Open → navigate to `C:\Windows\System32\drivers\etc\`
   - Change file filter to **All Files** → open `hosts`

3. Add this line at the bottom:
   ```
   161.118.185.249 apps.example.com apps
   ```

4. Save and close.

5. Flush DNS cache — open **Command Prompt as Administrator** and run:
   ```
   ipconfig /flushdns
   ```

6. Verify it works:
   ```
   ping apps.example.com
   ```
   You should see replies from `161.118.185.249`.

---

## Step 3 — Download Oracle Instant Client

The Oracle EBS database uses Native Network Encryption which requires the Oracle Instant Client (thick mode).

1. Go to:
   ```
   https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
   ```

2. Under **Version 23.x**, download **instantclient-basic-windows.x64-23.x.x.x.x.zip**

3. Create the folder `C:\oracle\`

4. Extract the zip into `C:\oracle\`
   - After extraction you should have: `C:\oracle\instantclient_21_15\instantclient_23_0\oci.dll`
   - (The zip adds two folder levels — this is expected)

5. Verify the path contains `oci.dll`:
   ```
   dir C:\oracle\instantclient_21_15\instantclient_23_0\oci.dll
   ```

---

## Step 4 — Install Python dependencies

Open **Command Prompt** (no admin needed), navigate to your project folder, and run:

```cmd
cd C:\oracle-mcp
pip install -r requirements.txt
```

This installs `oracledb`, `mcp`, and `python-dotenv`.

If you are using the standalone `PROCUREMENT_AGENT_AI` package, you can also use the bootstrap launcher instead of doing this manually:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x start_procurement_agent.sh
./start_procurement_agent.sh
```

It will create `.env` from `.env.example`, install missing packages, and start the agent.

---

## Step 5 — Configure .env

Open `.env` in any text editor. The defaults are already set for this environment:

```ini
DB_HOST=161.118.185.249
DB_PORT=1521
DB_SID=EBSDB
DB_SERVICE_NAME=ebs_EBSDB

APPS_USER=apps
APPS_PASSWORD=apps

ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_15\instantclient_23_0
```

Only change these if your local setup differs (e.g. you extracted the zip to a different folder).

---

## Step 6 — Test the connection

Run this one-liner to confirm everything works end-to-end:

```cmd
python -c "import oracledb; oracledb.init_oracle_client(lib_dir=r'C:\oracle\instantclient_21_15\instantclient_23_0'); conn = oracledb.connect(user='apps', password='apps', dsn=oracledb.makedsn('161.118.185.249', 1521, sid='EBSDB')); cur = conn.cursor(); cur.execute('SELECT VERSION, USER, SYSDATE FROM V$INSTANCE, DUAL'); print(cur.fetchone()); conn.close()"
```

Expected output:
```
('19.0.0.0.0', 'APPS', datetime.datetime(2026, 3, 9, 12, 35, 6))
```

If you see a version, user, and timestamp — the connection is working.

---

## Step 7 — Run the MCP server

```cmd
cd C:\oracle-mcp
python oracle_mcp_server.py
```

The server starts in stdio mode (ready for Claude Code integration).

---

## Step 8 — Register with Claude Code (optional)

To use the tools directly inside Claude Code, add the server to your MCP config.

Open (or create) `C:\Users\<YourUsername>\.claude\mcp.json` and add:

```json
{
  "mcpServers": {
    "oracle-ebs": {
      "command": "python",
      "args": ["C:\\oracle-mcp\\oracle_mcp_server.py"]
    }
  }
}
```

Restart Claude Code. You will then have access to these tools:

| Tool | Description |
|---|---|
| `test_connection` | Verify DB is reachable — returns version, user, timestamp |
| `get_db_info` | Instance metadata, NLS settings, connection pool stats |
| `list_tables` | List tables in a schema (default: APPS) |
| `execute_query` | Run any SELECT query, up to 1000 rows |
| `describe_table` | Show column definitions and comments for a table |

---

## Step 9 — Run the tutorial procurement agent

This project now also includes a standalone tutorial-based agent runner:

```
python tutorial_agentic_procurement_agent.py --workflow exception-triage
```

Useful variants:

```cmd
python tutorial_agentic_procurement_agent.py --workflow exception-triage --autonomy-level 1
python tutorial_agentic_procurement_agent.py --workflow exception-triage --autonomy-level 2
python tutorial_agentic_procurement_agent.py --workflow all --autonomy-level 2 --limit 5
```

What it does:

| Mode | Behaviour |
|---|---|
| `--autonomy-level 0` | Inform only |
| `--autonomy-level 1` | Recommend actions, no draft PO action emitted |
| `--autonomy-level 2` | Emit draft PO payloads for buyer review |

The script follows the tutorial workflows and saves an auditable JSON report in:

```
PROCUREMENT_AGENT_AI/tutorial_agent_outputs/
```

It does not write live transactions into Oracle EBS.

---

## Step 10 — Use it from the Claude terminal

If you want this to work smoothly inside the Claude terminal for this workspace:

1. Start the Oracle MCP server if you want Claude to use the Oracle tools interactively:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
python oracle_mcp_server.py --sse
```

2. Run the standalone tutorial agent directly from the Claude terminal:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
python3 tutorial_agentic_procurement_agent.py --workflow exception-triage --autonomy-level 1 --limit 5
```

3. Or use the launcher script added for Claude-terminal use:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x run_tutorial_agent.sh
./run_tutorial_agent.sh exception-triage 1 5 rules
./run_tutorial_agent.sh exception-triage 2 5 rules
./run_tutorial_agent.sh exception-triage 2 5 claude
./run_tutorial_agent.sh all 1 5 claude
```

How this works:

| Piece | Role |
|---|---|
| `oracle_mcp_server.py` | Gives Claude MCP tools for DB exploration |
| `tutorial_agentic_procurement_agent.py` | Runs the tutorial workflow logic |
| `run_tutorial_agent.sh` | Simple Claude-terminal launcher |
| `.claude/settings.local.json` | Allows these commands in the local Claude workspace |

Important limitation:

For `claude` engine mode, set `ANTHROPIC_API_KEY` in your terminal or `.env` first. The runner will then use Claude tool-use and save both JSON and Excel outputs.

## Step 11 — Use it from Claude Desktop through MCP

This folder now also includes a dedicated MCP server for the tutorial procurement agent.

Files:

| File | Role |
|---|---|
| `tutorial_procurement_mcp_server.py` | MCP server that runs the procurement agent |
| `start_procurement_mcp.sh` | Bootstrap launcher used by Claude Desktop |
| `run_procurement_mcp.sh` | Launcher for stdio or SSE mode |
| `install_claude_desktop.py` | Writes the local MCP entry into Claude Desktop |
| `claude_desktop_procurement_config.example.json` | Sample Claude Desktop MCP config |

Available MCP tools:

| Tool | Description |
|---|---|
| `test_connection` | Check Oracle connectivity used by the procurement agent |
| `run_procurement_agent` | Run the procurement agent with workflow, limit, plan, autonomy, engine, and optional organization_id |
| `list_saved_reports` | List generated JSON and Excel outputs |
| `get_latest_report_paths` | Return the latest JSON and Excel file paths |

`organization_id` is generic. You can pass any valid Oracle org ID available in `MTL_PARAMETERS`.

Recommended shareable setup:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x start_procurement_agent.sh
./start_procurement_agent.sh
```

This creates `.env` if needed, installs missing packages, registers `procurement-agent-ai` in Claude Desktop, runs the agent, and saves outputs in `tutorial_agent_outputs/`.

Restart Claude Desktop once after the first run.

Manual MCP start:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x start_procurement_mcp.sh
./start_procurement_mcp.sh
./start_procurement_mcp.sh sse
chmod +x run_procurement_mcp.sh
./run_procurement_mcp.sh
./run_procurement_mcp.sh sse
```

If you want SSE mode on a custom port, set `PROCUREMENT_MCP_PORT` first.

Automatic Claude Desktop registration:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
python install_claude_desktop.py
```

If you still want a manual Claude Desktop config entry, use:

```json
{
   "mcpServers": {
      "procurement-agent-ai": {
         "command": "/absolute/path/to/python3",
         "args": [
            "/absolute/path/to/PROCUREMENT_AGENT_AI/tutorial_procurement_mcp_server.py"
         ]
      }
   }
}
```

Example Claude Desktop prompt:

```text
Use the procurement-agent-ai MCP server and run_procurement_agent with:
- workflow: exception-triage
- autonomy_level: 1
- limit: 5
- organization_id: 7088
- engine: rules

Replace `7088` with any valid organization ID available in your Oracle instance.

Then show me:
1. action summary
2. JSON report path
3. Excel report path
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `getaddrinfo failed` | Hosts file entry missing or DNS not flushed | Redo Step 2, run `ipconfig /flushdns` |
| `DPI-1047: Cannot locate 64-bit Oracle Client` | Wrong Instant Client path | Check `ORACLE_CLIENT_PATH` in `.env` points to the folder containing `oci.dll` |
| `NNE` / `DPY-3001` | Thin mode used instead of thick | Ensure `ORACLE_CLIENT_PATH` is set and Instant Client is valid |
| `ORA-01017: invalid username/password` | Wrong credentials | Check `APPS_USER` / `APPS_PASSWORD` in `.env` |
| `timed out` | Network/firewall blocking port 1521 | Confirm hosts entry is correct and port 1521 is not blocked |
