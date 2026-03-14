# Procurement MCP Server Guide

> Purpose: explain how the procurement MCP server works, how Claude Desktop uses it, what tools it exposes, and how to test it safely.

---

## What This MCP Server Is

The procurement MCP server is the Claude Desktop frontend layer for the tutorial procurement agent.

It does not replace the procurement agent. It wraps the existing Python runner and exposes a small set of MCP tools so Claude can:

- test Oracle connectivity
- run procurement workflows
- list generated reports
- return the latest JSON and Excel output paths

Main server file:

- [PROCUREMENT_AGENT_AI/tutorial_procurement_mcp_server.py](PROCUREMENT_AGENT_AI/tutorial_procurement_mcp_server.py)

---

## Architecture

```text
Claude Desktop
  -> procurement-agent-ai MCP server
     -> tutorial_procurement_mcp_server.py
        -> tutorial_agentic_procurement_agent.py
           -> Oracle EBS read-only queries
           -> JSON + Excel outputs
```

This means Claude does not directly query Oracle tables itself. Claude calls the MCP tool, the MCP server calls the procurement agent, and the procurement agent performs the actual business logic.

---

## Why Use MCP Here

Without MCP, the user has to know script names, shell commands, and parameters.

With MCP:

- business users can ask in plain English
- Claude decides which tool to call
- Claude passes the right parameters
- Claude summarizes the result in readable language
- outputs are still saved in JSON and Excel for auditability

---

## Tools Exposed To Claude

The procurement MCP server exposes these tools.

### `test_connection`

Checks Oracle connectivity used by the procurement agent.

Use this for:

- Oracle connectivity validation
- thick mode validation
- confirming that the MCP server is alive

### `run_procurement_agent`

Runs the procurement agent.

Parameters:

- `workflow`
- `autonomy_level`
- `plan_id`
- `limit`
- `organization_id`
- `engine`

`organization_id` can be any valid organization ID present in Oracle `MTL_PARAMETERS`. It is not limited to 7088.

Supported workflow values:

- `all`
- `exception-triage`
- `late-supplier`
- `safety-stock`
- `price-anomaly`
- `demand-to-po`
- `spend-analytics`

Supported engine values:

- `rules`
- `claude`

### `list_saved_reports`

Lists recent JSON and Excel outputs from procurement runs.

### `get_latest_report_paths`

Returns the latest JSON and Excel report path.

---

## Files Involved

- [PROCUREMENT_AGENT_AI/tutorial_procurement_mcp_server.py](PROCUREMENT_AGENT_AI/tutorial_procurement_mcp_server.py)
- [PROCUREMENT_AGENT_AI/tutorial_agentic_procurement_agent.py](PROCUREMENT_AGENT_AI/tutorial_agentic_procurement_agent.py)
- [PROCUREMENT_AGENT_AI/run_procurement_mcp.sh](PROCUREMENT_AGENT_AI/run_procurement_mcp.sh)
- [PROCUREMENT_AGENT_AI/claude_desktop_procurement_config.example.json](PROCUREMENT_AGENT_AI/claude_desktop_procurement_config.example.json)
- [PROCUREMENT_AGENT_AI/tutorial_agent_outputs](PROCUREMENT_AGENT_AI/tutorial_agent_outputs)

---

## How Claude Desktop Uses It

When you type a prompt like:

```text
Use the procurement-agent-ai MCP server and run the procurement agent for exception-triage.
```

Claude Desktop does this:

1. identifies that the `procurement-agent-ai` MCP server is relevant
2. selects the `run_procurement_agent` tool
3. sends the workflow and other parameters
4. waits for the MCP tool result
5. explains the returned result in plain language

Claude reasoning here means orchestration and interpretation, not direct Oracle database logic. The business logic still lives in the procurement Python agent.

---

## How To Start It Manually

### Stdio mode

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
chmod +x run_procurement_mcp.sh
./run_procurement_mcp.sh
```

### SSE mode

```bash
cd "/path/to/PROCUREMENT_AGENT_AI"
./run_procurement_mcp.sh sse
```

Default SSE port for this server is `8120`.

If you want a custom SSE port:

```bash
export PROCUREMENT_MCP_PORT=8125
./run_procurement_mcp.sh sse
```

---

## Claude Desktop Configuration

The live Claude Desktop config should include all three MCP servers:

- `oracle-ebs`
- `item-master-ai`
- `procurement-agent-ai`

Example procurement entry:

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

---

## How To Test In Claude Desktop

### Test 1 - Check the server is loaded

```text
List available MCP servers and confirm whether procurement-agent-ai is loaded.
```

### Test 2 - Check Oracle connectivity

```text
Use the procurement-agent-ai MCP server and call test_connection.
Show me the result clearly.
```

### Test 3 - Run the agent

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

### Test 4 - Get latest outputs

```text
Use the procurement-agent-ai MCP server and call get_latest_report_paths.
Then tell me the latest JSON and Excel file paths.
```

---

## When To Use `engine=rules` vs `engine=claude`

### `engine=rules`

Use this when you want:

- deterministic logic
- lower dependency surface
- stable repeatable behavior

### `engine=claude`

Use this when you want:

- tutorial-style Claude tool use inside the procurement agent itself
- model-generated final summaries
- deeper interactive reasoning inside the agent run

Requirement:

- `ANTHROPIC_API_KEY` must be available in environment or `.env`

---

## What Outputs Are Produced

Every procurement run can produce:

- JSON audit file
- Excel workbook

These are saved in:

- [PROCUREMENT_AGENT_AI/tutorial_agent_outputs](PROCUREMENT_AGENT_AI/tutorial_agent_outputs)

---

## Troubleshooting

### MCP server visible but connection fails

Likely causes:

- Oracle thick mode issue
- wrong Instant Client path
- DB credential issue
- network or port issue

Use:

```text
Use the procurement-agent-ai MCP server and call test_connection.
If it fails, show the exact error.
```

### Claude Desktop does not see the server

Likely causes:

- Claude Desktop not restarted
- wrong Python path in config
- wrong script path in config
- malformed JSON in Claude config

### SSE mode port conflict

The Oracle MCP server uses a different port. The procurement MCP server defaults to `8120`, so they can run side by side.

---

## Summary

The procurement MCP server makes the tutorial procurement agent accessible through Claude Desktop in a business-friendly way.

It is useful because it keeps the real procurement logic in Python, while Claude provides:

- natural language interaction
- tool selection
- summarized explanations
- easier testing and demonstration

This gives you a clean split between:

- Oracle and rule logic in the agent
- user interaction and reasoning presentation in Claude Desktop