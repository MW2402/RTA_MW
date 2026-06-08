import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from config import LOG_DIR

ALERT_CSV_PATH = f"{LOG_DIR}/alerts.csv"
CHART_DIR = "charts"

CATEGORY_CHART_PATH = f"{CHART_DIR}/alerts_by_category.png"
STORE_CHART_PATH = f"{CHART_DIR}/alerts_by_store.png"

REFRESH_SECONDS = 5


def ensure_chart_directory() -> None:
    Path(CHART_DIR).mkdir(parents=True, exist_ok=True)


def load_alerts() -> pd.DataFrame:
    path = Path(ALERT_CSV_PATH)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def save_empty_chart(path: str, title: str) -> None:
    plt.figure(figsize=(9, 5))
    plt.title(title)
    plt.text(
        0.5,
        0.5,
        "No alerts yet",
        ha="center",
        va="center",
        transform=plt.gca().transAxes,
        fontsize=14,
    )
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_bar_chart(
    counts: pd.Series,
    path: str,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    if counts.empty:
        save_empty_chart(path, title)
        return

    plt.figure(figsize=(9, 5))
    counts.plot(kind="bar")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def generate_charts(df: pd.DataFrame) -> None:
    if df.empty:
        save_empty_chart(
            CATEGORY_CHART_PATH,
            "Stock-out alerts by category",
        )
        save_empty_chart(
            STORE_CHART_PATH,
            "Stock-out alerts by store",
        )
        return

    category_counts = df["category"].value_counts()
    store_counts = df["store_id"].value_counts()

    save_bar_chart(
        counts=category_counts,
        path=CATEGORY_CHART_PATH,
        title="Stock-out alerts by category",
        xlabel="Category",
        ylabel="Number of alerts",
    )

    save_bar_chart(
        counts=store_counts,
        path=STORE_CHART_PATH,
        title="Stock-out alerts by store",
        xlabel="Store",
        ylabel="Number of alerts",
    )


def main() -> None:
    ensure_chart_directory()

    print("Generating live chart image files...")
    print(f"Input: {ALERT_CSV_PATH}")
    print(f"Output: {CHART_DIR}/")
    print("Open the PNG files from the Jupyter file browser.")

    try:
        while True:
            df = load_alerts()
            generate_charts(df)

            print(
                f"Charts updated | "
                f"alerts={len(df)} | "
                f"{CATEGORY_CHART_PATH}, {STORE_CHART_PATH}"
            )

            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\nLive chart generator stopped.")


if __name__ == "__main__":
    main()