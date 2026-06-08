import json
import time

from kafka import KafkaProducer

from config import (
    BROKER,
    TOPIC_INVENTORY,
    PRODUCER_SLEEP_SECONDS,
)
from event_generator import generate_inventory_event


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def send_event(producer: KafkaProducer, event: dict) -> None:
    producer.send(
        TOPIC_INVENTORY,
        value=event,
    )


def log_event(event_number: int, event: dict) -> None:
    print(
        f"[{event_number:05d}] "
        f"{event['product_id']} | "
        f"{event['store_id']} | "
        f"{event['category']} | "
        f"stock={event['current_stock']}/{event['shelf_capacity']} | "
        f"sales={event['sales_last_10min']} | "
        f"replenishment={event['replenishment_pending']}"
    )


def run_stream(producer: KafkaProducer) -> None:
    event_count = 0

    while True:
        event = generate_inventory_event()

        send_event(producer, event)

        event_count += 1
        log_event(event_count, event)

        time.sleep(PRODUCER_SLEEP_SECONDS)


def main() -> None:
    producer = create_producer()

    try:
        print(
            f"Starting producer -> topic: {TOPIC_INVENTORY}"
        )

        run_stream(producer)

    except KeyboardInterrupt:
        print("\nStopping producer...")

    finally:
        producer.flush()
        producer.close()
        print("Producer closed.")


if __name__ == "__main__":
    main()