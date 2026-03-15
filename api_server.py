"""
Simple REST API Server for Streamlit
Wraps the procurement agent in HTTP endpoints
"""

from flask import Flask, request, jsonify
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from tutorial_agentic_procurement_agent import (
    OracleReadOnlyGateway,
    TutorialProcurementAgent,
    run_agent,
)

app = Flask(__name__)

# Gateway initialized lazily (on first use, not on startup)
_gateway = None

def get_gateway():
    """Lazy initialization of gateway"""
    global _gateway
    if _gateway is None:
        _gateway = OracleReadOnlyGateway()
    return _gateway


# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Procurement Agent API Server is running",
        "version": "1.0.0"
    })


# ============================================================================
# TEST CONNECTION
# ============================================================================
@app.route("/test_connection", methods=["POST"])
def test_connection():
    try:
        gateway = get_gateway()
        result = gateway.test_connection()
        return jsonify({
            "status": "ok",
            "message": "✅ Connection successful!",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Connection failed: {str(e)}"
        }), 500


# ============================================================================
# LIST ORGANIZATION IDS
# ============================================================================
@app.route("/list_organization_ids", methods=["POST"])
def list_organization_ids():
    try:
        gateway = get_gateway()
        result = gateway.get_organizations()
        return jsonify({
            "status": "ok",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to list organizations: {str(e)}"
        }), 500


# ============================================================================
# RUN PROCUREMENT AGENT
# ============================================================================
@app.route("/run_procurement_agent", methods=["POST"])
def run_procurement_agent_endpoint():
    try:
        data = request.get_json() or {}

        workflow = data.get("workflow", "exception-triage")
        limit = data.get("limit", 10)
        autonomy_level = data.get("autonomy_level", 1)
        organization_id = data.get("organization_id")
        plan_id = data.get("plan_id")

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
            return jsonify({
                "status": "error",
                "message": f"Invalid workflow: {workflow}",
                "valid_workflows": valid_workflows
            }), 400

        # Validate autonomy level
        if autonomy_level not in [1, 2]:
            return jsonify({
                "status": "error",
                "message": "Autonomy level must be 1 or 2"
            }), 400

        # Run agent
        try:
            result = run_agent(
                workflow=workflow,
                plan_id=plan_id,
                limit=limit,
                autonomy_level=autonomy_level,
                organization_id=organization_id,
            )

            return jsonify({
                "status": "ok",
                "message": f"✅ Completed {workflow} workflow",
                "data": result
            })

        except Exception as agent_error:
            return jsonify({
                "status": "error",
                "message": f"Agent failed: {str(agent_error)}",
                "detail": str(agent_error)
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500


# ============================================================================
# GET LATEST REPORT PATHS
# ============================================================================
@app.route("/get_latest_report_paths", methods=["POST"])
def get_latest_report_paths():
    try:
        import os
        from pathlib import Path

        output_dir = Path("tutorial_agent_outputs")
        if not output_dir.exists():
            return jsonify({
                "status": "ok",
                "data": {
                    "latest_json": None,
                    "latest_excel": None
                }
            })

        json_files = sorted(output_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        excel_files = sorted(output_dir.glob("*.xlsx"), key=os.path.getmtime, reverse=True)

        return jsonify({
            "status": "ok",
            "data": {
                "latest_json": json_files[0].name if json_files else None,
                "latest_excel": excel_files[0].name if excel_files else None
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get report paths: {str(e)}"
        }), 500


# ============================================================================
# READ OUTPUT FILE
# ============================================================================
@app.route("/read_output_file", methods=["POST"])
def read_output_file():
    try:
        data = request.get_json() or {}
        filename = data.get("filename")

        if not filename:
            return jsonify({
                "status": "error",
                "message": "filename parameter required"
            }), 400

        import os
        import base64
        from pathlib import Path

        # Look in current directory first, then in tutorial_agent_outputs
        file_path = None
        if os.path.exists(filename):
            file_path = filename
        elif os.path.exists(f"tutorial_agent_outputs/{filename}"):
            file_path = f"tutorial_agent_outputs/{filename}"

        if not file_path or not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": f"File not found: {filename}",
                "detail": "Check with get_latest_report_paths() first"
            }), 404

        # Handle JSON files
        if file_path.endswith(".json"):
            with open(file_path, "r") as f:
                content = f.read()
            return jsonify({
                "status": "ok",
                "message": f"✅ JSON file ready",
                "data": {
                    "filename": filename,
                    "format": "json",
                    "content": content,
                    "size_bytes": len(content)
                }
            })

        # Handle Excel files
        elif file_path.endswith(".xlsx"):
            with open(file_path, "rb") as f:
                excel_bytes = f.read()
            base64_content = base64.b64encode(excel_bytes).decode("utf-8")
            return jsonify({
                "status": "ok",
                "message": f"✅ Excel file ready ({len(excel_bytes) / 1024:.1f} KB)",
                "data": {
                    "filename": filename,
                    "format": "base64",
                    "content": base64_content,
                    "size_bytes": len(excel_bytes),
                    "instructions": "Decode the Base64 content and save as .xlsx\nOpen with Excel, Google Sheets, or LibreOffice"
                }
            })

        else:
            return jsonify({
                "status": "error",
                "message": f"Unsupported file format: {file_path}"
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to read file: {str(e)}"
        }), 500


# ============================================================================
# LIST SAVED REPORTS
# ============================================================================
@app.route("/list_saved_reports", methods=["POST"])
def list_saved_reports():
    try:
        import os
        from pathlib import Path

        output_dir = Path("tutorial_agent_outputs")
        if not output_dir.exists():
            return jsonify({
                "status": "ok",
                "data": []
            })

        all_files = sorted(
            output_dir.glob("*"),
            key=os.path.getmtime,
            reverse=True
        )

        limit = request.get_json().get("limit", 20) if request.get_json() else 20

        files_info = []
        for f in all_files[:limit]:
            files_info.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime
            })

        return jsonify({
            "status": "ok",
            "data": files_info
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to list reports: {str(e)}"
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": [
            "POST /",
            "POST /test_connection",
            "POST /run_procurement_agent",
            "POST /get_latest_report_paths",
            "POST /read_output_file",
            "POST /list_organization_ids",
            "POST /list_saved_reports"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
