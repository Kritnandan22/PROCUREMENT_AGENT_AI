import argparse
import json
import urllib.request
import urllib.error

# The Render MCP server SSE endpoint
SERVER_URL = "https://procurement-mcp-server-yo8q.onrender.com/sse"

def check_server() -> bool:
    """Check if the Render server is awake and responding."""
    try:
        # A simple GET request to the SSE endpoint to ensure it doesn't 502/404
        req = urllib.request.Request(SERVER_URL, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in [200, 400, 405] # SSE requires specific headers, so anything but 50x is fine
        except urllib.error.HTTPError as e:
            # 405 Method Not Allowed / 400 Bad Request means the server is UP, just expects a proper MCP payload
            return True
    except Exception as e:
        return False

def main():
    parser = argparse.ArgumentParser(description="Procurement Agent Remote Client")
    parser.add_argument("--test", action="store_true", help="Test connection to the remote agent")
    args = parser.parse_args()

    print("=" * 60)
    print("🌍 Procurement Agent AI - Remote Client")
    print("=" * 60)
    
    if args.test:
        print(f"Pinging server: {SERVER_URL}...")
        is_up = check_server()
        if is_up:
            print("✅ Server is ONLINE and READY.")
        else:
            print("❌ Server is offline or waking up from sleep.")
        return

    print("To use the Procurement Agent on this machine, add it to your Claude Desktop config:")
    print("\n   1. Open Claude Desktop settings")
    print("   2. Edit your claude_desktop_config.json")
    print("   3. Add the following entry:")
    print()
    print("   {")
    print('      "mcpServers": {')
    print('          "procurement-remote": {')
    print('              "command": "npx",')
    print('              "args": [')
    print('                  "-y",')
    print('                  "@modelcontextprotocol/inspector",')
    print(f'                  "{SERVER_URL}"')
    print('              ]')
    print("          }")
    print("      }")
    print("   }")
    print("\nOr, if you use Claude Code in the terminal, simply run:")
    print(f"claude mcp add procurement-remote npx -y @modelcontextprotocol/inspector {SERVER_URL}")

if __name__ == "__main__":
    main()
