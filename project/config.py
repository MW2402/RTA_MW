# -----------------------------
# Kafka configuration
# -----------------------------

BROKER = "broker:9092"

TOPIC_INVENTORY = "inventory_events"
TOPIC_SCORED = "scored_inventory_events"
TOPIC_ALERTS = "stockout_alerts"
TOPIC_ONLINE_TRAINING = "online_training_events"


# -----------------------------
# API configuration
# -----------------------------

API_HOST = "0.0.0.0"
API_PORT = 8001
API_URL = "http://localhost:8001/score"
API_TIMEOUT_SECONDS = 2


# -----------------------------
# Model paths
# -----------------------------

MODEL_DIR = "models"
MODEL_PATH = f"{MODEL_DIR}/stockout_model.pkl"
CATEGORY_MAPPING_PATH = f"{MODEL_DIR}/category_mapping.json"
STORE_MAPPING_PATH = f"{MODEL_DIR}/store_mapping.json"


# -----------------------------
# Data paths
# -----------------------------

DATA_DIR = "data"
SYNTHETIC_TRAINING_DATA_PATH = f"{DATA_DIR}/synthetic_training_data.csv"
SAMPLE_EVENTS_PATH = f"{DATA_DIR}/sample_events.jsonl"
ONLINE_TRAINING_BUFFER_PATH = f"{DATA_DIR}/online_training_buffer.csv"


# -----------------------------
# Logging paths
# -----------------------------

LOG_DIR = "logs"
ALERT_LOG_PATH = f"{LOG_DIR}/alerts.log"


# -----------------------------
# Business thresholds
# -----------------------------

ALERT_THRESHOLD = 0.75

LOW_STOCK_THRESHOLD = 10
HIGH_SALES_THRESHOLD = 8

ONLINE_UPDATE_BATCH_SIZE = 50


# -----------------------------
# Synthetic data configuration
# -----------------------------

STORES = ["S01", "S02", "S03", "S04"]

PRODUCT_CATEGORIES = [
    "dairy",
    "bakery",
    "beverages",
    "snacks",
    "frozen",
    "household",
]

PRODUCT_IDS = [
    f"P{i:03d}" for i in range(1, 21)
]

SHELF_CAPACITY_BY_CATEGORY = {
    "dairy": 40,
    "bakery": 35,
    "beverages": 60,
    "snacks": 50,
    "frozen": 45,
    "household": 30,
}


# -----------------------------
# ML configuration
# -----------------------------

RANDOM_SEED = 42

MODEL_CLASSES = [0, 1]

FEATURE_COLUMNS = [
    "current_stock",
    "shelf_capacity",
    "sales_last_10min",
    "stock_ratio",
    "replenishment_pending",
    "category_encoded",
    "store_encoded",
]


# -----------------------------
# Runtime behavior
# -----------------------------

PRODUCER_SLEEP_SECONDS = 0.5
PRODUCER_EVENT_COUNT = 1000

MODEL_RELOAD_INTERVAL_SECONDS = 5
MODEL_SNAPSHOT_DIR = f"{MODEL_DIR}/snapshots"
SAVE_MODEL_SNAPSHOTS = True
