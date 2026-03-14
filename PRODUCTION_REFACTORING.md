# Production-Grade Configuration System

## Overview

The procurement agent has been completely refactored to remove all hardcoded values and implement a professional, enterprise-ready configuration system. This document explains the changes and how to use the new system.

## What Changed

### Before (Hardcoded)
```python
# ❌ OLD - Hardcoded values scattered throughout
DB_HOST = os.getenv("DB_HOST", "161.118.185.249")  # Default hardcoded
APPS_USER = os.getenv("APPS_USER", "apps")         # Default hardcoded

# In methods:
SELECT * FROM INV.MTL_SYSTEM_ITEMS_B  # Table name hardcoded
SELECT * FROM MSC.MSC_EXCEPTION_DETAILS
if on_time_rate < 70:  # Threshold hardcoded
if hist_deviation > 20:  # Deviation threshold hardcoded
```

### After (Configuration-Driven)
```python
# ✅ NEW - All configuration external
config = get_config()
db_host = config.database.host
app_user = config.database.user

# In methods:
SELECT * FROM {self.tables.system_items_b}  # From config
SELECT * FROM {self.tables.msc_exception_details}
if on_time_rate < self.de_config.on_time_rate_switch:  # From config
if hist_deviation > self.de_config.price_dev_renegotiate:
```

## New Architecture

```
config.yaml (Business Parameters)
    ↓
config.py (AppConfig Class - Type Safe)
    ↓
tutorial_agentic_procurement_agent.py (Uses Configuration)
    ↓
tutorial_procurement_mcp_server.py (Exposes Tools)
```

## Configuration Files

### 1. `config.yaml` - Business Configuration

This YAML file contains ALL configurable parameters:

```yaml
database:
  host: ${DB_HOST}              # Environment variable
  port: ${DB_PORT}              # Environment variable
  user: ${APPS_USER}
  password: ${APPS_PASSWORD}
  oracle_client_path: ${ORACLE_CLIENT_PATH}

tables:                          # Oracle EBS table names
  inventory:
    system_items_b: INV.MTL_SYSTEM_ITEMS_B
    parameters: INV.MTL_PARAMETERS
  planning:
    plans: MSC.MSC_PLANS
    exception_details: MSC.MSC_EXCEPTION_DETAILS
  procurement:
    po_headers_all: APPS.PO_HEADERS_ALL
    po_lines_all: APPS.PO_LINES_ALL

exception_types:                 # Business exception mappings
  1: "Items with No Activity"
  6: "Past Due Purchase Orders"
  # ... etc

decision_engine:                 # Business thresholds
  supplier_performance:
    on_time_rate_threshold_switch: 70
    on_time_rate_threshold_monitor: 80
  pricing:
    price_deviation_renegotiate: 20
    price_deviation_review: 10
    contract_breach_threshold: 5

workflows:                       # Workflow definitions
  exception_triage:
    enabled: true
    default_limit: 50
  # ... etc
```

### 2. `.env` - Environment Secrets

Create a `.env` file with sensitive values:

```bash
DB_HOST=161.118.185.249
DB_PORT=1521
DB_SID=EBSDB
APPS_USER=apps
APPS_PASSWORD=apps
ORACLE_CLIENT_PATH=/path/to/oracle/client

OUTPUT_DIR=./tutorial_agent_outputs
```

## Using the Configuration System

### As a User

Run the agent with environment-specific configuration:

```bash
# Development
export DB_HOST=dev-ebs.company.com
export APPS_USER=apps_dev
python tutorial_agentic_procurement_agent.py --workflow exception-triage

# Production
export DB_HOST=prod-ebs.company.com
export APPS_USER=apps_prod
python tutorial_agentic_procurement_agent.py --workflow exception-triage
```

No code changes needed. Configuration changes everything!

### As a Developer

Use the configuration system in code:

```python
from config import get_config

config = get_config()

# Access database config
print(config.database.host)
print(config.database.port)

# Access table mappings
print(config.tables.msc_exception_details)
print(config.tables.po_headers_all)

# Access decision engine thresholds
print(config.decision_engine.on_time_rate_switch)
print(config.decision_engine.price_dev_renegotiate)

# Get exception types
exception_types = config.get_exception_types()

# Check feature flags
if config.is_feature_enabled("claude_engine"):
    # Use Claude engine
    pass
```

## Customization Examples

### Example 1: Using Different Oracle Instance

Edit `config.yaml`:
```yaml
database:
  host: ${DB_HOST}  # Points to environment variable
```

Set environment:
```bash
export DB_HOST=different-ebs-instance.company.com
export DB_PORT=1522
```

