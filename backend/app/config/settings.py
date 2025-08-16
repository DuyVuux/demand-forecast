# Default settings for Analysis module
# These act as defaults; runtime overrides are stored in data/analysis/config.json

# Columns that should be excluded from numeric statistics by default
EXCLUDED_COLUMNS = [
    "ORDERKEY",
    "SKU",
    "CUSTOMERCODE",
]

# Columns that should be force-included even if auto-detection flags them as identifiers
INCLUDED_COLUMNS: list[str] = []

# Patterns to detect identifier-like columns (case-insensitive)
# Lightweight rules: exact 'id', endswith '_id', contains 'code', 'sku', 'orderkey'
IDENTIFIER_PATTERNS = [
    "^id$",
    ".*_id$",
    "code",
    "sku",
    "orderkey",
]

# Unique ratio threshold to auto-detect identifier-like columns
# If unique(non-null)/non-null >= threshold and dtype looks integer -> mark as ID-like
UNIQUE_RATIO_THRESHOLD = 0.9

# Columns to be treated with special 'code grouping' logic in column detail view
# Case-insensitive matching. These are typically categorical columns for which we want to see the associated primary codes.
CODE_COLUMNS = [
    "ProductCategory",
    "CustomerCode",
    "BusinessModel",
    "WarehouseCode",
    "Unit",
    "ProductCode", # Can be both a code column and a primary code
]

# The main identifier column to be aggregated when a CODE_COLUMN is selected.
# For example, when viewing 'ProductCategory', we list the SKUs within it.
# This should be a column with high cardinality that uniquely identifies items.
PRIMARY_CODE_COLUMN = "SKU"
