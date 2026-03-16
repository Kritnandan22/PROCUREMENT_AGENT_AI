import argparse
import json
import urllib.request
import urllib.error
import os

# Your Hosted Service URL
SERVER_URL = "https://procurement-agent-ai.onrender.com/sse"

def check_server(api_key: str = None) -> bool:
    """Check if the Render server is awake and responding."""
    try:
        url = SERVER_URL
        if api_key:
            url += f"?apiKey={api_key}"
            
        req = urllib.request.Request(url, method="GET")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
            
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in [200, 400, 405]
        except urllib.error.HTTPError as e:
            # 405 Method Not Allowed / 400 Bad Request indicates server is alive
            return True
    except Exception as e:
        return False

def main():
    parser = argparse.ArgumentParser(description="Procurement Agent Remote Client")
    parser.add_argument("--test", action="store_true", help="Test connection to the remote agent")
    parser.add_argument("--key", type=str, help="Your API key for the managed service")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("PROCUREMENT_API_KEY", "")

    print("=" * 60)
    print("🌍 Procurement Agent AI - Remote Client")
    print("=" * 60)
    
    if args.test:
        print(f"Pinging server: {SERVER_URL}...")
        is_up = check_server(api_key)
        if is_up:
            print("✅ Server is ONLINE and READY.")
        else:
            print("❌ Server is offline or unreachable.")
        return

    print("To use the Procurement Agent on this machine, add it to your Claude Desktop config:")
    print("\n   1. Open Claude Desktop settings")
    print("   2. Edit your claude_desktop_config.json")
    print("   3. Add the following entry:")
    print()
    
    # We construct the URL with the API key as a query param if it exists, or suggest passing via env
    # The exact method depends on how your Render server parses keys.
    url_to_use = SERVER_URL
    if list(api_key):
        url_to_use += f"?apiKey={api_key}"

    print("   {")
    print('      "mcpServers": {')
    print('          "procurement-remote": {')
    print('              "command": "npx",')
    print('              "args": [')
    print('                  "-y",')
    print('                  "@modelcontextprotocol/inspector",')
    print(f'                  "{url_to_use}"')
    print('              ],')
    print('              "env": {')
    print(f'                  "PROCUREMENT_API_KEY": "{api_key}"')
    print('              }')
    print("          }")
    print("      }")
    print("   }")
    print("\nOr, if you use Claude Code in the terminal, run:")
    print(f"claude mcp add procurement-remote npx -y @modelcontextprotocol/inspector {url_to_use}")

if __name__ == "__main__":
    main()
