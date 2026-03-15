# Procurement Agent MCP - User Setup Guide

## What This Agent Does

The Procurement Agent is an **AI-powered procurement analysis tool** that:
- ✅ Identifies procurement exceptions (late suppliers, excess inventory, safety stock issues)
- ✅ Analyzes supplier performance
- ✅ Detects pricing anomalies
- ✅ Recommends draft purchase orders
- ✅ Provides spend analytics

**Output**: Excel and JSON reports with actionable recommendations

---

## Quick Start (5 minutes)

### Step 1: Add MCP Server to Claude Desktop

**File location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Add this block** (replace existing mcpServers if needed):
```json
{
  "mcpServers": {
    "procurement-agent": {
      "url": "https://procurement-agent-ai.onrender.com/sse",
      "transport": "sse"
    }
  }
}
```

**Restart Claude Desktop** — the tools will appear.

### Step 2: Test Connection

In Claude, run:
```
I want to test the procurement agent connection
```

If it works, you'll see ✅ DB info returned.

### Step 3: Configure Oracle Credentials

You need these 7 environment variables set:

```bash
export DB_HOST="your-oracle-server.example.com"
export DB_PORT="1521"
export DB_SID="PROD"              # OR DB_SERVICE_NAME
export DB_SERVICE_NAME=""          # Leave blank if using SID
export APPS_USER="apps"
export APPS_PASSWORD="YourSecurePassword"
export ORACLE_CLIENT_PATH="/path/to/oracle/client"  # Optional
```

**Where to find these?**
- Contact your Oracle EBS database administrator
- DB_HOST: Your server IP/hostname
- DB_PORT: Usually 1521
- DB_SID/SERVICE_NAME: Ask your DBA
- APPS_USER/PASSWORD: Your EBS login credentials
- ORACLE_CLIENT_PATH: Only needed if Oracle client not in PATH

### Step 4: Run the Agent

In Claude, ask:
```
Run the procurement agent to analyze exceptions
```

Wait 30-60 seconds for analysis to complete.

---

## How to Use the Agent

### Command 1: Run Exception Triage (Most Common)
```
Run the procurement agent to identify exception items and recommend actions
```

**What it does**:
- Finds items with no activity
- Detects excess inventory
- Identifies safety stock issues
- Recommends supplier changes

**Output**: Excel with exception list + recommendations

---

### Command 2: Get the Latest Report

```
Show me the latest procurement agent report
```

**Returns**: Path to the most recent JSON/Excel output

---

### Command 3: Download Your Report

```
I need to download the procurement agent Excel file to my computer
```

**Claude will**:
1. Find the latest report on the server
2. Decode the Base64 file
3. Save it to your Downloads folder

---

## Understanding the Output

### Excel Report Contains:

| Sheet | Content | Use Case |
|-------|---------|----------|
| **Exception Summary** | Overview of all exceptions found | Executive summary |
| **Exception Details** | Full line-by-line analysis | Detailed investigation |
| **Supplier Options** | Alternative suppliers for items | Supplier switching |
| **Action Recommendations** | Draft POs or negotiation actions | Procurement decisions |
| **Metadata** | Run date, records processed, version | Audit trail |

### JSON Report Contains:

```json
{
  "status": "ok",
  "data": {
    "workflow": "exception-triage",
    "plan_id": null,
    "actions_created": 2,
    "action_summary": {
      "recommend_draft_po": 2
    },
    "details": [
      {
        "item_id": 12345,
        "exception_type": "Late Supplier",
        "severity": "HIGH",
        "recommended_action": "Switch to backup supplier",
        "suppliers": [ ... ]
      }
    ]
  }
}
```

---

## Troubleshooting

### Problem: "Connection timeout" error

**Cause**: Render server is waking up (first run of the day)

**Solution**: Wait 30-60 seconds and try again. Cold start takes time.

---

### Problem: "ORA-00903: Invalid table name"

**Cause**: Table schema mismatch (Oracle EBS configuration issue)

