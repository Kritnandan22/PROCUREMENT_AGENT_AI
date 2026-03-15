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


def _err(message: str, detail: str = "", user_action: str = "") -> str:
    """Return error with user-friendly guidance."""
    return json.dumps(
        {
            "status": "error",
            "message": message,
            "detail": detail,
            "user_action": user_action or _error_guidance(message),
        }
    )


def _error_guidance(error_msg: str) -> str:
    """Provide user-friendly guidance for common errors."""
    error_lower = error_msg.lower()

    if "ora-" in error_lower or "oracledb" in error_lower:
        return (
            "❌ Database Error\n"
            "Fix: Check your Oracle credentials\n"
            "1. Verify DB_HOST, DB_PORT, DB_SID are correct\n"
            "2. Verify APPS_USER and APPS_PASSWORD are correct\n"
            "3. Confirm you have network access to the Oracle server\n"
            "4. Try running test_connection first"
        )
    elif "connection" in error_lower or "timeout" in error_lower:
        return (
            "❌ Connection Issue\n"
            "Fix: Check your network and credentials\n"
            "1. Verify all environment variables are set: DB_HOST, APPS_USER, etc\n"
            "2. Check if Render server is awake (first request takes 30-60 seconds)\n"
            "3. Try the test_connection tool first\n"
            "4. Check your firewall/network access"
        )
    elif "permission" in error_lower or "access" in error_lower:
        return (
            "❌ Permission Denied\n"
            "Fix: Check your Oracle user permissions\n"
            "1. Verify APPS_USER has SELECT permission on tables\n"
            "2. Contact your DBA to grant required permissions\n"
            "3. Try a different Oracle account if available"
        )
    elif "table" in error_lower or "column" in error_lower:
        return (
            "❌ Table/Column Not Found\n"
            "Fix: Check your Oracle schema and version\n"
            "1. Verify you're pointing to the right Oracle instance\n"
            "2. Confirm the Oracle EBS tables exist in your schema\n"
            "3. Check config.yaml table mappings match your schema\n"
            "4. Contact your DBA for table locations"
        )
    else:
        return "❌ Error\nFix: Check the error details above and try again"


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
    """Test the Oracle EBS connection and return database info.

    Run this first to verify your Oracle credentials work!
    """
    try:
        gateway = OracleReadOnlyGateway()
        db_info = gateway.test_connection()
        return _ok(
            db_info,
            message="✅ Connection successful!",
        )
    except Exception as exc:
        error_msg = str(exc)
        return _err(
            f"❌ Cannot connect to Oracle EBS: {error_msg}",
            detail=traceback.format_exc(),
        )


