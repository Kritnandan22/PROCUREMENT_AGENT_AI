# Procurement Agent AI - Workflow Instructions

This file instructs Claude on how to use the specific custom tools provided by the Procurement Agent AI MCP server. 

When you attach this file to a Claude chat or place it in your workspace, Claude will read these instructions and understand how to leverage the external MCP tools.

## How to Set Up This Agent (For the Customer)
1. **Unzip** this `thin_client` folder and keep it somewhere safe.
2. Ensure the provider has given you the **Secret Provider Password (API Key)**.
3. Rename the `.env.example` file to `.env`.
4. Open the `.env` file and replace `your_api_key_here` with your secret password.
5. Open your terminal in this folder and run `python procurement_client.py`.
6. Follow the instructions on the screen to copy the generated JSON snippet.
7. Paste that snippet into your Claude Desktop Configuration file (Settings -> Developer -> Edit Config).
8. Restart Claude!

---

## Basic Workflow (How Claude uses this)
1. Use the pre-configured MCP tools to retrieve procurement data, such as market anomalies, vendor risk assessments, or supply chain disruptions.
2. Analyze the retrieved data and produce summarized insights.
3. Recommend actions based on the specific constraints given in the chat.

*(You can customize this CLAUDE.md with your specific AI persona or system instructions.)*
