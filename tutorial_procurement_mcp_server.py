"""Claude Desktop MCP server for the tutorial procurement agent."""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from tutorial_agentic_procurement_agent import OUTPUT_DIR, OracleReadOnlyGateway, run_agent


load_dotenv(Path(__file__).with_name(".env"))

_host = os.getenv("MCP_HOST", "0.0.0.0")
_port = int(os.getenv("PORT", os.getenv("PROCUREMENT_MCP_PORT", "8120")))


def _json_default(value: Any) -> Any:
    return str(value)


def _ok(data: Any, **extra: Any) -> str:
    return json.dumps(
        {"status": "ok", **extra, "data": data},
        default=_json_default,
    )


def _err(message: str, detail: str = "") -> str:
    return json.dumps(
        {"status": "error", "message": message, "detail": detail}
    )


mcp = FastMCP(
    "procurement-agent-ai",
    instructions=(
        "Run the tutorial procurement agent, test Oracle connectivity, "
        "and list saved JSON or Excel outputs for Claude Desktop."
    ),
    host=_host,
    port=_port,
)


@mcp.tool()
def test_connection() -> str:
    """Test the Oracle EBS connection used by the procurement agent."""
    try:
        gateway = OracleReadOnlyGateway()
        return _ok(gateway.test_connection(), message="Connection successful")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


@mcp.tool()
def run_procurement_agent(
    workflow: str = "exception-triage",
    autonomy_level: int = 1,
    plan_id: int | None = None,
    limit: int = 10,
    organization_id: int | None = None,
    engine: str = "rules",
) -> str:
    """Run the procurement agent and return output paths plus a summary."""
    try:
        run_output = run_agent(
            workflow=workflow,
            autonomy_level=autonomy_level,
            plan_id=plan_id,
            limit=limit,
            organization_id=organization_id,
            engine=engine,
        )
        result = run_output["result"]
        summary = {
            "workflow": workflow,
            "autonomy_level": autonomy_level,
            "plan_id": plan_id,
            "limit": limit,
            "organization_id": organization_id,
            "engine": engine,
            "actions_created": len(result.get("actions", [])),
            "action_summary": result.get("action_summary", {}),
            "json_path": run_output["json_path"],
            "excel_path": run_output["excel_path"],
        }
        return _ok(summary, message="Procurement agent run completed")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


@mcp.tool()
def list_saved_reports(limit: int = 20) -> str:
    """List the most recent saved JSON and Excel outputs."""
    try:
        files = sorted(
            OUTPUT_DIR.glob("tutorial_agent_run_*"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )[: max(1, min(limit, 100))]
        data = [
            {
                "name": path.name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "modified_at": path.stat().st_mtime,
            }
            for path in files
        ]
        return _ok(data, count=len(data))
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


@mcp.tool()
def get_latest_report_paths() -> str:
    """Return the latest JSON and Excel report paths if they exist."""
    try:
        json_files = sorted(
            OUTPUT_DIR.glob("tutorial_agent_run_*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        excel_files = sorted(
            OUTPUT_DIR.glob("tutorial_agent_run_*.xlsx"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        payload = {
            "latest_json": str(json_files[0]) if json_files else "",
            "latest_excel": str(excel_files[0]) if excel_files else "",
        }
        return _ok(payload)
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())

@mcp.tool()
def read_output_file(filename: str) -> str:
    """Read a JSON or Excel file from the output directory and return its content.
    Excel files are returned as Base64 strings.
    JSON files are returned as raw text strings.
    """
    try:
        path = OUTPUT_DIR / filename
        if not path.resolve().is_relative_to(OUTPUT_DIR.resolve()):
            return _err("Access denied: path outside output directory")
        if not path.exists():
            return _err(f"File not found: {filename}")
            
        if filename.endswith(".xlsx"):
            import base64
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            return _ok({"filename": filename, "format": "base64", "content": encoded})
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return _ok({"filename": filename, "format": "text", "content": content})
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


@mcp.prompt()
def exception_triage() -> str:
    """Run the exception-triage procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='exception-triage' and engine='rules' to triage procurement exceptions."


@mcp.prompt()
def late_supplier() -> str:
    """Run the late-supplier procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='late-supplier' and engine='rules' to analyze late supplier arrivals."


@mcp.prompt()
def safety_stock() -> str:
    """Run the safety-stock procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='safety-stock' and engine='rules' to evaluate safety stock levels."


@mcp.prompt()
def price_anomaly() -> str:
    """Run the price-anomaly procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='price-anomaly' and engine='rules' to detect purchase order price anomalies."


@mcp.prompt()
def demand_to_po() -> str:
    """Run the demand-to-po procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='demand-to-po' and engine='rules' to convert firm demand into purchase orders."


@mcp.prompt()
def spend_analytics() -> str:
    """Run the spend-analytics procurement workflow."""
    return "Please use the run_procurement_agent tool with workflow='spend-analytics' and engine='rules' to analyze and categorize procurement spend."


if __name__ == "__main__":
    transport = "sse" if "--sse" in sys.argv else "stdio"
    if transport == "sse":
        print(
            (
                "Starting Procurement MCP server (SSE) on "
                f"http://{_host}:{_port}/sse"
            ),
            file=sys.stderr,
        )
    else:
        print("Starting Procurement MCP server (stdio)", file=sys.stderr)
    mcp.run(transport=transport)
