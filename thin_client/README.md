# Procurement Agent AI - Thin Client

This folder contains everything your customers need to connect to your hosted Procurement Agent AI MCP server.

## Contents
1. **`CLAUDE.md`** - Includes system instructions for Claude so it knows how to use your procurement tools.
2. **`.env.example`** - Where the customer enters the API key you provide them.
3. **`.mcp.json`** - A pre-configured MCP configuration pointing to your server.
4. **`procurement_client.py`** - A helper script to test the connection and generate the string to paste into Claude Desktop.

## Usage Instructions for Your Customers

1. **Set Up the API Key on Render (FOR YOU - The Host)**
   Before sharing this folder, securely log in to your Render dashboard, navigate to your \`procurement-mcp-server\` Environment Variables, and add a new secret:
   * **Key:** \`PROCUREMENT_API_KEY\`
   * **Value:** *(Create a secure, random password/string)*
   Click "Save and Deploy".

2. **Give the Customer their API Key**
   Send the securely generated string to the customer privately.

3. **Customer Sets up `.env`**
   The customer should rename \`.env.example\` to \`.env\` and paste their assigned API Key.

4. **Test the Connection**
   Have the user run the test script to ensure their machine can reach your server:
   ```bash
   python procurement_client.py --test --key "YOUR_API_KEY_HERE"
   ```

3. **Install it in Claude Desktop**
   Have the user run the script to see the exact JSON configuration to add to their Claude Desktop:
   ```bash
   python procurement_client.py --key "YOUR_API_KEY_HERE"
   ```
   They should open their Claude Desktop Settings -> Developer, Edit Config, and paste the generated JSON snippet into the `mcpServers` section.
