import csv
import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import numpy as np
from kafka import KafkaConsumer

from config import (
    BROKER,
    TOPIC_ONLINE_TRAINING,
    MODEL_PATH,
    MODEL_CLASSES,
    ONLINE_UPDATE_BATCH_SIZE,
    ONLINE_TRAINING_BUFFER_PATH,
    DATA_DIR,
    FEATURE_COLUMNS,
    LOW_STOCK_THRESHOLD,
    HIGH_SALES_THRESHOLD,
    RANDOM_SEED,
    MODEL_SNAPSHOT_DIR,
    SAVE_MODEL_SNAPSHOTS,
)
from feature_engineering import batch_features_to_array


rng = np.random.default_rng(RANDOM_SEED)


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC_ONLINE_TRAINING,
        bootstrap_servers=BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="stockout-online-trainer",
    )


def ensure_data_directory() -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def load_model_bundle() -> dict:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}. Run train_model.py first."
        )

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    required_keys = {"scaler", "classifier", "model_name", "feature_columns"}
    missing_keys = required_keys - set(bundle.keys())

    if missing_keys:
        raise ValueError(
            f"Invalid model bundle. Missing keys: {sorted(missing_keys)}"
        )

    return bundle


def save_model_bundle(bundle: dict) -> None:
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)


def create_noisy_stockout_label(event: Dict[str, Any]) -> int:
    stock_ratio = float(event["stock_ratio"])
    sales_norm = min(float(event["sales_last_10min"]) / 18.0, 1.0)
    replenishment_pending = int(event["replenishment_pending"])

    label_probability = (
        0.45 * (1.0 - stock_ratio)
        + 0.35 * sales_norm
        + 0.20 * (1 - replenishment_pending)
    )

    label_probability = float(np.clip(label_probability, 0.05, 0.95))

    return int(rng.random() < label_probability)


def append_batch_to_csv(
    batch: List[Dict[str, Any]],
    labels: np.ndarray,
) -> None:
    file_exists = os.path.exists(ONLINE_TRAINING_BUFFER_PATH)

    fieldnames = [
        "event_id",
        "product_id",
        "store_id",
        "category",
        "timestamp",
        *FEATURE_COLUMNS,
        "stockout_label",
    ]

    with open(
        ONLINE_TRAINING_BUFFER_PATH,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        if not file_exists:
            writer.writeheader()

        for event, label in zip(batch, labels):
            row = {
                "event_id": event["event_id"],
                "product_id": event["product_id"],
                "store_id": event["store_id"],
                "category": event["category"],
                "timestamp": event["timestamp"],
                "stockout_label": int(label),
            }

            for column in FEATURE_COLUMNS:
                row[column] = event[column]

            writer.writerow(row)


def save_model_snapshot(bundle: dict, update_number: int) -> str:
    Path(MODEL_SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    snapshot_path = (
        f"{MODEL_SNAPSHOT_DIR}/"
        f"stockout_model_update_{update_number:04d}_{timestamp}.pkl"
    )

    with open(snapshot_path, "wb") as f:
        pickle.dump(bundle, f)

    return snapshot_path


def update_model(
    batch: List[Dict[str, Any]],
    update_number: int,
) -> dict:
    labels = np.array(
        [create_noisy_stockout_label(event) for event in batch],
        dtype=int,
    )

    X_batch = batch_features_to_array(batch)

    bundle = load_model_bundle()

    scaler = bundle["scaler"]
    classifier = bundle["classifier"]

    scaler.partial_fit(X_batch)
    X_batch_scaled = scaler.transform(X_batch)

    classifier.partial_fit(
        X_batch_scaled,
        labels,
        classes=np.array(MODEL_CLASSES),
    )

    bundle["scaler"] = scaler
    bundle["classifier"] = classifier
    bundle["last_update_number"] = update_number
    bundle["last_update_time"] = datetime.now().isoformat(timespec="seconds")

    save_model_bundle(bundle)

    snapshot_path = None

    if SAVE_MODEL_SNAPSHOTS:
        snapshot_path = save_model_snapshot(
            bundle=bundle,
            update_number=update_number,
        )

    append_batch_to_csv(
        batch=batch,
        labels=labels,
    )

    return {
        "batch_size": len(batch),
        "positive_labels": int(labels.sum()),
        "negative_labels": int(len(labels) - labels.sum()),
        "average_label": float(labels.mean()),
        "snapshot_path": snapshot_path,
    }

def print_update_summary(update_number: int, summary: dict) -> None:
    print("\n=================================")
    print(f"ONLINE MODEL UPDATE #{update_number}")
    print("=================================")
    print(f"Batch size: {summary['batch_size']}")
    print(f"Positive labels: {summary['positive_labels']}")
    print(f"Negative labels: {summary['negative_labels']}")
    print(f"Positive label rate: {summary['average_label']:.4f}")
    print(f"Model bundle updated: {MODEL_PATH}")
    print(f"Training buffer: {ONLINE_TRAINING_BUFFER_PATH}")
    if summary["snapshot_path"]:
        print(f"Snapshot saved: {summary['snapshot_path']}")


def main() -> None:
    ensure_data_directory()

    consumer = create_consumer()
    buffer = []
    update_number = 0

    print(
        f"Listening for online training events on topic "
        f"'{TOPIC_ONLINE_TRAINING}'..."
    )

    try:
        for message in consumer:
            event = message.value
            buffer.append(event)

            print(
                f"Buffered training event "
                f"{len(buffer)}/{ONLINE_UPDATE_BATCH_SIZE} | "
                f"{event['product_id']} | "
                f"{event['store_id']}"
            )

            if len(buffer) >= ONLINE_UPDATE_BATCH_SIZE:
                batch = buffer[:ONLINE_UPDATE_BATCH_SIZE]
                buffer = buffer[ONLINE_UPDATE_BATCH_SIZE:]

                update_number += 1

                summary = update_model(
                    batch=batch,
                    update_number=update_number,
                )

    except KeyboardInterrupt:
        print("\nStopping online trainer...")

    finally:
        consumer.close()
        print("Online trainer stopped.")


if __name__ == "__main__":
    main()