import random
from datetime import datetime

from config import (
    PRODUCT_IDS,
    STORES,
    PRODUCT_CATEGORIES,
    SHELF_CAPACITY_BY_CATEGORY,
)


def generate_event_id() -> str:
    return f"EVT{random.randint(100000, 999999)}"


def choose_product_context():
    product_id = random.choice(PRODUCT_IDS)
    store_id = random.choice(STORES)
    category = random.choice(PRODUCT_CATEGORIES)
    shelf_capacity = SHELF_CAPACITY_BY_CATEGORY[category]

    return product_id, store_id, category, shelf_capacity


def generate_normal_case(shelf_capacity: int) -> dict:
    min_stock = max(1, int(shelf_capacity * 0.45))

    return {
        "current_stock": random.randint(min_stock, shelf_capacity),
        "sales_last_10min": random.randint(0, 6),
        "replenishment_pending": 1 if random.random() < 0.10 else 0,
    }


def generate_clear_risk_case(shelf_capacity: int) -> dict:
    return {
        "current_stock": random.randint(0, min(8, shelf_capacity)),
        "sales_last_10min": random.randint(10, 18),
        "replenishment_pending": 0,
    }


def generate_low_stock_low_sales_case(shelf_capacity: int) -> dict:
    return {
        "current_stock": random.randint(0, min(10, shelf_capacity)),
        "sales_last_10min": random.randint(0, 5),
        "replenishment_pending": 0,
    }


def generate_medium_stock_high_sales_case(shelf_capacity: int) -> dict:
    lower = max(8, int(shelf_capacity * 0.20))
    upper = max(lower, int(shelf_capacity * 0.45))

    return {
        "current_stock": random.randint(lower, upper),
        "sales_last_10min": random.randint(8, 16),
        "replenishment_pending": 0,
    }


def generate_low_stock_replenishment_case(shelf_capacity: int) -> dict:
    return {
        "current_stock": random.randint(0, min(12, shelf_capacity)),
        "sales_last_10min": random.randint(6, 15),
        "replenishment_pending": 1,
    }


def generate_borderline_case(shelf_capacity: int) -> dict:
    return {
        "current_stock": random.randint(8, min(18, shelf_capacity)),
        "sales_last_10min": random.randint(6, 11),
        "replenishment_pending": 1 if random.random() < 0.35 else 0,
    }


def generate_inventory_event() -> dict:
    (
        product_id,
        store_id,
        category,
        shelf_capacity,
    ) = choose_product_context()

    p = random.random()

    if p < 0.45:
        stock_data = generate_normal_case(shelf_capacity)
    elif p < 0.60:
        stock_data = generate_clear_risk_case(shelf_capacity)
    elif p < 0.72:
        stock_data = generate_low_stock_low_sales_case(shelf_capacity)
    elif p < 0.84:
        stock_data = generate_medium_stock_high_sales_case(shelf_capacity)
    elif p < 0.94:
        stock_data = generate_low_stock_replenishment_case(shelf_capacity)
    else:
        stock_data = generate_borderline_case(shelf_capacity)

    return {
        "event_id": generate_event_id(),
        "product_id": product_id,
        "store_id": store_id,
        "category": category,
        "current_stock": stock_data["current_stock"],
        "shelf_capacity": shelf_capacity,
        "sales_last_10min": stock_data["sales_last_10min"],
        "replenishment_pending": stock_data["replenishment_pending"],
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_inventory_events(n: int) -> list[dict]:
    return [generate_inventory_event() for _ in range(n)]


if __name__ == "__main__":
    for _ in range(10):
        print(generate_inventory_event())