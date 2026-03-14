# Agentic Procurement AI — Complete Guide

> **Who this document is for:** Everyone — business users, procurement managers, IT teams, and developers.
> No technical background required to understand what this system does and how it works.

---

## Table of Contents

1. [What Is This System?](#1-what-is-this-system)
2. [The Big Picture — How It Works](#2-the-big-picture--how-it-works)
3. [The 6 Workflows — What the Agent Does](#3-the-6-workflows--what-the-agent-does)
4. [How the Agent Makes Decisions](#4-how-the-agent-makes-decisions)
5. [Autonomy Levels — How Much the Agent Can Act](#5-autonomy-levels--how-much-the-agent-can-act)
6. [Priority System — How Urgent Is Each Finding](#6-priority-system--how-urgent-is-each-finding)
7. [Draft Purchase Orders — What Gets Generated](#7-draft-purchase-orders--what-gets-generated)
8. [Validation Rules — Safety Checks Before Any PO](#8-validation-rules--safety-checks-before-any-po)
9. [The Excel Output — What Each Sheet Shows](#9-the-excel-output--what-each-sheet-shows)
10. [Oracle EBS Data — Where the Agent Reads From](#10-oracle-ebs-data--where-the-agent-reads-from)
11. [How to Run the Agent](#11-how-to-run-the-agent)
12. [All Actions the Agent Can Take](#12-all-actions-the-agent-can-take)
13. [Example End-to-End Run](#13-example-end-to-end-run)
14. [Glossary](#14-glossary)

---

## 1. What Is This System?

The **Agentic Procurement AI** is an automated software agent that connects directly to your **Oracle E-Business Suite (EBS) R12** database, reads live procurement data, spots problems, and either notifies the right people or generates ready-to-approve purchase orders — all without anyone having to write reports or manually dig through the system.

### What Problem Does It Solve?

Every day, procurement teams face:
- Hundreds of exception alerts from Oracle's planning system that nobody has time to review
- Suppliers delivering late, with no automatic follow-up
- Inventory running out below safety stock targets
- Prices paid that are higher than the agreed contract price
- Customer orders at risk because supply is not lined up
- Millions in spend with no visibility of who buys what, from whom, and at what price

This agent reads all of that data automatically, decides what needs attention, and acts on it — at whatever level of autonomy you choose.

### What Makes It "Agentic"?

A traditional report tells you what happened.
An agentic system **reads data → reasons about it → decides what to do → acts** — on its own, with an audit trail of every decision.

This agent:
- Connects to Oracle EBS and reads live data (never writes without your permission)
- Runs 6 different procurement workflows simultaneously
- Makes prioritised decisions using a built-in scoring engine
- Generates complete, Oracle-ready draft purchase orders
- Records every decision with the reasoning behind it
- Saves everything to Excel and JSON for review

---

## 2. The Big Picture — How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORACLE EBS R12 DATABASE                     │
│  MSC Planning  │  PO / Purchasing  │  Inventory  │  HR / GL    │
└────────────────────────┬────────────────────────────────────────┘
                         │  Read-Only Connection
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ORACLE READ-ONLY GATEWAY (Safe Layer)              │
│  All queries are SELECT only. No data is ever changed here.     │
└────────────────────────┬────────────────────────────────────────┘
                         │  Structured Data
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PROCUREMENT DECISION ENGINE                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Exception   │  │  Late        │  │  Safety Stock        │  │
│  │  Triage      │  │  Supplier    │  │  Alerts              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Price       │  │  Demand→PO   │  │  Spend               │  │
│  │  Anomaly     │  │  Tracing     │  │  Analytics           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │  Decisions + Actions
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                              │
│                                                                  │
│   📊 Excel Report (5 sheets)    📄 JSON Audit File              │
│   📋 Draft PO Payloads          🔔 Buyer Notifications          │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Flow

**Step 1 — Connect**
The agent connects to Oracle EBS using a read-only database account. It identifies which supply plan has the most exceptions and starts working.

**Step 2 — Read**
It reads from 15+ Oracle tables across planning (MSC), purchasing (APPS), inventory (INV), and HR schemas.

**Step 3 — Analyse**
Each of the 6 workflows runs its own analysis — looking at exceptions, supplier performance, inventory levels, prices, demand gaps, and spending patterns.

**Step 4 — Decide**
The built-in Decision Engine scores every finding by urgency (type severity + financial impact + time pressure + demand risk) and assigns a priority (P1 through P4).

**Step 5 — Act**
Depending on the autonomy level you chose, the agent either just reports, recommends, or generates a complete draft purchase order ready for buyer approval.

**Step 6 — Record**
Every decision — what was found, what was decided, why, and what the evidence was — is saved to an Excel workbook and a JSON audit file.

---

## 3. The 6 Workflows — What the Agent Does

### Workflow 1 — Exception Triage

**Plain English:** The Oracle planning system flags hundreds of supply chain problems every day. This workflow reads them all, prioritises them, and decides which need immediate action.

**What it looks at:** `MSC_EXCEPTION_DETAILS` — the planning system's exception queue

**Exception types it handles:**

| Exception | What It Means | Agent's Response |
|---|---|---|
| Past Due Purchase Orders | A PO was due but not received | Create draft PO to re-order |
| Late Replenishment Orders | Replenishment is going to be late | Create draft PO urgently |
| Items Below Safety Stock | Stock has fallen below the minimum buffer | Create draft PO |
| Orders at Risk | Customer orders may not be fulfilled | Notify buyer immediately (P1-CRITICAL) |
| Demand Not Satisfied | Demand exists with no supply planned | Notify buyer (P2-HIGH) |
| Excess Inventory | Too much stock on hand | Auto-resolve (low priority) |
| Items with No Activity | Item has had no movement | Auto-resolve (low priority) |
| Expired Lots | Batch/lot has expired | Auto-resolve |
| All others | Everything else | Add to buyer worklist |

**Key decision point:** For supply-facing exceptions (past due, late orders, below safety stock), the agent creates a draft PO. For demand-facing exceptions (orders at risk, demand not satisfied), it always escalates to a human buyer because customer fulfilment is at stake.

---

### Workflow 2 — Late Supplier Detection

**Plain English:** Looks at every open purchase order that is overdue or about to be overdue, identifies which suppliers are chronically late, and decides whether to send a reminder or escalate to the procurement manager.

**What it looks at:** `PO_HEADERS_ALL`, `PO_LINE_LOCATIONS_ALL`, `PO_VENDORS`

**Decision fork:**

```
Is this PO overdue?
    │
    ├── YES, 7+ days overdue AND supplier has a poor track record
    │       → Notify buyer (P1-CRITICAL)
    │         Recommend switching to an alternate supplier
    │
    └── YES, but first-time lateness / minor delay
            → Send reminder alert to supplier (P3-MEDIUM)
              Include: PO number, item, quantity still outstanding
```

**What makes a supplier "chronically late":** The agent checks the supplier's on-time delivery history. If on-time rate < 70% across more than 3 orders, it flags as chronic and escalates.

**Alternate supplier recommendation:** When a supplier is flagged, the agent automatically queries available alternates for the same item and ranks them by fastest lead time + lowest price.

---

### Workflow 3 — Safety Stock Alerts

**Plain English:** Every item in your Oracle system has a minimum stock level (safety stock). This workflow compares current available supply against those targets and raises alerts for anything below — or flags excess.

**What it looks at:** `MSC_SAFETY_STOCKS`, `MSC_SUPPLIES`, `MSC_SYSTEM_ITEMS`

**Decision logic:**

```
Current Supply vs. Safety Stock Target
    │
    ├── Current supply < Target
    │       │
    │       ├── Shortage > 500 units → P2-HIGH → Create draft PO
    │       └── Shortage ≤ 500 units → P3-MEDIUM → Create draft PO
    │
    └── Current supply > Target
            → Flag excess inventory (P3-MEDIUM)
              Calculate holding cost
              Recommend clearance or redistribution
```

**Supplier routing:** When a draft PO is recommended, the agent picks the cheapest + fastest available supplier automatically (sorted by lead time first, then price).

---

### Workflow 4 — Price Anomaly Detection

**Plain English:** Compares what you are currently paying for items against what you agreed to pay (contract price) and what you paid on average over the last 12 months. If prices have drifted upward without a contract change, it flags the item for renegotiation.

**What it looks at:** `PO_LINES_ALL`, `PO_HEADERS_ALL`, `PO_AGREEMENTS` (blanket orders)

**Decision thresholds:**

| Condition | Deviation | Action |
|---|---|---|
| Current price > contract price | > 5% | Flag for immediate renegotiation (P2-HIGH) |
| Current price > 12-month average | > 20% | Flag for renegotiation |
| Current price > 12-month average | 10–20% | Flag for review |
| Within normal range | < 10% | No action |

**What is "maverick spend"?** A purchase made without an active blanket/contract agreement in place. These bypass negotiated pricing and are flagged as compliance risks.

---

### Workflow 5 — Demand-to-PO Tracing

**Plain English:** Looks at Oracle's planning system to find demand records (e.g., sales orders, forecasts) that are not yet covered by a planned purchase order. These are gaps that could result in missed customer commitments.

**What it looks at:** `MSC_FULL_PEGGING`, `MSC_SUPPLIES`, `MSC_DEMANDS`, `MSC_PLANS`

**Revenue at risk:** For each uncovered demand, the agent traces through the pegging table to the actual customer sales order and calculates the revenue value at risk. If pegging data is not available, it falls back to quantity × list price as an estimate.

**Tracing method:**
```
Demand (Sales Order / Forecast)
    ↓
MSC_FULL_PEGGING (links demand to supply)
    ↓
MSC_SUPPLIES (planned replenishment orders)
    ↓
If order_type = 5 (Planned Purchase Order) → Create draft PO
```

---

### Workflow 6 — Spend Analytics

**Plain English:** Aggregates all purchase order spending across your supplier base and surfaces four types of risk: over-dependence on one supplier, off-contract spending, single-source supply risk, and price consolidation opportunities.

**What it looks at:** `PO_HEADERS_ALL`, `PO_LINES_ALL`, `PO_VENDORS`, `PO_AGREEMENTS`

**Four analyses run:**

#### A) Concentration Risk
Ranks all suppliers by total spend. If any supplier accounts for more than 30% of total spend, it is flagged as a concentration risk.

#### B) Maverick Spend Detection
Identifies purchases made to suppliers where no active blanket agreement exists. These are "off-contract" or "unauthorized" purchases that bypass negotiated pricing.

**Threshold:** Flagged as P2-HIGH if the spend per line exceeds $10,000.

#### C) Single-Source Risk
Identifies items that are only bought from one supplier. If that supplier fails, production stops.

**Threshold:** Flagged as P2-HIGH if annual spend on that item exceeds $50,000.

#### D) Consolidation Opportunities
Finds items being bought from multiple suppliers at different prices. If the price spread between cheapest and most expensive is more than 10%, consolidating to one supplier could reduce costs.

#### E) Quarterly Spend Trend
Aggregates spend by quarter over the last 24 months, broken down by business unit (Org ID). Shows whether spend is growing, stable, or declining over time.

---

## 4. How the Agent Makes Decisions

The agent uses a built-in **Procurement Decision Engine** — a rules-based scoring system that evaluates every finding across four dimensions and produces a priority score.

### The Scoring Formula

```
Priority Score = (40% × Exception Type Severity)
              + (25% × Financial Impact Score)
              + (20% × Time Urgency Score)
              + (15% × Customer Demand Risk Score)
```

### Component 1 — Exception Type Severity (40%)

Each exception type has a built-in severity weight:

| Exception Type | Severity Weight |
|---|---|
| Past Due Purchase Orders | 0.90 (highest) |
| Demand Not Satisfied | 0.85 |
| Items Below Safety Stock | 0.80 |
| Late Replenishment Orders | 0.75 |
| Demand Past Due | 0.70 |
| Orders at Risk / Short Shipments | 0.60 |
| Cancelled Supply | 0.50 |
| Excess Inventory | 0.40 |
| Items with No Activity | 0.30 (lowest) |

### Component 2 — Financial Impact (25%)

```
Financial Score = min(Quantity × Unit Price ÷ $50,000, 1.0)
```
A $50,000+ value item scores maximum (1.0). A $5,000 item scores 0.10.

### Component 3 — Time Urgency (20%)

```
Time Score = min(Days Overdue ÷ 30, 1.0)
```
30+ days overdue scores maximum (1.0). If not yet overdue, a base score of 0.30 is applied.

### Component 4 — Customer Demand Risk (15%)

```
Demand Score = min(Number of Pegging Records ÷ 10, 1.0)
```
Each pegging record represents a customer order that depends on this supply. 10+ customer orders at risk scores maximum (1.0).

### Priority Assignment

| Score Range | Priority | Typical Action |
|---|---|---|
| ≥ 0.75 | **P1-CRITICAL** | Immediate action — notify buyer / draft PO |
| 0.55 – 0.74 | **P2-HIGH** | Urgent — draft PO or flag for renegotiation |
| 0.35 – 0.54 | **P3-MEDIUM** | Monitor — add to worklist or send reminder |
| < 0.35 | **P4-LOW** | Low urgency — report insight only |

---

## 5. Autonomy Levels — How Much the Agent Can Act

You control how much the agent does on its own by setting an **autonomy level** when running it.

### Level 0 — Report Only

> *"Tell me what you found. I'll decide what to do."*

- The agent reads data and identifies problems
- Every finding is converted to a `report_only` action
- **No draft POs, no escalations, no buyer notifications**
- Safe for first-time use or audit situations
- All decisions are presented for human review

### Level 1 — Recommend (Default)

> *"Tell me what you'd do, and I'll approve it."*

- The agent analyses all 6 workflows
- Recommends actions (e.g., `recommend_draft_po`) with full reasoning
- Does **not** generate actual PO payloads
- Buyers see the recommendation, rationale, and evidence, then decide
- Safe for normal operations

### Level 2 — Draft PO Generation

> *"Generate the paperwork. I'll review and approve before it goes to Oracle."*

- The agent generates **complete, Oracle R12-ready draft purchase orders**
- Each PO has all 25+ required fields (vendor, item, quantity, price, GL account, etc.)
- POs are created with status `INCOMPLETE` — they cannot be sent to a supplier without a buyer approving them in Oracle
- Every draft PO is validated through 5 safety checks before being included

> **Important:** Even at Level 2, no data is written to Oracle. The agent is read-only. The draft POs are output to Excel/JSON for a buyer to manually enter or approve in Oracle EBS.

---

## 6. Priority System — How Urgent Is Each Finding

All findings across all 6 workflows use the same four-level priority system:

| Priority | Colour in Excel | Meaning | Typical Response Time |
|---|---|---|---|
| **P1-CRITICAL** | 🔴 Red | Immediate threat to supply or customer fulfilment | Same day |
| **P2-HIGH** | 🟠 Orange | Significant risk requiring urgent attention | Within 24 hours |
| **P3-MEDIUM** | 🟡 Amber | Important but not yet an emergency | Within 1 week |
| **P4-LOW** | 🟢 Green | Monitor only — low impact | Next review cycle |

---

## 7. Draft Purchase Orders — What Gets Generated

When the agent generates a draft PO (autonomy level 2), it creates a complete Oracle R12 payload with all required fields — not just a summary.

### PO Number Format

All agent-generated draft POs use the format:
```
AGNT-YYYYMMDD-NNNN
Example: AGNT-20260311-0001
```

This makes them instantly identifiable as agent-generated drafts when viewed in Oracle.

### What's in a Draft PO

**Header (Who, What Organisation, What Terms)**
- PO number, type (STANDARD), status (INCOMPLETE)
- Vendor ID and name, vendor site
- Organisation ID (business unit)
- Currency (USD)
- Payment terms, FOB code (SHIPPER), freight terms
- Ship-to and bill-to location
- Invoice matching (3-way match)
- Created-by module: `TUTORIAL_AGENT`

**Line (What Item, How Much, At What Price)**
- Item ID, item number, item description
- Unit of measure (UOM)
- Quantity ordered
- Unit price
- Line amount (quantity × price)
- Need-by date

**Shipment Schedule (When and Where to Deliver)**
- Need-by date
- Ship-to location
- Receipt required flag
- Inspection required flag

**Distribution (Which GL Account to Charge)**
- Destination type (INVENTORY)
- Charge account (GL code combination, e.g., 1010-1000-1000)
- Amount ordered
- Project ID and task ID (if project accounting is in use)

**Validation Status (Safety Checks)**
- Can create PO: YES / NO
- Supplier status: ACTIVE / ON_HOLD / INACTIVE / NOT_FOUND
- Item status: PURCHASABLE / NOT_PURCHASABLE / INACTIVE / NOT_FOUND
- Any warnings (lead time issues, MOQ, high value)

---

## 8. Validation Rules — Safety Checks Before Any PO

Before generating any draft PO, the agent automatically runs 5 validation checks:

### Rule 1 — Supplier Active Status
Checks if the supplier is currently active in Oracle.
- **Blocked if:** supplier is ON HOLD or INACTIVE (end date has passed)
- **Warning if:** supplier not found in vendor master

### Rule 2 — Item Purchasable Flag
Checks if the item is set up for purchasing in Oracle.
- **Blocked if:** `PURCHASING_ENABLED_FLAG ≠ Y` or item has passed its end date
- **Warning if:** item not found in item master

### Rule 3 — Lead-Time Feasibility
Checks if the supplier can physically deliver in time.
- **Warning if:** supplier's lead time in days > days until the item is needed
- **Message:** "Lead time (X days) exceeds days until needed (Y days). Consider alternate supplier or expedite."

### Rule 4 — Minimum Order Quantity (MOQ)
Checks if the quantity being ordered meets the supplier's minimum.
- **Warning if:** requested quantity < supplier's minimum order quantity
- **Message:** "Quantity X is below minimum order quantity (Y) for this supplier-item."

### Rule 5 — Financial Threshold
Flags high-value POs that need manager approval.
- **Warning if:** estimated PO value (quantity × price) exceeds **$100,000**
- **Message:** "High-value PO: estimated value $X exceeds $100K. Procurement manager approval required."

---

## 9. The Excel Output — What Each Sheet Shows

Every run produces a professionally formatted Excel workbook with 5 sheets, colour-coded by priority.

### Sheet 1 — Dashboard

The executive summary. At a glance:
- Run date/time, database connected, Oracle version
- Which plan was analysed
- **KPI boxes:** total count of each action type (create_draft_po, notify_buyer, etc.)
- **Workflow execution table:** one row per workflow showing records reviewed, actions created, and key metric

### Sheet 2 — All Actions

Every single decision the agent made, in one place.

| Column | Description |
|---|---|
| `#` | Row number |
| `Workflow` | Which of the 6 workflows produced this finding |
| `Action` | The decision taken (e.g., create_draft_po, notify_buyer) |
| `Priority` | P1/P2/P3/P4 — **colour-coded** red/orange/amber/green |
| `Requires Approval` | YES = buyer must approve before acting; NO = informational |
| `Summary` | One-line explanation of what was found |
| `Rationale` | The agent's reasoning — why this action was chosen |
| `Confidence` | How confident the agent is in this recommendation (%) |
| `Assigned To` | Who should handle this action (e.g., Senior Buyer) |

### Sheet 3 — Draft POs

All draft purchase orders generated during the run. 25 columns:

| Column Group | Columns |
|---|---|
| **Identification** | PO Number, Status, Workflow, Priority |
| **Supplier** | Vendor ID, Vendor Name, Org ID, Currency, Payment Terms ID, Ship-To Location ID, FOB Code |
| **Item** | Item ID, Item Number, Item Description, UOM, Quantity, Unit Price, Line Amount |
| **Finance** | Charge Account, Destination Type, Amount Ordered |
| **Validation** | Can Create PO, Supplier Status, Item Status, Warnings |

### Sheet 4 — Spend Analytics

Three sections:

**Top Suppliers by Spend** — Ranked table showing every supplier with total spend, PO count, distinct items, and currency.

**Risk Flags** — Every maverick spend finding, single-source risk, and consolidation opportunity with recommended actions.

**Quarterly Spend Trend** — Last 24 months of spend broken down by quarter and business unit, showing whether spending is growing or shrinking over time.

### Sheet 5 — Workflow Summary

A compact metrics table for each workflow. No raw data — just the key numbers:

| Workflow | Metrics Shown |
|---|---|
| Exception Triage | Plan ID, exception types found, decisions made |
| Late Supplier | Candidates reviewed, chronic late suppliers flagged |
| Safety Stock | Items below target, items with excess, total items reviewed |
| Price Anomaly | Anomalies found, items over contract price, items without active contract |
| Demand-to-PO | Pegging records reviewed |
| Spend Analytics | Suppliers ranked, total spend, top-3 concentration %, maverick count, single-source count, consolidation opportunities, quarterly periods analysed |

---

## 10. Oracle EBS Data — Where the Agent Reads From

The agent is **completely read-only**. It connects using a SELECT-only database role and cannot insert, update, or delete any Oracle data.

### Tables Used

#### Planning / Supply Chain (MSC Schema)
| Table | What It Contains |
|---|---|
| `MSC_EXCEPTION_DETAILS` | All supply chain exception alerts from the planning engine |
| `MSC_PLANS` | Supply chain plan definitions (name, compile date, status) |
| `MSC_SUPPLIES` | Planned supply orders (purchase orders, work orders, on-hand) |
| `MSC_DEMANDS` | Demand records (sales orders, forecasts) |
| `MSC_FULL_PEGGING` | Links between demand and supply (who needs what and from where) |
| `MSC_SAFETY_STOCKS` | Minimum stock level targets per item |
| `MSC_SYSTEM_ITEMS` | Item master within the planning schema |
| `MSC_ITEM_SUPPLIERS` | Which suppliers are approved for which items |

#### Purchasing (APPS Schema)
| Table | What It Contains |
|---|---|
| `PO_HEADERS_ALL` | Purchase order headers (PO number, vendor, status, dates) |
| `PO_LINES_ALL` | PO line items (item, quantity, price) |
| `PO_LINE_LOCATIONS_ALL` | Shipment schedules (need-by date, receipt date, quantity) |
| `PO_VENDORS` | Supplier master (name, active status, hold flag) |
| `PO_VENDOR_SITES_ALL` | Supplier delivery sites (lead time, payment terms, FOB) |
| `PO_AGREEMENTS` | Blanket purchase agreements / contracts |

#### Inventory (INV Schema)
| Table | What It Contains |
|---|---|
| `MTL_SYSTEM_ITEMS_B` | Item master (description, UOM, list price, purchasing flag) |
| `MTL_PARAMETERS` | Inventory organisation settings |

#### Other
| Table | What It Contains |
|---|---|
| `HR_LOCATIONS` | Ship-to and bill-to location codes and addresses |
| `AP_TERMS` | Payment terms definitions |

---

## 11. How to Run the Agent

### Prerequisites
- Python 3.9+ installed
- Oracle EBS R12 database accessible
- `.env` file in the same folder with Oracle credentials:
  ```
  ORACLE_USER=apps
  ORACLE_PASSWORD=yourpassword
  ORACLE_HOST=your.server.ip
  ORACLE_PORT=1521
  ORACLE_SID=EBSDB
  ```

### Basic Run Commands

**Run all 6 workflows, recommend mode (default):**
```bash
python tutorial_agentic_procurement_agent.py --workflow all
```

**Run all workflows with draft PO generation:**
```bash
python tutorial_agentic_procurement_agent.py --workflow all --autonomy-level 2
```

**Run just one specific workflow:**
```bash
python tutorial_agentic_procurement_agent.py --workflow late-supplier
python tutorial_agentic_procurement_agent.py --workflow safety-stock
python tutorial_agentic_procurement_agent.py --workflow spend-analytics
```

**Run report-only (safest — no actions taken):**
```bash
python tutorial_agentic_procurement_agent.py --workflow all --autonomy-level 0
```

**Analyse a specific supply plan:**
```bash
python tutorial_agentic_procurement_agent.py --workflow all --plan-id 74032
```

**Increase the number of records reviewed:**
```bash
python tutorial_agentic_procurement_agent.py --workflow all --autonomy-level 2 --limit 100
```

### All Command Options

| Option | Values | Default | Description |
|---|---|---|---|
| `--workflow` | `all`, `exception-triage`, `late-supplier`, `safety-stock`, `price-anomaly`, `demand-to-po`, `spend-analytics` | `exception-triage` | Which workflow(s) to run |
| `--autonomy-level` | `0`, `1`, `2` | `1` | How much the agent acts independently |
| `--engine` | `rules`, `claude` | `rules` | Decision engine to use |
| `--plan-id` | Any integer | Auto-detected | Specific Oracle supply plan to analyse |
| `--limit` | Any integer | `10` | Max records to process per workflow |

### Output Files

All output is saved to `tutorial_agent_outputs/` in the same folder:
- **JSON file:** `tutorial_agent_run_YYYYMMDD_HHMMSS.json` — complete audit trail (all decisions, evidence, payloads)
- **Excel file:** `tutorial_agent_run_YYYYMMDD_HHMMSS.xlsx` — 5-sheet formatted workbook

---

## 12. All Actions the Agent Can Take

| Action Name | When Used | Level 2 Required? |
|---|---|---|
| `report_only` | Autonomy level 0 — everything becomes a report | No |
| `report_insight` | Informational findings (e.g., spend concentration) | No |
| `add_to_worklist` | Low-priority exceptions, unknown types | No |
| `send_reminder_alert` | First-time late supplier — sends reminder message | No |
| `monitor_delivery` | PO approaching due date but not yet late | No |
| `auto_resolve` | Minor issues (excess inventory < 500, no activity) | No |
| `notify_buyer` | Demand-facing exceptions, chronic lateness, high-risk | No |
| `recommend_draft_po` | Level 1 — recommends a PO but does not generate payload | No |
| `create_draft_po` | Level 2 — generates full Oracle R12 PO payload | **Yes** |
| `flag_for_renegotiation` | Price above contract or historical average | No |
| `flag_maverick_spend` | Purchase with no active blanket agreement | No |
| `flag_single_source_risk` | Item with only one approved supplier | No |
| `flag_excess_inventory` | Supply above safety stock target | No |
| `consolidate_spend` | Same item bought from multiple suppliers at different prices | No |

---

## 13. Example End-to-End Run

Here is a real example of the agent processing one exception from start to finish.

### Input from Oracle
The planning system (plan 387 — "Windows") has an exception of **type 6 (Past Due Purchase Order)** for item 1060.

### Step 1 — Read Data
The agent queries Oracle and retrieves:
- Item 1060 context: price, UOM, lead time
- Supplier options: 3G Communications, Inc. (vendor 783) — fastest + cheapest
- Open PO coverage: zero (no existing open POs)
- Pegging context: no active customer demand pegged to this item
- Safety stock status: normal

### Step 2 — Score Priority
Decision Engine calculates:
- Type severity (Past Due = 0.90) × 0.40 = **0.360**
- Financial score (260 units) × 0.25 = (depends on price)
- Time urgency (overdue) × 0.20 = **0.060** (base)
- Demand coverage (0 pegging) × 0.15 = **0.000**
- **Composite score ≈ 0.62 → P2-HIGH**

### Step 3 — Decide
At autonomy level 2: **create_draft_po**

### Step 4 — Generate Draft PO
```
PO Number    : AGNT-20260311-0001
Vendor       : 3G Communications, Inc. (ID: 783)
Item         : 1060
Quantity     : 260
UOM          : EA
Unit Price   : [from item master]
Org ID       : 204
Status       : INCOMPLETE (pending buyer approval)
Charge Acct  : 1010-1000-1000
Destination  : INVENTORY
```

### Step 5 — Validate
✅ Supplier: ACTIVE
✅ Item 1060: PURCHASABLE
✅ Lead time: within required window
✅ Quantity: above MOQ
✅ PO value: below $100K threshold

**Can Create PO: YES**

### Step 6 — Record
This decision is written to:
- All Actions sheet (row 1, P2-HIGH, `create_draft_po`)
- Draft POs sheet (full 25-column record)
- JSON audit file (complete evidence + reasoning)

### What Happens Next?
The buyer opens the Excel, reviews the Draft POs sheet, and if they agree, enters the PO into Oracle EBS manually or approves it through the standard Oracle approval workflow. The PO status changes from INCOMPLETE → APPROVED → sent to supplier.

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Agentic** | A system that can observe, reason, decide, and act — not just report |
| **Autonomy Level** | How much the agent can act on its own (0=report, 1=recommend, 2=draft PO) |
| **Blanket Agreement / PO Agreement** | A long-term contract with a supplier at agreed pricing |
| **Charge Account** | The GL (General Ledger) code that records the expense (e.g., 1010-1000-1000) |
| **Chronic Late Supplier** | A supplier with on-time delivery rate below 70% across multiple orders |
| **Concentration Risk** | When too much of your spend goes to one supplier — creates vulnerability |
| **Decision Engine** | The built-in rules-based system that scores and prioritises every finding |
| **Distribution (PO)** | The accounting line of a PO — which department and GL account is charged |
| **Exception** | An alert from Oracle's planning system that something is wrong |
| **FOB** | Free On Board — determines who owns goods during shipping (SHIPPER = seller pays freight) |
| **Gateway** | The read-only Oracle database connection layer — cannot write to the database |
| **GL / General Ledger** | The financial accounting system that records all expenses |
| **INCOMPLETE (PO Status)** | Oracle status meaning the PO is a draft — not yet sent to supplier |
| **Lead Time** | How many days it takes for a supplier to deliver after an order is placed |
| **Maverick Spend** | Purchasing from a supplier without an active contract — bypasses negotiated pricing |
| **MOQ** | Minimum Order Quantity — the smallest quantity a supplier will accept |
| **MSC** | Manufacturing Scheduling and Coordination — Oracle's supply chain planning module |
| **Oracle EBS R12** | Oracle E-Business Suite Release 12 — the enterprise procurement system |
| **Org ID** | Operating Unit ID — identifies which business unit a transaction belongs to |
| **Pegging** | The link between a demand (sales order) and the supply planned to meet it |
| **P1/P2/P3/P4** | Priority levels: P1=Critical, P2=High, P3=Medium, P4=Low |
| **PO** | Purchase Order — a formal document ordering goods from a supplier |
| **Procurement Manager** | The person who approves high-value or policy-exception POs |
| **Safety Stock** | The minimum buffer quantity of an item that should always be on hand |
| **Single-Source Risk** | Only one supplier available for an item — if they fail, you cannot buy elsewhere |
| **Spend Analytics** | Analysis of how much is being spent, with whom, and on what |
| **Triage** | The process of sorting and prioritising exceptions by urgency |
| **UOM** | Unit of Measure — e.g., EA (each), KG, LT (litre) |
| **Vendor Site** | A specific delivery/billing address for a supplier |
| **Workflow** | One of the 6 analysis processes the agent runs |

---

*Generated by the Agentic Procurement AI system.*
*Tutorial source: `TUTORIAL_Agentic_Procurement_AI.md`*
*Implementation: `tutorial_agentic_procurement_agent.py`*
*Write-back module: `oracle_r12_po_writer.py`*