Run:
```bash
python tutorial_agentic_procurement_agent.py
```

**No code changes!**

### Example 2: Changing Business Thresholds

Edit `config.yaml`:
```yaml
decision_engine:
  supplier_performance:
    on_time_rate_threshold_switch: 75  # Was 70, now stricter
    on_time_rate_threshold_monitor: 85  # Was 80
  pricing:
    price_deviation_renegotiate: 25  # Was 20, more lenient
```

The decision engine automatically uses these new thresholds:

```python
# In decide_supplier_switch():
if on_time_rate < self.de_config.on_time_rate_switch:  # Uses 75 now
    decision = "switch"
```

### Example 3: Using Custom Table Names

If your Oracle instance uses non-standard table names:

Edit `config.yaml`:
```yaml
tables:
  inventory:
    system_items_b: CUSTOM_SCHEMA.CUSTOM_ITEMS_TABLE
  planning:
    exception_details: CUSTOM_SCHEMA.CUSTOM_EXCEPTIONS
```

Automatic in SQL queries:
```python
# In get_item_context():
query = f"SELECT * FROM {self.tables.system_items_b}"
# Uses CUSTOM_SCHEMA.CUSTOM_ITEMS_TABLE
```

## Production Deployment Checklist

- [ ] Create production `config.yaml` with your business parameters
- [ ] Set `.env` with production database credentials
- [ ] Update `database.host` to production EBS instance
- [ ] Review and set `decision_engine` thresholds for your business
- [ ] Update `exception_types` mappings if different from standard EBS
- [ ] Update `tables` mappings if using non-standard table names
- [ ] Enable/disable features via `features` section
- [ ] Set `autonomy` levels appropriate for your operation
- [ ] Test with `python tutorial_agentic_procurement_agent.py --workflow exception-triage --limit 5`
- [ ] Validate in logs that configuration loaded correctly
- [ ] Deploy to production

## Configuration Validation

The configuration system includes validation:

```python
# Raises ConfigurationError if:
- DB_HOST not set
- APPS_USER or APPS_PASSWORD missing
- Neither DB_SID nor DB_SERVICE_NAME provided
- DB_PORT invalid (not 1-65535)
- Configuration file not found
- Environment variable referenced but not set
```

Example error:
```
ConfigurationError: Environment variable DB_HOST is required but not set
```

## Type Safety

All configuration is type-checked:

```python
@dataclass
class DatabaseConfig:
    host: str           # Must be string
    port: int           # Must be integer
    user: str
    password: str

    def validate(self) -> None:
        if not self.host:
            raise ConfigurationError("DB_HOST is required")
        if self.port < 1 or self.port > 65535:
            raise ConfigurationError(f"Invalid DB_PORT: {self.port}")
```

## Environment Variable Override Precedence

1. **Highest**: Environment variables (e.g., `export DB_HOST=...`)
2. **Medium**: Values in `.env` file
3. **Lowest**: Defaults in `config.yaml`

Example:
```bash
# In config.yaml:
database:
  host: ${DB_HOST}  # Looks for environment variable

# In .env:
DB_HOST=default.company.com

# Command line override:
export DB_HOST=override.company.com
python script.py  # Uses override.company.com
```

## Advanced: Custom Configuration Loading

For complex scenarios, create custom config:

```python
from config import AppConfig

# Load specific config file
custom_config = AppConfig(config_file="/path/to/custom/config.yaml")

# Or create programmatically
config = AppConfig()
custom_threshold = config.decision_engine.on_time_rate_switch  # 70
```

## Troubleshooting

### "Configuration file not found: config.yaml"

Ensure `config.yaml` exists in same directory as `config.py`:
```bash
ls -la config.yaml
# Should show config.yaml
```

### "Environment variable X is required but not set"

The configuration references an environment variable that's not set:
```bash
export MISSING_VAR=value
python script.py
```

### "Invalid DB_PORT"

Port must be 1-65535:
```bash
export DB_PORT=1521  # Valid
# Not:
export DB_PORT=99999  # Invalid
```

## Summary

✅ **No Hardcoding**: All configuration external
✅ **Production Ready**: Type-safe, validated configuration
✅ **Multi-Environment**: Easy dev/test/prod setup
✅ **Auditable**: Configuration in version control (except `.env`)
✅ **Flexible**: Supports any Oracle EBS instance layout
✅ **Backwards Compatible**: Legacy variables still work
✅ **Enterprise Ready**: Professional configuration management

The agent is now truly **production-grade** - zero hardcoded business logic or database references!
