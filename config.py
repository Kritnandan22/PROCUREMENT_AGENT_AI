"""Production-level configuration management for the procurement agent.

Handles:
- YAML config file loading
- Environment variable overrides
- Type casting and validation
- Configuration merging and defaults
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""
    pass


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str
    port: int
    sid: Optional[str]
    service_name: Optional[str]
    user: str
    password: str
    oracle_client_path: Optional[str]
    pool_min: int = 1
    pool_max: int = 4
    pool_increment: int = 1
    stmt_cache_size: int = 50

    def validate(self) -> None:
        """Validate database configuration."""
        if not self.host:
            raise ConfigurationError("DB_HOST is required")
        if not self.user or not self.password:
            raise ConfigurationError("APPS_USER and APPS_PASSWORD are required")
        if not (self.sid or self.service_name):
            raise ConfigurationError("Either DB_SID or DB_SERVICE_NAME is required")
        if self.port < 1 or self.port > 65535:
            raise ConfigurationError(f"Invalid DB_PORT: {self.port}")


@dataclass
class TableMappings:
    """Oracle EBS table mappings (schema.table format)."""
    # Inventory
    system_items_b: str
    mtp_parameters: str
    # Planning/Supply Chain
    msc_plans: str
    msc_exception_details: str
    msc_supplies: str
    msc_demands: str
    msc_full_pegging: str
    msc_safety_stocks: str
    msc_system_items: str
    msc_item_suppliers: str
    # Procurement
    po_headers_all: str
    po_lines_all: str
    po_line_locations_all: str
    po_vendors: str
    po_vendor_sites_all: str
    po_agreements: str
    # Other
    hr_locations: str
    ap_terms: str


@dataclass
class DecisionEngineConfig:
    """Decision engine thresholds and parameters."""
    on_time_rate_switch: float
    on_time_rate_monitor: float
    min_deliveries: int
    price_dev_renegotiate: float
    price_dev_review: float
    contract_breach_threshold: float


class AppConfig:
    """Main application configuration class."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file and environment variables.

        Args:
            config_file: Path to config.yaml file. If not provided, uses default location.

        Raises:
            ConfigurationError: If required configuration is missing or invalid.
        """
        load_dotenv()

        if config_file is None:
            config_file = Path(__file__).parent / "config.yaml"
        else:
            config_file = Path(config_file)

        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")

        with open(config_file, "r") as f:
            self._yaml_config = yaml.safe_load(f) or {}

        self._load_database_config()
        self._load_table_mappings()
        self._load_decision_engine_config()
        self._load_workflows_config()
        self._load_output_config()

    def _interpolate_env_vars(self, value: Any) -> Any:
        """Interpolate ${VAR_NAME} with environment variables."""
        if not isinstance(value, str):
            return value

        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ConfigurationError(
                    f"Environment variable {var_name} is required but not set"
                )
            return env_value

        return re.sub(r"\$\{(\w+)\}", replace_var, value)

    def _load_database_config(self) -> None:
        """Load and validate database configuration."""
        db_cfg = self._yaml_config.get("database", {})

        self.database = DatabaseConfig(
            host=self._interpolate_env_vars(db_cfg.get("host", "")),
            port=int(self._interpolate_env_vars(db_cfg.get("port", "1521"))),
            sid=self._interpolate_env_vars(db_cfg.get("sid")) if db_cfg.get("sid") else None,
            service_name=self._interpolate_env_vars(db_cfg.get("service_name")) if db_cfg.get("service_name") else None,
            user=self._interpolate_env_vars(db_cfg.get("user", "")),
            password=self._interpolate_env_vars(db_cfg.get("password", "")),
            oracle_client_path=os.getenv("ORACLE_CLIENT_PATH"),
            pool_min=int(db_cfg.get("pool_min", 1)),
            pool_max=int(db_cfg.get("pool_max", 4)),
            pool_increment=int(db_cfg.get("pool_increment", 1)),
            stmt_cache_size=int(db_cfg.get("stmt_cache_size", 50)),
        )
        self.database.validate()

    def _load_table_mappings(self) -> None:
        """Load table name mappings."""
        tables = self._yaml_config.get("tables", {})

        self.tables = TableMappings(
            # Inventory
            system_items_b=tables.get("inventory", {}).get("system_items_b", "INV.MTL_SYSTEM_ITEMS_B"),
            mtp_parameters=tables.get("inventory", {}).get("parameters", "INV.MTL_PARAMETERS"),
            # Planning/Supply Chain
            msc_plans=tables.get("planning", {}).get("plans", "MSC.MSC_PLANS"),
            msc_exception_details=tables.get("planning", {}).get("exception_details", "MSC.MSC_EXCEPTION_DETAILS"),
            msc_supplies=tables.get("planning", {}).get("supplies", "MSC.MSC_SUPPLIES"),
            msc_demands=tables.get("planning", {}).get("demands", "MSC.MSC_DEMANDS"),
            msc_full_pegging=tables.get("planning", {}).get("full_pegging", "MSC.MSC_FULL_PEGGING"),
            msc_safety_stocks=tables.get("planning", {}).get("safety_stocks", "MSC.MSC_SAFETY_STOCKS"),
            msc_system_items=tables.get("planning", {}).get("system_items", "MSC.MSC_SYSTEM_ITEMS"),
            msc_item_suppliers=tables.get("planning", {}).get("item_suppliers", "MSC.MSC_ITEM_SUPPLIERS"),
            # Procurement
            po_headers_all=tables.get("procurement", {}).get("po_headers_all", "PO.PO_HEADERS_ALL"),
            po_lines_all=tables.get("procurement", {}).get("po_lines_all", "PO.PO_LINES_ALL"),
            po_line_locations_all=tables.get("procurement", {}).get("po_line_locations_all", "PO.PO_LINE_LOCATIONS_ALL"),
            po_vendors=tables.get("procurement", {}).get("po_vendors", tables.get("procurement", {}).get("vendors", "PO.PO_VENDORS_OBS")),
            po_vendor_sites_all=tables.get("procurement", {}).get("vendor_sites", "PO.PO_VENDOR_SITES_OBS"),
            po_agreements=tables.get("procurement", {}).get("agreements", "APPS.PO_AGREEMENTS"),
            # Other
            hr_locations=tables.get("other", {}).get("hr_locations", "HR.HR_LOCATIONS"),
            ap_terms=tables.get("other", {}).get("ap_terms", "APPS.AP_TERMS"),
        )

    def _load_decision_engine_config(self) -> None:
        """Load decision engine thresholds."""
        de = self._yaml_config.get("decision_engine", {})
        supplier = de.get("supplier_performance", {})
        pricing = de.get("pricing", {})

        self.decision_engine = DecisionEngineConfig(
            on_time_rate_switch=float(supplier.get("on_time_rate_threshold_switch", 70)),
            on_time_rate_monitor=float(supplier.get("on_time_rate_threshold_monitor", 80)),
            min_deliveries=int(supplier.get("min_deliveries_for_confidence", 20)),
            price_dev_renegotiate=float(pricing.get("price_deviation_renegotiate", 20)),
            price_dev_review=float(pricing.get("price_deviation_review", 10)),
            contract_breach_threshold=float(pricing.get("contract_breach_threshold", 5)),
        )

    def _load_workflows_config(self) -> None:
        """Load workflow configuration."""
        self.workflows = self._yaml_config.get("workflows", {})

    def _load_output_config(self) -> None:
        """Load output configuration."""
        output = self._yaml_config.get("output", {})
        output_path = output.get("directory", "tutorial_agent_outputs")

        # Allow environment variable override, but use default if not set
        env_output_dir = os.getenv("OUTPUT_DIR")
        if env_output_dir:
            output_path = env_output_dir
        elif output_path.startswith("${") and output_path.endswith("}"):
            # Only interpolate if it's an env var reference
            output_path = self._interpolate_env_vars(output_path)

        self.output_dir = Path(output_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_exception_types(self) -> Dict[int, str]:
        """Get exception type mappings."""
        return self._yaml_config.get("exception_types", {})

    def get_priorities(self) -> Dict[str, float]:
        """Get priority score mappings."""
        return self._yaml_config.get("priorities", {})

    def get_autonomy_level(self, level: int) -> Dict[str, Any]:
        """Get autonomy level configuration."""
        autonomy = self._yaml_config.get("autonomy", {})
        level_key = f"level_{level}"
        return autonomy.get(level_key, {})

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        features = self._yaml_config.get("features", {})
        return features.get(f"enable_{feature_name}", False)

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"AppConfig(host={self.database.host}, "
            f"port={self.database.port}, "
            f"user={self.database.user}, "
            f"tables_configured={len(vars(self.tables))})"
        )


# Global configuration instance (lazy loaded)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
