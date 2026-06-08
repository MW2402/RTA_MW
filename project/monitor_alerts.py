import csv
import json
import os
from datetime import datetime
from pathlib import Path

from kafka import KafkaConsumer

from config import (
    BROKER,
    TOPIC_ALERTS,
    LOG_DIR,
)

ALERT_CSV_PATH = f"{LOG_DIR}/alerts.csv"


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC_ALERTS,
        bootstrap_servers=BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="stockout-alert-monitor",
    )


def ensure_log_directory() -> None:
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def format_alert(alert: dict) -> str:
    return (
        f"ALERT | "
        f"Store {alert['store_id']} | "
        f"Product {alert['product_id']} | "
        f"{alert['category']} | "
        f"Risk={alert['stockout_probability']:.4f} | "
        f"Stock={alert['current_stock']}/{alert['shelf_capacity']} | "
        f"Sales={alert['sales_last_10min']} | "
        f"Replenishment={alert['replenishment_pending']} | "
        f"Reason={alert['alert_reason']}"
    )


def write_alert_to_csv(alert: dict) -> None:
    file_exists = os.path.exists(ALERT_CSV_PATH)

    fieldnames = [
        "received_at",
        "event_id",
        "product_id",
        "store_id",
        "category",
        "current_stock",
        "shelf_capacity",
        "sales_last_10min",
        "replenishment_pending",
        "timestamp",
        "stockout_probability",
        "alert_source",
        "alert_reason",
    ]

    row = {
        "received_at": datetime.now().isoformat(timespec="seconds"),
        **alert,
    }

    with open(ALERT_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def main() -> None:
    ensure_log_directory()
    consumer = create_consumer()

    try:
        print(f"Listening for alerts on topic '{TOPIC_ALERTS}'...")
        print(f"Writing alerts to: {ALERT_CSV_PATH}")

        for message in consumer:
            alert = message.value

            print(format_alert(alert))
            write_alert_to_csv(alert)

    except KeyboardInterrupt:
        print("\nStopping alert monitor...")

    finally:
        consumer.close()
        print("Alert monitor stopped.")


if __name__ == "__main__":
    main()