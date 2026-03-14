# PROCUREMENT_AGENT_AI

This folder is a standalone procurement package created so you can zip and share the procurement agent more easily.

It keeps the main procurement files together in one place while leaving the original `DB Test` folder unchanged.

Included files:

- `tutorial_agentic_procurement_agent.py`: main procurement agent runner
- `tutorial_procurement_mcp_server.py`: Claude Desktop MCP server for the procurement agent
- `oracle_mcp_server.py`: Oracle database MCP helper
- `start_procurement_agent.sh`: one-step bootstrap and startup script for the procurement agent
- `start_procurement_mcp.sh`: one-step bootstrap launcher used by Claude Desktop
- `install_claude_desktop.py`: writes the correct local MCP entry into Claude Desktop
- `run_tutorial_agent.sh`: launcher for the procurement agent
- `run_procurement_mcp.sh`: launcher for the procurement MCP server
- `requirements.txt`: Python dependencies
- `SETUP.md`: setup guide
- `PROCUREMENT_MCP_SERVER_GUIDE.md`: MCP-specific guide
- `AGENTIC_PROCUREMENT_AI_COMPLETE_GUIDE.md`: business and technical guide
- `TUTORIAL_Agentic_Procurement_AI.md`: tutorial source
- `claude_desktop_procurement_config.example.json`: sample Claude Desktop MCP config
- `.env.example`: environment template without secrets
- `tutorial_agent_outputs/`: output folder for JSON and Excel reports

Recommended sharing flow:

1. Zip the `PROCUREMENT_AGENT_AI` folder.
2. Send the zip file.
3. Tell the receiver to run `./start_procurement_agent.sh`.

Quick start:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x start_procurement_agent.sh
./start_procurement_agent.sh
```

What the startup script does:

1. finds a usable Python interpreter
2. creates `.env` from `.env.example` if missing
3. installs Python packages if they are not already installed
4. registers `procurement-agent-ai` in Claude Desktop using the current folder path
5. starts the procurement agent with default values and saves results in `tutorial_agent_outputs/`

Default run values used by the startup script:

- workflow: `exception-triage`
- autonomy level: `1`
- limit: `5`
- engine: `rules`
- organization id: auto-detect from Oracle session context

You can still override them:

```bash
./start_procurement_agent.sh all 1 5 rules
./start_procurement_agent.sh exception-triage 2 5 claude
./start_procurement_agent.sh exception-triage 1 5 rules 7088
```

The last value is only an example. You can pass any valid organization ID available in Oracle.

Argument order for `start_procurement_agent.sh` is:

1. workflow
2. autonomy level
3. limit
4. engine
5. optional organization id

You can also run the Python entry point directly with an explicit org override:

```bash
python tutorial_agentic_procurement_agent.py --workflow exception-triage --organization-id 7088
```

Replace `7088` with any valid organization ID available in your Oracle instance.

The Claude Desktop MCP tool `run_procurement_agent` now also accepts `organization_id`, so the procurement agent can run against any valid org available in Oracle instead of defaulting to org 204.

After the first startup run, restart Claude Desktop once. Then Claude can use the `procurement-agent-ai` MCP server from this folder.

If you want to start the MCP server manually outside Claude Desktop:

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x start_procurement_mcp.sh
./start_procurement_mcp.sh
./start_procurement_mcp.sh sse
```