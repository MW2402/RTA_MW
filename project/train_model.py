import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from config import (
    DATA_DIR,
    MODEL_DIR,
    LOG_DIR,
    SYNTHETIC_TRAINING_DATA_PATH,
    MODEL_PATH,
    CATEGORY_MAPPING_PATH,
    STORE_MAPPING_PATH,
    PRODUCT_CATEGORIES,
    STORES,
    FEATURE_COLUMNS,
    LOW_STOCK_THRESHOLD,
    HIGH_SALES_THRESHOLD,
    RANDOM_SEED,
    MODEL_CLASSES,
)
from feature_engineering import (
    build_category_mapping,
    build_store_mapping,
    save_json_mapping,
    compute_stock_ratio,
)


def create_directories() -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    path = Path(SYNTHETIC_TRAINING_DATA_PATH)

    if not path.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {SYNTHETIC_TRAINING_DATA_PATH}. "
            "Run generate_dataset.py first."
        )

    return pd.read_csv(path)


def create_labels(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)

    base_score = (
        0.45 * (1.0 - (df["current_stock"] / df["shelf_capacity"]).clip(0, 1))
        + 0.35 * (df["sales_last_10min"] / 18).clip(0, 1)
        + 0.20 * (1 - df["replenishment_pending"])
    )

    label_probability = np.clip(base_score, 0.05, 0.95)

    random_values = rng.random(len(df))

    df["stockout_risk"] = (random_values < label_probability).astype(int)
    df["label_probability"] = label_probability.round(4)

    return df


def build_and_save_mappings() -> tuple[dict[str, int], dict[str, int]]:
    category_mapping = build_category_mapping(PRODUCT_CATEGORIES)
    store_mapping = build_store_mapping(STORES)

    save_json_mapping(category_mapping, CATEGORY_MAPPING_PATH)
    save_json_mapping(store_mapping, STORE_MAPPING_PATH)

    return category_mapping, store_mapping


def create_feature_matrix(
    df: pd.DataFrame,
    category_mapping: dict[str, int],
    store_mapping: dict[str, int],
) -> tuple[np.ndarray, np.ndarray]:
    feature_df = pd.DataFrame()

    feature_df["current_stock"] = df["current_stock"].astype(float)
    feature_df["shelf_capacity"] = df["shelf_capacity"].astype(float)
    feature_df["sales_last_10min"] = df["sales_last_10min"].astype(float)

    feature_df["stock_ratio"] = [
        compute_stock_ratio(current_stock, shelf_capacity)
        for current_stock, shelf_capacity in zip(
            df["current_stock"],
            df["shelf_capacity"],
        )
    ]

    feature_df["replenishment_pending"] = df["replenishment_pending"].astype(float)
    feature_df["category_encoded"] = (
        df["category"].map(category_mapping).fillna(-1).astype(float)
    )
    feature_df["store_encoded"] = (
        df["store_id"].map(store_mapping).fillna(-1).astype(float)
    )

    X = feature_df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df["stockout_risk"].to_numpy(dtype=int)

    return X, y


def train_initial_model(X: np.ndarray, y: np.ndarray) -> dict:
    classes = np.array(MODEL_CLASSES)

    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y,
    )

    class_weight_dict = {
        int(cls): float(weight)
        for cls, weight in zip(classes, class_weights)
    }

    scaler = StandardScaler()
    scaler.partial_fit(X)

    X_scaled = scaler.transform(X)

    classifier = SGDClassifier(
        loss="log_loss",
        class_weight=class_weight_dict,
        random_state=RANDOM_SEED,
        alpha=0.01,
        max_iter=1000,
        tol=1e-3,
    )

    classifier.partial_fit(
        X_scaled,
        y,
        classes=classes,
    )

    return {
        "scaler": scaler,
        "classifier": classifier,
        "model_name": "standard_scaler_sgd_classifier_log_loss",
        "feature_columns": FEATURE_COLUMNS,
    }


def save_model_bundle(model_bundle: dict) -> None:
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_bundle, f)


def print_summary(df: pd.DataFrame, X: np.ndarray) -> None:
    positive_count = int(df["stockout_risk"].sum())
    negative_count = int(len(df) - positive_count)

    print("\n=================================")
    print("INITIAL MODEL TRAINED")
    print("=================================")
    print(f"Records: {len(df)}")
    print(f"Positive labels: {positive_count}")
    print(f"Negative labels: {negative_count}")
    print(f"Positive label rate: {positive_count / len(df):.4f}")
    print(f"Features: {X.shape[1]}")
    print("Model: StandardScaler + SGDClassifier(loss='log_loss', alpha=0.01)")
    print(f"Saved model bundle: {MODEL_PATH}")
    print(f"Saved dataset: {SYNTHETIC_TRAINING_DATA_PATH}")
    print(f"Saved category mapping: {CATEGORY_MAPPING_PATH}")
    print(f"Saved store mapping: {STORE_MAPPING_PATH}")


def main() -> None:
    create_directories()

    df = load_dataset()
    df = create_labels(df)

    category_mapping, store_mapping = build_and_save_mappings()

    X, y = create_feature_matrix(
        df=df,
        category_mapping=category_mapping,
        store_mapping=store_mapping,
    )

    model_bundle = train_initial_model(X, y)

    save_model_bundle(model_bundle)

    df.to_csv(
        SYNTHETIC_TRAINING_DATA_PATH,
        index=False,
    )

    print_summary(df, X)


if __name__ == "__main__":
    main()