@mcp.tool()
def run_procurement_agent(
    workflow: str = "exception-triage",
    autonomy_level: int = 1,
    plan_id: int | None = None,
    limit: int = 10,
    organization_id: int | None = None,
    engine: str = "rules",
) -> str:
    """Run the procurement agent and return summary + file paths.

    Supported workflows:
    - exception-triage: Find procurement exceptions (default)
    - late-supplier: Identify late-performing suppliers
    - safety-stock: Analyze safety stock levels
    - price-anomaly: Detect pricing anomalies
    - demand-to-po: Convert demand signals to PO recommendations
    - spend-analytics: Analyze spend patterns and supplier concentration

    Autonomy levels:
    - 1 (default): Read-only analysis and recommendations
    - 2: Create draft purchase orders automatically
    """
    try:
        # Validate workflow
        valid_workflows = [
            "exception-triage",
            "late-supplier",
            "safety-stock",
            "price-anomaly",
            "demand-to-po",
            "spend-analytics",
        ]
        if workflow not in valid_workflows:
            return _err(
                f"❌ Invalid workflow: {workflow}",
                detail=f"Valid workflows: {', '.join(valid_workflows)}",
            )

        # Validate autonomy level
        if autonomy_level not in [1, 2]:
            return _err(
                "❌ Invalid autonomy_level",
                detail="Must be 1 (read-only) or 2 (auto-PO creation)",
            )

        # Run agent
        run_output = run_agent(
            workflow=workflow,
            autonomy_level=autonomy_level,
            plan_id=plan_id,
            limit=limit,
            organization_id=organization_id,
            engine=engine,
        )
        result = run_output["result"]

        # Validate results
        actions = result.get("actions", [])
        action_count = len(actions)

        summary = {
            "workflow": workflow,
            "autonomy_level": autonomy_level,
            "plan_id": plan_id,
            "limit": limit,
            "organization_id": organization_id,
            "engine": engine,
            "actions_created": action_count,
            "action_summary": result.get("action_summary", {}),
            "json_path": run_output["json_path"],
            "excel_path": run_output["excel_path"],
            "data_quality": {
                "records_processed": result.get("records_processed", 0),
                "has_results": action_count > 0,
                "complete": action_count > 0,
            },
        }

        # Warn if no results
        message = f"✅ Completed {workflow} workflow"
        if action_count == 0:
            message += " (⚠️ No exceptions found - data may be clean)"

        return _ok(summary, message=message)
    except Exception as exc:
        error_msg = str(exc)
        return _err(
            f"❌ Agent failed: {error_msg}",
            detail=traceback.format_exc(),
        )


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
    """Read a JSON or Excel file and return its content (base64 for Excel).

    For Excel files (.xlsx):
    - Content is Base64 encoded
    - Decode and save to your Downloads folder as .xlsx
    - Open with Excel or Google Sheets

    For JSON files (.json):
    - Content is plain text
    - Contains structured procurement analysis data
    - Can be imported into your systems

    Usage:
    1. Call get_latest_report_paths() to find files
    2. Call this tool with the filename
    3. Decode Base64 (if Excel) and save locally
    """
    try:
        path = OUTPUT_DIR / filename
        if not path.resolve().is_relative_to(OUTPUT_DIR.resolve()):
            return _err(
                "❌ Access denied",
                detail="Path outside output directory",
            )
        if not path.exists():
            return _err(
                f"❌ File not found: {filename}",
                detail=f"Check with get_latest_report_paths() first",
            )

        if filename.endswith(".xlsx"):
            import base64

            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            file_size_mb = path.stat().st_size / (1024 * 1024)
            return _ok(
                {
                    "filename": filename,
                    "format": "base64",
                    "content": encoded,
                    "size_bytes": path.stat().st_size,
                    "instructions": (
                        "Decode the Base64 content and save as .xlsx\n"
                        "Open with Excel, Google Sheets, or LibreOffice"
                    ),
                },
                message=f"✅ Excel file ready ({file_size_mb:.1f} MB)",
            )

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        file_size_kb = path.stat().st_size / 1024
        return _ok(
            {
                "filename": filename,
                "format": "text",
                "content": content,
                "size_bytes": path.stat().st_size,
                "instructions": "JSON data - can be imported into systems or parsed for analysis",
            },
            message=f"✅ JSON file ready ({file_size_kb:.1f} KB)",
        )
    except Exception as exc:
        return _err(
            f"❌ Cannot read file: {str(exc)}",
            detail=traceback.format_exc(),
        )


@mcp.tool()
def list_organization_ids() -> str:
    """List all available organization IDs from Oracle MTL_PARAMETERS table.

    Use these IDs to filter analysis by specific organizations/business units.
    """
    try:
        gateway = OracleReadOnlyGateway()
        result = gateway.list_organization_ids()
        return _ok(
            result,
            message="✅ Organization IDs retrieved",
            count=len(result) if isinstance(result, list) else 0,
        )
    except Exception as exc:
        return _err(
            f"❌ Cannot list organization IDs: {str(exc)}",
            detail=traceback.format_exc(),
        )


