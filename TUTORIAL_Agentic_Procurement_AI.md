# Intelligent Agentic Procurement AI — Beginner's Tutorial

> **Pre-requisite:** MCP server connected to Oracle EBS (apps/apps @ 161.118.185.249:1521/EBSDB)
> This tutorial uses real data already confirmed in this instance:
> 27,298 PO Headers · 118,911 PO Lines · 217,419 Schedules · 140 MSC Plans

---

## Table of Contents

1. [What is Agentic AI?](#1-what-is-agentic-ai)
2. [The Big Picture Architecture](#2-the-big-picture-architecture)
3. [Oracle EBS Procurement Data Model](#3-oracle-ebs-procurement-data-model)
4. [The PO Lifecycle](#4-the-po-lifecycle)
5. [Supply Planning (MSC) and How It Drives Procurement](#5-supply-planning-msc-and-how-it-drives-procurement)
6. [Key Tables Reference](#6-key-tables-reference)
7. [How the MCP Server Bridges AI and Oracle](#7-how-the-mcp-server-bridges-ai-and-oracle)
8. [The 6 Agentic Procurement Workflows](#8-the-6-agentic-procurement-workflows)
9. [Data Flow: From Exception to Purchase Order](#9-data-flow-from-exception-to-purchase-order)
10. [Hands-On Queries to Try](#10-hands-on-queries-to-try)

---

## 1. What is Agentic AI?

Traditional software asks: **"What should I do?"** and waits for human input.

Agentic AI asks: **"What needs to be done?"** — then plans, acts, and reports back.

```
TRADITIONAL SYSTEM                    AGENTIC AI SYSTEM
=====================                 =====================
Human   --> clicks button             AI observes DB changes
System  --> runs one report           AI decides what matters
Human   --> reads report              AI takes action (or recommends)
Human   --> decides what to do        AI logs decision + rationale
Human   --> manually creates PO       AI creates draft PO
                                      Human  --> approves/rejects
```

### The 4 Levels of Autonomy

```
Level 0: INFORM        "Here is what I found."
           |
Level 1: RECOMMEND     "Here is what I found + what you should do."
           |
Level 2: ACT + INFORM  "I did it + here is what I did and why."
           |
Level 3: AUTONOMOUS    "I did it. Log available if you want to audit."
```

> **Start at Level 0-1.** Build trust before giving the AI Level 2-3 autonomy.

---

## 2. The Big Picture Architecture

```
+------------------------------------------------------------------+
|                    AGENTIC PROCUREMENT AI                        |
+------------------------------------------------------------------+
|                                                                  |
|   +-------------+     +-----------+     +--------------------+  |
|   |   CLAUDE /  |     |    MCP    |     |   ORACLE EBS       |  |
|   |   LLM Agent |<--->|   SERVER  |<--->|   Database         |  |
|   +-------------+     +-----------+     +--------------------+  |
|         |                                     |                  |
|         |                            +--------+--------+         |
|         |                            |                 |         |
|         v                    +-------+------+  +-------+------+  |
|   +----------+               | PROCUREMENT  |  |   PLANNING   |  |
|   | Decision |               | PO_HEADERS   |  |  MSC_PLANS   |  |
|   | Engine   |               | PO_LINES     |  |  MSC_DEMANDS |  |
|   +----------+               | PO_SCHEDULES |  |  MSC_SUPPLIES|  |
|         |                    +--------------+  +--------------+  |
|         v                                                         |
|   +----------+                                                    |
|   |  Action  |  --> Create Draft PO                              |
|   |  Layer   |  --> Send Alerts                                   |
|   +----------+  --> Update Plans                                  |
|                 --> Generate Reports                              |
+------------------------------------------------------------------+
```

### Components Explained

| Component | What it does |
|---|---|
| **LLM Agent (Claude)** | Reads data, understands context, decides actions |
| **MCP Server** | Secure bridge between AI and Oracle — no direct DB access from AI |
| **Oracle EBS** | System of record — all procurement and planning data lives here |
| **Decision Engine** | Rules + AI logic to rank actions by priority and risk |
| **Action Layer** | Executes approved actions back into Oracle (write-back) |

---

## 3. Oracle EBS Procurement Data Model

### The Star Schema for Procurement

```
                          +------------------+
                          |   PO_VENDORS     |
                          |  (Suppliers)     |
                          |  vendor_id  (PK) |
                          |  vendor_name     |
                          +--------+---------+
                                   |
                          BELONGS_TO (vendor_id)
                                   |
+------------------+     +---------v---------+     +------------------+
|  PO_VENDOR_SITES |     |  PO_HEADERS_ALL   |     |  HR_LOCATIONS    |
|  (Supplier Sites)|<----+  po_header_id(PK) +---->|  (Ship-to Loc)   |
|  vendor_site_id  |     |  segment1 = PO#   |     |  location_id     |
+------------------+     |  vendor_id (FK)   |     +------------------+
                          |  org_id           |
                          |  status_code      |
                          |  currency_code    |
                          |  creation_date    |
                          +---------+---------+
                                    |
                           HAS_MANY (po_header_id)
                                    |
                          +---------v---------+
                          |  PO_LINES_ALL     |
                          |  po_line_id  (PK) |
                          |  po_header_id(FK) |
                          |  line_num         |
                          |  item_id          |
                          |  unit_price       |
                          |  quantity         |
                          +---------+---------+
                                    |
                           HAS_MANY (po_line_id)
                                    |
                          +---------v---------+
                          | PO_LINE_LOCATIONS |   <-- "Schedules"
                          |  line_location_id |
                          |  po_line_id  (FK) |
                          |  need_by_date     |
                          |  quantity_ordered |
                          |  quantity_received|
                          |  ship_to_location |
                          +---------+---------+
                                    |
                           HAS_MANY (line_location_id)
                                    |
                          +---------v---------+
                          | PO_DISTRIBUTIONS  |
                          |  distribution_id  |
                          |  charge_account   |
                          |  quantity_ordered |
                          |  project_id       |
                          +-------------------+
```

### Row Counts From Your Instance

```
PO_HEADERS_ALL      =   27,298  (each = one Purchase Order)
PO_LINES_ALL        =  118,911  (avg 4.4 lines per PO)
PO_LINE_LOCATIONS   =  217,419  (avg 1.8 schedules per line)
```

---

## 4. The PO Lifecycle

```
DEMAND              PLANNING             PROCUREMENT           RECEIVING
========            ========             ===========           =========

Sales Order  -->  MSC_DEMANDS  -->  MSC_SUPPLIES      -->   GRN / Receipt
                  (Demand)         (Planned Order)
                                        |
                                   [AI Decision]
                                        |
                              Draft PO Created
                          (PO_HEADERS: status=DRAFT)
                                        |
                               Buyer Reviews
                                        |
                          Approved PO Sent to Supplier
                          (PO_HEADERS: status=APPROVED)
                                        |
                             Supplier Acknowledges
                                        |
                              Goods Shipped/Received
                          (PO_LINE_LOCATIONS: qty_received++)
                                        |
                               Invoice Matched
                                        |
                              Payment Released
```

### PO Status Flow

```
  DRAFT -----> INCOMPLETE -----> IN PROCESS -----> APPROVED -----> CLOSED
    |                                                  |
    |                                            CANCELLED
    v
  REJECTED
```

### Key Status Codes in Oracle EBS

| Status | Meaning | AI Action |
|---|---|---|
| `DRAFT` | PO created, not submitted | Watch for stale drafts |
| `IN PROCESS` | Submitted for approval | Alert if approval delayed |
| `APPROVED` | Active PO | Monitor delivery dates |
| `CLOSED` | Fully received and matched | Archive |
| `FINALLY CLOSED` | No further action | Archive |
| `CANCELLED` | Terminated | Flag for re-procurement |
| `INCOMPLETE` | Missing required fields | Alert buyer |

---

## 5. Supply Planning (MSC) and How It Drives Procurement

```
ORACLE ASCP / MSC PLANNING ENGINE
==================================

  INPUTS                    ENGINE                   OUTPUTS
  ------                    ------                   -------
  Demand Forecasts          +----------+             Planned Orders
  Sales Orders       --->   |  MSC     |  --->       (MSC_SUPPLIES)
  Inventory Levels          | Planning |             Exceptions
  BOM / Routing             | Engine   |             (MSC_EXCEPTION_DETAILS)
  Supplier Lead Times       +----------+             Pegging
  Resource Capacity                                  (MSC_FULL_PEGGING)
```

### The Planning Hierarchy

```
MSC_PLANS  (140 plans in your instance)
    |
    +-- MSC_DEMANDS         (1,226,360 rows)  <-- What is needed?
    |       |
    |       +-- Sales Orders, Forecasts, Safety Stock targets
    |
    +-- MSC_SUPPLIES        (606,290 rows)    <-- What is available/planned?
    |       |
    |       +-- On Hand, POs, WOs, Planned Orders
    |
    +-- MSC_EXCEPTION_DETAILS (199,190 rows)  <-- What is WRONG?
    |       |
    |       +-- Late, Short, Excess, Cancelled, etc.
    |
    +-- MSC_FULL_PEGGING    (1,445,420 rows)  <-- Why is demand there?
            |
            +-- Traces demand back to root cause
```

### Exception Types — What the AI Watches

```
SUPPLY EXCEPTIONS                   DEMAND EXCEPTIONS
=================                   =================
1  = Items with no activity         11 = Orders at risk
2  = Late replenishment orders      12 = Orders past due
3  = Items below safety stock       13 = Demand not satisfied
4  = Excess inventory               14 = Late demand
5  = Expired lots
6  = Past due POs                   RESOURCE EXCEPTIONS
7  = Cancelled POs                  ===================
8  = Short shipments                21 = Resource overloaded
9  = Supplier capacity breach       22 = Resource underloaded
10 = Lead time breach               23 = Resource unavailable
```

> **Your top exception plan is "Windows" with 42,060 exceptions.**
> An AI agent would triage these, prioritize by revenue impact, and act.

---

## 6. Key Tables Reference

### Procurement Tables

```
+---------------------------+------------------------------------------+
| TABLE                     | PURPOSE                                  |
+---------------------------+------------------------------------------+
| PO_HEADERS_ALL            | One row per Purchase Order               |
| PO_LINES_ALL              | Line items within each PO                |
| PO_LINE_LOCATIONS_ALL     | Delivery schedules per line              |
| PO_DISTRIBUTIONS_ALL      | Accounting distributions                 |
| PO_VENDORS                | Supplier master                          |
| PO_VENDOR_SITES_ALL       | Supplier addresses/sites                 |
| PO_VENDOR_CONTACTS        | Supplier contacts                        |
| PO_REQUISITION_HEADERS    | Purchase Requisitions (pre-PO)           |
| PO_REQUISITION_LINES_ALL  | Requisition line items                   |
| PO_RELEASES_ALL           | Blanket PO releases                      |
| PO_AGREEMENTS             | Blanket/Contract Purchase Agreements     |
| RCV_SHIPMENT_HEADERS      | Receiving (GRN) headers                  |
| RCV_TRANSACTIONS          | Individual receipt transactions          |
| AP_INVOICES_ALL           | AP Invoice matched to PO                 |
+---------------------------+------------------------------------------+
```

### Planning Tables

```
+---------------------------+------------------------------------------+
| TABLE                     | PURPOSE                                  |
+---------------------------+------------------------------------------+
| MSC_PLANS                 | Plan definitions (140 plans)             |
| MSC_DEMANDS               | All demand records per plan              |
| MSC_SUPPLIES              | All supply records per plan              |
| MSC_EXCEPTION_DETAILS     | Planning exceptions (alerts)             |
| MSC_FULL_PEGGING          | Demand-to-supply trace chains            |
| MSC_SYSTEM_ITEMS          | Items within the plan                    |
| MSC_SUPPLIER_CAPACITIES   | Supplier capacity constraints            |
| MSC_SAFETY_STOCKS         | Safety stock targets per item/org        |
| MSC_SOURCING_RULES        | Where to buy/make each item              |
| MSC_ITEM_SUPPLIERS        | Item-supplier relationships              |
| MSC_BOM_COMPONENTS        | Bill of Materials                        |
| MSC_RESOURCE_REQUIREMENTS | Capacity requirements per planned order  |
+---------------------------+------------------------------------------+
```

---

## 7. How the MCP Server Bridges AI and Oracle

```
WITHOUT MCP (dangerous)            WITH MCP (safe)
====================               ==========================

AI Agent                           AI Agent
   |                                  |
   | raw SQL                          | natural language tool call
   v                                  v
Oracle DB  <-- direct access       MCP Server
(no audit, no safety)                 |
                                      | controlled query
                                      v
                                   Oracle DB
                                      |
                                      | structured JSON
                                      v
                                   AI Agent  <-- safe, audited response
```

### MCP Tools Available in This Project

```
oracle-ebs MCP Server
|
+-- test_connection()
|       Returns: DB version, user, timestamp
|
+-- get_db_info()
|       Returns: Instance metadata, NLS settings, pool stats
|
+-- list_tables(schema, name_filter)
|       Returns: Table list with row counts
|
+-- execute_query(sql, max_rows)
|       Returns: SELECT results as JSON (read-only, max 1000 rows)
|
+-- describe_table(table_name, schema)
        Returns: Column definitions and comments
```

### How an Agent Uses MCP

```python
# Agent "thinking":
# "I need to find all overdue purchase orders"

result = mcp.execute_query("""
    SELECT ph.segment1 AS po_number,
           ph.vendor_id,
           pll.need_by_date,
           pll.quantity_ordered - pll.quantity_received AS qty_outstanding
    FROM   po_headers_all ph
    JOIN   po_line_locations_all pll ON pll.po_header_id = ph.po_header_id
    WHERE  pll.need_by_date < SYSDATE
    AND    pll.quantity_received < pll.quantity_ordered
    AND    ph.status_lookup_code = 'APPROVED'
""")

# Agent then decides:
# -> Send alert to buyer
# -> Escalate if overdue > 7 days
# -> Log decision with rationale
```

---

## 8. The 6 Agentic Procurement Workflows

### Workflow 1: Exception Triage

```
TRIGGER: New exceptions in MSC_EXCEPTION_DETAILS
         |
         v
    AI reads exceptions
         |
         v
    Classify by type + severity
         |
    +----+----+
    |         |
  HIGH      LOW/MED
  RISK       RISK
    |         |
    v         v
 Escalate   Add to
 to Buyer   worklist
    |
    v
 Create urgent
 follow-up PO
```

### Workflow 2: Late Supplier Detection

```
Every day:
    Query PO_LINE_LOCATIONS where:
        - need_by_date < SYSDATE + 3 days
        - quantity_received < quantity_ordered
        - status = APPROVED
             |
             v
    For each late PO line:
        Check supplier history (on-time rate)
             |
        +----+------+
        |           |
    Chronic      First
    Late         Offence
        |           |
        v           v
    Flag for     Send
    supplier     reminder
    review       alert
        |
        v
    Recommend
    alternate
    supplier
    (from MSC_ITEM_SUPPLIERS)
```

### Workflow 3: Safety Stock Alert

```
MSC_SAFETY_STOCKS has target levels
MSC_SUPPLIES has current on-hand
         |
         v
    AI compares:
    on_hand_qty vs safety_stock_qty
         |
    +----+-------+
    |             |
  BELOW         ABOVE
  SAFETY        SAFETY
  STOCK         STOCK
    |             |
    v             v
  Create        Flag as
  urgent        excess
  requisition   inventory
    |
    v
  Route to
  approved
  supplier
  (cheapest + fastest)
```

### Workflow 4: Price Anomaly Detection

```
AI monitors PO_LINES_ALL.unit_price
    |
    v
Compare against:
  - Historical avg price (last 12 months)
  - Contract price (PO_AGREEMENTS)
  - Market benchmark
    |
    v
If price deviation > threshold:
    |
    +-- Flag for buyer review
    +-- Suggest renegotiation
    +-- Check if blanket agreement exists
```

### Workflow 5: Demand-to-PO Tracing (Pegging)

```
Customer Order (Sales Order)
    |
    v
MSC_FULL_PEGGING
    |
    v
Planned Order (MSC_SUPPLIES, order_type=5)
    |
    v
[AI checks: has a real PO been created?]
    |
    +-- YES --> Monitor delivery
    |
    +-- NO  --> Create draft PO from planned order
                  |
                  v
               Write to Oracle via MCP
               (POST /draftPurchaseOrders)
```

### Workflow 6: Spend Analytics

```
PO_HEADERS_ALL  +  PO_LINES_ALL  +  PO_DISTRIBUTIONS_ALL
                         |
                         v
              AI aggregates spend by:
              - Supplier
              - Category
              - Business Unit
              - Time period
                         |
                         v
              Identify:
              - Top 10 suppliers by spend
              - Maverick spend (no contract)
              - Single-source risk items
              - Consolidation opportunities
```

---

## 9. Data Flow: From Exception to Purchase Order

```
Step 1: Planning Run
========================================
MSC Planning Engine runs
        |
        v
Planned Orders created in MSC_SUPPLIES
(order_type = 5 = "Planned Purchase Order")

Step 2: Exception Detected
========================================
MSC_EXCEPTION_DETAILS row created
  exception_type = 2 (Late Replenishment)
  inventory_item_id = 12345
  date1 = need_by_date
  quantity = shortage qty

Step 3: AI Agent Reads Exception
========================================
MCP Tool: execute_query()
  SELECT e.*, i.item_number, i.description
  FROM msc_exception_details e
  JOIN msc_system_items i ON i.inventory_item_id = e.inventory_item_id
  WHERE e.plan_id = 74032  -- UNCONS plan

Step 4: AI Evaluates
========================================
- Revenue at risk? (join to sales orders via pegging)
- Alternate suppliers available? (MSC_ITEM_SUPPLIERS)
- Lead time acceptable? (PO_VENDOR_SITES.lead_time)
- Budget available? (PO_DISTRIBUTIONS budget check)

Step 5: AI Recommends / Acts
========================================
Level 1: "Recommend creating PO for item 12345,
          qty 500, from supplier ABC Corp,
          need-by 2026-04-01"

Level 2: Creates draft PO in Oracle
         Notifies buyer for approval

Step 6: Write-Back to Oracle
========================================
MCP Tool: (future) create_draft_po()
  POST /draftPurchaseOrders
  {
    "vendor_id": 1234,
    "item_id": 12345,
    "quantity": 500,
    "need_by_date": "2026-04-01"
  }

Step 7: Audit Trail
========================================
Every action logged with:
  - What was done
  - Why (rationale)
  - Confidence score
  - Human who approved (if applicable)
```

---

## 10. Hands-On Queries to Try

Use the MCP server's `execute_query` tool or run these directly.

### Query 1: Find open POs with overdue schedules

```sql
SELECT ph.SEGMENT1                              AS po_number,
       pll.NEED_BY_DATE,
       TRUNC(SYSDATE) - TRUNC(pll.NEED_BY_DATE) AS days_overdue,
       pll.QUANTITY_ORDERED - NVL(pll.QUANTITY_RECEIVED,0) AS qty_outstanding,
       pv.VENDOR_NAME
FROM   APPS.PO_HEADERS_ALL       ph
JOIN   APPS.PO_LINE_LOCATIONS_ALL pll ON pll.PO_HEADER_ID = ph.PO_HEADER_ID
JOIN   APPS.PO_VENDORS            pv  ON pv.VENDOR_ID     = ph.VENDOR_ID
WHERE  ph.TYPE_LOOKUP_CODE    = 'STANDARD'
AND    ph.STATUS_LOOKUP_CODE  = 'APPROVED'
AND    pll.NEED_BY_DATE       < SYSDATE
AND    pll.QUANTITY_RECEIVED  < pll.QUANTITY_ORDERED
ORDER  BY days_overdue DESC
```

### Query 2: Top suppliers by PO spend

```sql
SELECT pv.VENDOR_NAME,
       COUNT(DISTINCT ph.PO_HEADER_ID)   AS po_count,
       SUM(pl.QUANTITY * pl.UNIT_PRICE)  AS total_spend,
       ph.CURRENCY_CODE
FROM   APPS.PO_HEADERS_ALL  ph
JOIN   APPS.PO_LINES_ALL    pl ON pl.PO_HEADER_ID = ph.PO_HEADER_ID
JOIN   APPS.PO_VENDORS      pv ON pv.VENDOR_ID    = ph.VENDOR_ID
WHERE  ph.TYPE_LOOKUP_CODE = 'STANDARD'
AND    ph.AUTHORIZATION_STATUS = 'APPROVED'
GROUP  BY pv.VENDOR_NAME, ph.CURRENCY_CODE
ORDER  BY total_spend DESC
```

### Query 3: Planning exceptions ranked by plan

```sql
SELECT p.COMPILE_DESIGNATOR  AS plan_name,
       e.EXCEPTION_TYPE,
       COUNT(*)               AS exception_count
FROM   MSC.MSC_PLANS            p
JOIN   MSC.MSC_EXCEPTION_DETAILS e ON e.PLAN_ID = p.PLAN_ID
GROUP  BY p.COMPILE_DESIGNATOR, e.EXCEPTION_TYPE
ORDER  BY plan_name, exception_count DESC
```

### Query 4: Items below safety stock

```sql
SELECT si.ITEM_NAME,
       ss.SAFETY_STOCK_QUANTITY  AS target_qty,
       s.QUANTITY                AS current_supply,
       ss.SAFETY_STOCK_QUANTITY - NVL(s.QUANTITY,0) AS shortage
FROM   MSC.MSC_SAFETY_STOCKS  ss
JOIN   MSC.MSC_SYSTEM_ITEMS   si ON si.INVENTORY_ITEM_ID = ss.INVENTORY_ITEM_ID
                                 AND si.PLAN_ID           = ss.PLAN_ID
LEFT JOIN (
    SELECT PLAN_ID, INVENTORY_ITEM_ID, SUM(NEW_ORDER_QUANTITY) AS QUANTITY
    FROM   MSC.MSC_SUPPLIES
    WHERE  ORDER_TYPE IN (1,2,3)   -- on hand, in transit, in receiving
    GROUP  BY PLAN_ID, INVENTORY_ITEM_ID
) s ON s.PLAN_ID = ss.PLAN_ID AND s.INVENTORY_ITEM_ID = ss.INVENTORY_ITEM_ID
WHERE  ss.PLAN_ID = 74032   -- UNCONS plan
AND    NVL(s.QUANTITY,0) < ss.SAFETY_STOCK_QUANTITY
ORDER  BY shortage DESC
```

### Query 5: Full demand-to-supplier trace (Pegging)

```sql
SELECT p.COMPILE_DESIGNATOR        AS plan,
       fp.PEGGING_ID,
       fp.DEMAND_ID,
       fp.SUPPLY_ID,
       s.ORDER_TYPE,
       s.NEW_ORDER_QUANTITY         AS planned_qty,
       s.FIRM_DATE                  AS need_by
FROM   MSC.MSC_FULL_PEGGING fp
JOIN   MSC.MSC_PLANS        p  ON p.PLAN_ID = fp.PLAN_ID
JOIN   MSC.MSC_SUPPLIES     s  ON s.PLAN_ID = fp.PLAN_ID
                               AND s.TRANSACTION_ID = fp.SUPPLY_ID
WHERE  fp.PLAN_ID = 74032
AND    ROWNUM <= 20
```

---

## Glossary

| Term | Meaning |
|---|---|
| **Agent** | An AI that perceives, decides, and acts autonomously |
| **MCP** | Model Context Protocol — secure tool bridge for AI agents |
| **Oracle EBS** | Enterprise Business Suite — Oracle's ERP platform |
| **ASCP** | Advanced Supply Chain Planning — Oracle's planning engine |
| **MSC** | Manufacturing Scheduling and Control — schema for planning data |
| **PO** | Purchase Order |
| **GRN** | Goods Receipt Note — physical delivery confirmation |
| **Pegging** | Tracing a demand back to its supply source |
| **Safety Stock** | Minimum inventory buffer to absorb demand uncertainty |
| **Planned Order** | AI/system-suggested order, not yet a real PO |
| **Exception** | A planning alert — something is wrong or at risk |
| **Lead Time** | Time from order placement to goods receipt |
| **Blanket PO** | A long-term agreement with a supplier for recurring purchases |
| **SID** | System Identifier — Oracle DB instance name (EBSDB here) |
| **Thick Mode** | oracledb mode that uses Oracle Client DLLs for NNE encryption |

---

## Next Steps for Builders

```
Week 1:  Connect and explore the data (DONE in this session)
         - MCP server connected
         - 27K POs explored
         - 140 MSC plans catalogued

Week 2:  Build read-only agent tools
         - List exceptions by plan
         - Find overdue POs
         - Safety stock alerts

Week 3:  Add AI decision layer
         - Classify exceptions by priority
         - Score suppliers by reliability
         - Recommend actions with rationale

Week 4:  Cautious write-back
         - Create draft POs (human approval required)
         - Update planned order quantities
         - Log every action to audit table

Week 5+: Expand autonomy
         - Auto-approve low-risk, low-value orders
         - Supplier performance dashboards
         - Predictive shortage alerts (before exceptions fire)
```

---

*Generated from live Oracle EBS data session — 2026-03-09*
*MCP Server: oracle-ebs · DB: EBSDB @ 161.118.185.249:1521 · User: APPS*
