import json

import requests
from kafka import KafkaConsumer, KafkaProducer

from config import (
    BROKER,
    API_URL,
    API_TIMEOUT_SECONDS,
    ALERT_THRESHOLD,
    TOPIC_INVENTORY,
    TOPIC_SCORED,
    TOPIC_ALERTS,
    TOPIC_ONLINE_TRAINING,
    CATEGORY_MAPPING_PATH,
    STORE_MAPPING_PATH,
)
from feature_engineering import (
    load_json_mapping,
    build_features_from_event,
    build_online_training_event,
)


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC_INVENTORY,
        bootstrap_servers=BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="stockout-ml-consumer",
    )


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def load_mappings():
    category_mapping = load_json_mapping(CATEGORY_MAPPING_PATH)
    store_mapping = load_json_mapping(STORE_MAPPING_PATH)

    return category_mapping, store_mapping


def call_scoring_api(features: dict):
    try:
        response = requests.post(
            API_URL,
            json=features,
            timeout=API_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None


def build_scored_event(
    event: dict,
    features: dict,
    result: dict,
) -> dict:
    return {
        **event,
        "stock_ratio": features["stock_ratio"],
        "stockout_risk": result["stockout_risk"],
        "stockout_probability": result["stockout_probability"],
        "model": result["model"],
    }


def build_alert(scored_event: dict) -> dict:
    return {
        "event_id": scored_event["event_id"],
        "product_id": scored_event["product_id"],
        "store_id": scored_event["store_id"],
        "category": scored_event["category"],
        "current_stock": scored_event["current_stock"],
        "shelf_capacity": scored_event["shelf_capacity"],
        "sales_last_10min": scored_event["sales_last_10min"],
        "replenishment_pending": scored_event["replenishment_pending"],
        "timestamp": scored_event["timestamp"],
        "stockout_probability": scored_event["stockout_probability"],
        "alert_source": "ml_model",
        "alert_reason": "High stock-out probability",
    }


def process_event(
    event: dict,
    producer: KafkaProducer,
    category_mapping: dict,
    store_mapping: dict,
):
    features = build_features_from_event(
        event,
        category_mapping,
        store_mapping,
    )

    result = call_scoring_api(features)

    if result is None:
        return

    scored_event = build_scored_event(
        event,
        features,
        result,
    )

    producer.send(
        TOPIC_SCORED,
        value=scored_event,
    )

    training_event = build_online_training_event(
        event,
        features,
    )

    producer.send(
        TOPIC_ONLINE_TRAINING,
        value=training_event,
    )

    if (
        result["stockout_risk"]
        and result["stockout_probability"] >= ALERT_THRESHOLD
    ):
        alert = build_alert(scored_event)

        producer.send(
            TOPIC_ALERTS,
            value=alert,
        )

        print(
            f"ALERT | "
            f"{alert['product_id']} | "
            f"{alert['store_id']} | "
            f"prob={alert['stockout_probability']:.4f}"
        )
    else:
        print(
            f"SCORED | "
            f"{event['product_id']} | "
            f"{event['store_id']} | "
            f"prob={result['stockout_probability']:.4f}"
        )


def main():
    consumer = create_consumer()
    producer = create_producer()

    category_mapping, store_mapping = load_mappings()

    try:
        print(
            f"Listening for events on topic '{TOPIC_INVENTORY}'..."
        )

        for message in consumer:
            process_event(
                event=message.value,
                producer=producer,
                category_mapping=category_mapping,
                store_mapping=store_mapping,
            )

    except KeyboardInterrupt:
        print("\nStopping consumer...")

    finally:
        producer.flush()
        producer.close()
        consumer.close()

        print("Consumer stopped.")


if __name__ == "__main__":
    main()