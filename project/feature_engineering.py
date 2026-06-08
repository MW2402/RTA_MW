import json
from typing import Dict, List, Any

import numpy as np

from config import (
    FEATURE_COLUMNS,
    LOW_STOCK_THRESHOLD,
    HIGH_SALES_THRESHOLD,
)


def load_json_mapping(path: str) -> Dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_mapping(mapping: Dict[str, int], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4, ensure_ascii=False)


def build_category_mapping(categories: List[str]) -> Dict[str, int]:
    return {category: idx for idx, category in enumerate(categories)}


def build_store_mapping(stores: List[str]) -> Dict[str, int]:
    return {store: idx for idx, store in enumerate(stores)}


def encode_value(value: str, mapping: Dict[str, int]) -> int:
    return mapping.get(value, -1)


def compute_stock_ratio(current_stock: int, shelf_capacity: int) -> float:
    if shelf_capacity <= 0:
        return 0.0

    ratio = current_stock / shelf_capacity
    ratio = max(0.0, min(ratio, 1.0))

    return round(ratio, 4)


def build_features_from_event(
    event: Dict[str, Any],
    category_mapping: Dict[str, int],
    store_mapping: Dict[str, int],
) -> Dict[str, Any]:
    current_stock = int(event["current_stock"])
    shelf_capacity = int(event["shelf_capacity"])
    sales_last_10min = int(event["sales_last_10min"])
    replenishment_pending = int(event["replenishment_pending"])

    stock_ratio = compute_stock_ratio(
        current_stock=current_stock,
        shelf_capacity=shelf_capacity,
    )

    category_encoded = encode_value(event["category"], category_mapping)
    store_encoded = encode_value(event["store_id"], store_mapping)

    return {
        "current_stock": current_stock,
        "shelf_capacity": shelf_capacity,
        "sales_last_10min": sales_last_10min,
        "stock_ratio": stock_ratio,
        "replenishment_pending": replenishment_pending,
        "category_encoded": category_encoded,
        "store_encoded": store_encoded,
    }


def features_to_array(features: Dict[str, Any]) -> np.ndarray:
    return np.array(
        [[features[column] for column in FEATURE_COLUMNS]],
        dtype=float,
    )


def batch_features_to_array(records: List[Dict[str, Any]]) -> np.ndarray:
    return np.array(
        [[record[column] for column in FEATURE_COLUMNS] for record in records],
        dtype=float,
    )


def create_stockout_label(event: Dict[str, Any]) -> int:
    is_stockout_risk = (
        int(event["current_stock"]) <= LOW_STOCK_THRESHOLD
        and int(event["sales_last_10min"]) >= HIGH_SALES_THRESHOLD
        and int(event["replenishment_pending"]) == 0
    )

    return int(is_stockout_risk)


def build_online_training_event(
    event: Dict[str, Any],
    features: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build an online training event without a label.

    The label is intentionally not created here.
    In the streaming architecture, ml_consumer.py only sends the event
    and engineered features to Kafka. online_trainer.py later simulates
    delayed business feedback and creates the label before partial_fit().
    """

    return {
        "event_id": event["event_id"],
        "product_id": event["product_id"],
        "store_id": event["store_id"],
        "category": event["category"],
        "timestamp": event["timestamp"],
        **features,
    }