@mcp.tool()
def get_workflow_help(workflow: str = "exception-triage") -> str:
    """Get detailed help for a specific workflow.

    Workflows available:
    - exception-triage: Find procurement exceptions
    - late-supplier: Identify late suppliers
    - safety-stock: Analyze inventory levels
    - price-anomaly: Detect pricing issues
    - demand-to-po: Convert demands to POs
    - spend-analytics: Analyze spending patterns
    """
    workflows = {
        "exception-triage": {
            "description": "Identify procurement exceptions and recommend actions",
            "finds": [
                "Items with no activity",
                "Excess inventory",
                "Safety stock issues",
                "Late-performing suppliers",
                "Pricing anomalies",
            ],
            "output": "Exception list with supplier recommendations",
            "use_case": "Regular exception management (daily/weekly)",
            "setup_time": "1-5 minutes",
        },
        "late-supplier": {
            "description": "Identify and analyze late-performing suppliers",
            "finds": [
                "Suppliers with low on-time delivery rate",
                "Suppliers with high lead time variance",
                "Trend analysis of supplier performance",
                "Supplier switching recommendations",
            ],
            "output": "Supplier performance report with rankings",
            "use_case": "Supplier negotiations, consolidation planning",
            "setup_time": "2-5 minutes",
        },
        "safety-stock": {
            "description": "Analyze and optimize safety stock levels",
            "finds": [
                "Items with inadequate safety stock",
                "Items with excess safety stock",
                "Demand volatility analysis",
                "Safety stock adjustment recommendations",
            ],
            "output": "Inventory optimization report",
            "use_case": "Quarterly inventory planning",
            "setup_time": "2-10 minutes (depends on volume)",
        },
        "price-anomaly": {
            "description": "Detect pricing anomalies and deviations",
            "finds": [
                "Prices above contract rates",
                "Price trending issues",
                "Supplier price variance",
                "Renegotiation candidates",
            ],
            "output": "Pricing analysis with vendor comparisons",
            "use_case": "Cost management, supplier negotiations",
            "setup_time": "2-5 minutes",
        },
        "demand-to-po": {
            "description": "Convert demand signals to purchase order recommendations",
            "finds": [
                "Unfulfilled demand",
                "Recommended purchase order quantities",
                "Supplier recommendations",
                "Timeline analysis",
            ],
            "output": "PO recommendations with supplier selection",
            "use_case": "Purchase order creation, demand planning",
            "setup_time": "2-5 minutes",
        },
        "spend-analytics": {
            "description": "Analyze spending patterns and supplier concentration",
            "finds": [
                "Total spend by supplier",
                "Spend concentration analysis",
                "Supplier portfolio recommendations",
                "Consolidation opportunities",
            ],
            "output": "Spend report with vendor concentration",
            "use_case": "Strategic sourcing, supplier consolidation",
            "setup_time": "5-10 minutes (large dataset)",
        },
    }

    if workflow not in workflows:
        return _err(
            f"❌ Unknown workflow: {workflow}",
            detail=f"Valid workflows: {', '.join(workflows.keys())}",
        )

    info = workflows[workflow]
    return _ok(
        info,
        message=f"✅ Help for {workflow} workflow",
    )


def _download_instructions(workflow: str) -> str:
    return (
        f"You are a helpful procurement assistant helping the user run the {workflow} analysis.\n\n"
        f"**Workflow**: {workflow}\n"
        f"**Purpose**: Analyze procurement data and generate recommendations\n"
        f"**Output**: Excel report + JSON data saved to user's computer\n\n"
        f"**Follow these steps:**\n\n"
        f"1️⃣ **Run Analysis**\n"
        f"   Execute: `run_procurement_agent(workflow='{workflow}', engine='rules')`\n"
        f"   Wait for completion (1-5 minutes depending on data size)\n\n"
        f"2️⃣ **Verify Results**\n"
        f"   Check that the response shows:\n"
        f"   - status: 'ok'\n"
        f"   - actions_created: ≥1 (or note if 0)\n"
        f"   - json_path and excel_path values\n\n"
        f"3️⃣ **Read JSON Summary**\n"
        f"   Execute: `read_output_file('tutorial_agent_run_*.json')` (use filename from step 2)\n"
        f"   Summarize the key findings and recommendations in the chat\n\n"
        f"4️⃣ **Download Excel Report**\n"
        f"   Execute: `read_output_file('tutorial_agent_run_*.xlsx')` (use filename from step 2)\n"
        f"   The response will contain 'content' as Base64\n"
        f"   Decode the Base64 and save as: ~/Downloads/procurement_report.xlsx\n\n"
        f"5️⃣ **Confirm & Summarize**\n"
        f"   Tell the user:\n"
        f"   - Where the file was saved\n"
        f"   - Top 3 recommendations\n"
        f"   - Next steps (review with procurement team, take action, etc)\n\n"
        f"**Pro Tips:**\n"
        f"- If no exceptions found (actions_created: 0), note that data may be clean\n"
        f"- User can open the Excel file in Excel, Google Sheets, or LibreOffice\n"
        f"- Share the JSON data with other systems if needed\n"
        f"- Save the file with a date in the name (e.g., procurement_2026-03-15.xlsx)"
    )

@mcp.prompt()
def exception_triage() -> str:
    """Run the exception-triage workflow and download results locally."""
    return _download_instructions('exception-triage')

@mcp.prompt()
def late_supplier() -> str:
    """Run the late-supplier workflow and download results locally."""
    return _download_instructions('late-supplier')

@mcp.prompt()
def safety_stock() -> str:
    """Run the safety-stock workflow and download results locally."""
    return _download_instructions('safety-stock')

@mcp.prompt()
def price_anomaly() -> str:
    """Run the price-anomaly workflow and download results locally."""
    return _download_instructions('price-anomaly')

@mcp.prompt()
def demand_to_po() -> str:
    """Run the demand-to-po workflow and download results locally."""
    return _download_instructions('demand-to-po')

@mcp.prompt()
def spend_analytics() -> str:
    """Run the spend-analytics workflow and download results locally."""
    return _download_instructions('spend-analytics')


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
