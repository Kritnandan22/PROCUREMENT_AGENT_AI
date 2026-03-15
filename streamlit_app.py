"""
Procurement Agent - Simple Web Interface
Streamlit app for non-technical users to run workflows and download Excel reports
"""

import streamlit as st
import requests
import base64
import json
from datetime import datetime
from io import BytesIO
import pandas as pd

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Procurement Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================
if "mcp_server_url" not in st.session_state:
    st.session_state.mcp_server_url = ""
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_excel_base64" not in st.session_state:
    st.session_state.last_excel_base64 = None
if "last_excel_filename" not in st.session_state:
    st.session_state.last_excel_filename = None

# ============================================================================
# SIDEBAR - SERVER CONFIGURATION
# ============================================================================
st.sidebar.title("⚙️ Server Configuration")

# Get server URL from environment or user input
import os
default_url = os.getenv("API_SERVER_URL", "https://procurement-api.onrender.com")

server_url = st.sidebar.text_input(
    "API Server URL",
    value=default_url,
    placeholder="https://procurement-api.onrender.com"
)
st.session_state.mcp_server_url = server_url

# Test connection button
if st.sidebar.button("🔗 Test Connection", use_container_width=True):
    try:
        with st.spinner("Testing connection..."):
            response = requests.post(
                f"{server_url}/test_connection",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                st.sidebar.success("✅ Connection successful!")
                st.sidebar.json(data.get("data", {}))
            else:
                st.sidebar.error(f"❌ Connection failed: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {str(e)}")

st.sidebar.divider()

# ============================================================================
# MAIN PAGE
# ============================================================================
st.title("📊 Procurement Agent")
st.markdown("**Run analysis and download Excel reports directly**")

# ============================================================================
# TABS
# ============================================================================
tab1, tab2, tab3 = st.tabs(["🚀 Run Analysis", "📋 Results", "ℹ️ Help"])

# ============================================================================
# TAB 1: RUN ANALYSIS
# ============================================================================
with tab1:
    st.subheader("Select Analysis Parameters")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Organization")
        org_option = st.radio(
            "Choose organization:",
            ["Use Default", "Select Specific Organization"],
            label_visibility="collapsed"
        )

        organization_id = None
        if org_option == "Select Specific Organization":
            org_input = st.number_input(
                "Enter Organization ID:",
                min_value=1,
                value=1
            )
            organization_id = org_input
            st.info(f"📍 Organization ID: {organization_id}")
        else:
            st.info("📍 Using default organization from database")

    with col2:
        st.markdown("### Workflow")
        workflow = st.selectbox(
            "Select workflow:",
            [
                "exception-triage",
                "late-supplier",
                "safety-stock",
                "price-anomaly",
                "demand-to-po",
                "spend-analytics"
            ],
            label_visibility="collapsed"
        )

        workflow_descriptions = {
            "exception-triage": "🚨 Find procurement issues (late POs, shortages, excess inventory)",
            "late-supplier": "⏰ Identify suppliers delivering late",
            "safety-stock": "📦 Check inventory below safety levels",
            "price-anomaly": "💰 Detect unusual pricing issues",
            "demand-to-po": "🔄 Convert demand to PO recommendations",
            "spend-analytics": "📊 Analyze spending patterns and risks"
        }

        st.info(workflow_descriptions.get(workflow, ""))

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        limit = st.slider("Result Limit:", min_value=5, max_value=100, value=10)

    with col2:
        autonomy = st.radio(
            "Autonomy Level:",
            [1, 2],
            format_func=lambda x: f"Level {x} - " + ("Read-Only" if x == 1 else "Draft PO Creation"),
            horizontal=True
        )

    with col3:
        st.empty()

    st.divider()

    # ========================================================================
    # RUN BUTTON
    # ========================================================================
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("▶️ RUN ANALYSIS", use_container_width=True, type="primary"):
            if not server_url:
                st.error("❌ Please enter MCP Server URL first")
            else:
                try:
                    with st.spinner(f"⏳ Running {workflow} workflow..."):
                        # Call MCP server
                        payload = {
                            "workflow": workflow,
                            "limit": limit,
                            "autonomy_level": autonomy,
                        }

                        if organization_id:
                            payload["organization_id"] = organization_id

                        response = requests.post(
                            f"{server_url}/run_procurement_agent",
                            json=payload,
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.last_results = result

                            # Display results
                            st.markdown('<div class="success-box">', unsafe_allow_html=True)
                            st.success("✅ Analysis completed successfully!")
                            st.markdown('</div>', unsafe_allow_html=True)

                            # Show metrics
                            if "data" in result:
                                data = result["data"]

                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Actions Created", data.get("actions_created", 0))
                                with col2:
                                    st.metric("Organization", data.get("organization_id", "Default"))
                                with col3:
                                    st.metric("Autonomy Level", data.get("autonomy_level", "N/A"))
                                with col4:
                                    status = "✅ Clean Data" if not data.get("has_results") else "⚠️ Issues Found"
                                    st.metric("Status", status)

                                # Action summary
                                if data.get("action_summary"):
                                    st.subheader("Action Summary")
                                    col1, col2, col3 = st.columns(3)
                                    for idx, (action, count) in enumerate(data["action_summary"].items()):
                                        if idx % 3 == 0:
                                            col1.metric(action, count)
                                        elif idx % 3 == 1:
                                            col2.metric(action, count)
                                        else:
                                            col3.metric(action, count)

                                # Get Excel file
                                if data.get("excel_path"):
                                    st.info("📥 Fetching Excel file...")
                                    try:
                                        excel_response = requests.post(
                                            f"{server_url}/read_output_file",
                                            json={"filename": data["excel_path"].split("/")[-1]},
                                            timeout=10
                                        )

                                        if excel_response.status_code == 200:
                                            excel_data = excel_response.json()
                                            if "data" in excel_data and "content" in excel_data["data"]:
                                                # Store base64 for download
                                                st.session_state.last_excel_base64 = excel_data["data"]["content"]
                                                st.session_state.last_excel_filename = excel_data["data"]["filename"]

                                                st.success(f"✅ Excel file ready: {excel_data['data']['filename']}")
                                    except Exception as e:
                                        st.warning(f"⚠️ Could not fetch Excel file: {str(e)}")
                        else:
                            st.error(f"❌ Error: {response.status_code}")
                            if response.text:
                                st.error(response.text)

                except requests.exceptions.Timeout:
                    st.error("❌ Server timeout - taking too long to respond")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: RESULTS & DOWNLOAD
# ============================================================================
with tab2:
    if st.session_state.last_results:
        st.subheader("📊 Latest Results")

        result = st.session_state.last_results
        data = result.get("data", {})

        # Display full results as JSON
        with st.expander("View Full JSON Results"):
            st.json(result)

        st.divider()

        # Excel Download
        st.subheader("📥 Download Excel Report")

        if st.session_state.last_excel_base64:
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                # Decode base64 and create download button
                excel_bytes = base64.b64decode(st.session_state.last_excel_base64)

                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=excel_bytes,
                    file_name=st.session_state.last_excel_filename or "report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            st.success(f"✅ Click button above to download: {st.session_state.last_excel_filename}")
            st.info(f"📦 File size: {len(excel_bytes) / 1024:.1f} KB")
        else:
            st.info("No Excel file available yet. Run an analysis first in the 'Run Analysis' tab.")
    else:
        st.info("No results yet. Run an analysis in the 'Run Analysis' tab to see results here.")

# ============================================================================
# TAB 3: HELP
# ============================================================================
with tab3:
    st.subheader("📖 How to Use")

    st.markdown("""
    ### Step 1: Configure Server
    - Enter the MCP server URL in the left sidebar
    - Click "Test Connection" to verify it works

    ### Step 2: Select Parameters
    - Choose an **organization** (default or specific ID)
    - Select a **workflow** to run
    - Set **result limit** (how many records to analyze)

    ### Step 3: Run Analysis
    - Click **"RUN ANALYSIS"** button
    - Wait for results (usually 2-5 seconds)

    ### Step 4: Download Excel
    - Go to **"Results"** tab
    - Click **"Download Excel Report"** button
    - File saves to your Downloads folder
    - Open with Excel, Google Sheets, or LibreOffice
    """)

    st.divider()

    st.subheader("🔄 Available Workflows")

    workflows_help = {
        "exception-triage": {
            "desc": "Find procurement issues",
            "finds": ["Late/past due POs", "Items below safety stock", "Excess inventory", "Short shipments"]
        },
        "late-supplier": {
            "desc": "Identify supplier performance issues",
            "finds": ["Suppliers with late deliveries", "Performance trends", "Lead time breaches"]
        },
        "safety-stock": {
            "desc": "Check inventory levels",
            "finds": ["Items below safety stock (shortage)", "Items above safety stock (excess)"]
        },
        "price-anomaly": {
            "desc": "Detect pricing issues",
            "finds": ["Unusual price changes", "Price outliers", "Pricing discrepancies"]
        },
        "demand-to-po": {
            "desc": "Convert demand to purchase orders",
            "finds": ["Unmet demand", "PO recommendations", "Lead time calculations"]
        },
        "spend-analytics": {
            "desc": "Analyze spending patterns",
            "finds": ["Maverick spend", "Single-source risks", "Supplier concentration", "Spending insights"]
        }
    }

    for wf, info in workflows_help.items():
        with st.expander(f"**{wf}** - {info['desc']}"):
            st.write("**Finds:**")
            for item in info["finds"]:
                st.write(f"- {item}")

    st.divider()

    st.subheader("💡 Tips for Non-Technical Users")

    st.markdown("""
    - **Don't have organization ID?** Use "Use Default" option
    - **No results?** Data might be clean - that's good!
    - **Excel file won't open?** Make sure you have Excel, Google Sheets, or LibreOffice installed
    - **Server not responding?** Check the URL and click "Test Connection"
    - **Want different results?** Try "spend-analytics" for broader insights
    """)

    st.divider()

    st.subheader("🆘 Troubleshooting")

    issues = {
        "Server URL not working": "Check with your IT admin for correct server URL",
        "Test Connection fails": "Make sure your network can reach the server",
        "Analysis returns 0 results": "Your data might be clean - try a different workflow",
        "Excel file won't download": "Try a different browser or check your firewall",
        "Can't open Excel file": "Install Excel, Google Sheets, or LibreOffice"
    }

    for issue, solution in issues.items():
        with st.expander(f"❓ {issue}"):
            st.write(f"**Solution:** {solution}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <p>Procurement Agent v1.0 | Powered by Streamlit & Oracle EBS</p>
    <p>All data is read-only. No modifications to procurement system.</p>
</div>
""", unsafe_allow_html=True)