**Solution**:
1. Verify APPS_USER has correct permissions
2. Check that you're pointing to the right Oracle instance
3. Confirm all table names exist in your schema

---

### Problem: "Missing environment variables"

**Cause**: DB_HOST, APPS_USER, or APPS_PASSWORD not set

**Solution**: Set all 7 variables listed in Step 3 above

```bash
# Verify they're set:
echo $DB_HOST
echo $APPS_USER
# etc
```

---

### Problem: Empty results (0 exceptions found)

**Cause 1**: No exceptions in your data (actually good!)
**Cause 2**: Data hasn't been refreshed yet
**Cause 3**: Running against wrong organization

**Solution**:
- Check when your EBS data was last refreshed
- Ask DBA to confirm you're looking at the right org
- Try running again tomorrow with newer data

---

### Problem: "Request timed out"

**Cause**: Query is taking >5 minutes (too much data)

**Solution**:
- Run during off-peak hours
- Ask DBA to optimize your data
- Use a larger plan_id limit

---

## When to Run the Agent

### Daily/Weekly:
- Check for new exceptions
- Monitor supplier performance
- Track pricing anomalies

### Monthly:
- Full spend analytics
- Supplier consolidation analysis
- Safety stock optimization

### As Needed:
- After major supply disruptions
- Before supplier negotiations
- For ad-hoc analysis

---

## How the Agent Makes Decisions

The agent uses **Oracle EBS data** to analyze:

1. **Supplier Performance**: On-time delivery rate, lead times
2. **Inventory**: Safety stock levels, excess inventory flags
3. **Demand**: Sales orders, forecasts, actual demand
4. **Pricing**: Contract prices vs. actual paid prices

**Recommendations** are based on:
- Supplier on-time rate (threshold: 80%)
- Price deviation from baseline (threshold: 10-20%)
- Inventory turns and safety stock ratios
- Lead time variance

---

## Important Limitations

⚠️ **Know Before Using**:

1. **Ephemeral Storage**: Output files deleted after 15 minutes of inactivity
   - Solution: Download immediately after running

2. **Cold Start**: First request may take 30-60 seconds
   - The Render server wakes up from sleep
   - Subsequent requests are fast

3. **Read-Only Analysis**: Agent recommends but doesn't create POs
   - You must manually approve and create POs
   - Future version will support automation

4. **Single Workflow**: Only exception-triage is active
   - Can't yet run safety stock or spend analytics separately
   - Will be added in next version

5. **Data Freshness**: Results depend on Oracle data
   - Stale data = stale recommendations
   - Ask your DBA when data is refreshed daily

---

## Best Practices

✅ **DO**:
- Run during off-peak business hours
- Download reports immediately (don't rely on server storage)
- Review exceptions before taking action
- Validate recommendations with procurement team
- Keep monthly archive of reports

❌ **DON'T**:
- Expect 100% automation (AI supports human decisions)
- Trust anomalies without context (some items are exceptions by design)
- Run continuously (once/day is enough)
- Use for transactional updates (read-only tool)
- Assume supplier data is 100% accurate

---

## Data Privacy & Security

- **Your data**: Stays on the Render server (not shared)
- **Credentials**: Stored as environment variables only
- **Output files**: Deleted after 15 minutes
- **Logs**: Available on Render dashboard
- **No personal data**: Agent only sees item/supplier/org IDs

---

## Support & Questions

If something goes wrong:

1. **Check troubleshooting guide** above
2. **Verify environment variables** are set correctly
3. **Test connection** first before running analysis
4. **Check Render status** at https://status.render.com
5. **Contact your Oracle DBA** for data/permission issues

---

## Next Steps

After you're set up:
- [ ] Test connection (verify DB_* variables work)
- [ ] Run exception triage (analyze your data)
- [ ] Download report and review
- [ ] Share findings with procurement team
- [ ] Validate recommendations against business rules

**Ready? Ask Claude:**
> "Test the procurement agent connection and then run an exception analysis"

Enjoy! 🚀
