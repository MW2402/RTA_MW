import os
import time
from pathlib import Path

import pandas as pd

from config import LOG_DIR

ALERT_CSV_PATH = f"{LOG_DIR}/alerts.csv"
REFRESH_SECONDS = 5


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def load_alerts() -> pd.DataFrame:
    path = Path(ALERT_CSV_PATH)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def print_dashboard(df: pd.DataFrame) -> None:
    clear_screen()

    print("=" * 80)
    print("RETAIL STOCK-OUT TERMINAL DASHBOARD")
    print("=" * 80)

    if df.empty:
        print("\nNo alerts recorded yet.")
        print(f"\nWaiting for data in: {ALERT_CSV_PATH}")
        return

    total_alerts = len(df)
    avg_risk = df["stockout_probability"].mean()
    max_risk = df["stockout_probability"].max()

    print(f"\nTotal alerts: {total_alerts}")
    print(f"Average risk: {avg_risk:.4f}")
    print(f"Maximum risk: {max_risk:.4f}")

    print("\nAlerts by store:")
    print(df["store_id"].value_counts().to_string())

    print("\nAlerts by category:")
    print(df["category"].value_counts().to_string())

    print("\nTop risky products:")
    top_products = (
        df.groupby("product_id")["stockout_probability"]
        .max()
        .sort_values(ascending=False)
        .head(5)
    )
    print(top_products.to_string())

    print("\nLatest alerts:")
    latest = df.tail(10)[
        [
            "received_at",
            "store_id",
            "product_id",
            "category",
            "current_stock",
            "shelf_capacity",
            "sales_last_10min",
            "stockout_probability",
        ]
    ]

    print(latest.to_string(index=False))


def main() -> None:
    try:
        while True:
            df = load_alerts()
            print_dashboard(df)
            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\nTerminal dashboard stopped.")


if __name__ == "__main__":
    main()