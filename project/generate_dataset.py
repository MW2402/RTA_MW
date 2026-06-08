from pathlib import Path

import pandas as pd

from config import (
    DATA_DIR,
    SYNTHETIC_TRAINING_DATA_PATH,
)
from event_generator import generate_inventory_events


def ensure_data_directory() -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def generate_dataset(n_records: int = 5000) -> pd.DataFrame:
    print(f"Generating {n_records} synthetic inventory events...")

    events = generate_inventory_events(n_records)

    df = pd.DataFrame(events)

    df.to_csv(
        SYNTHETIC_TRAINING_DATA_PATH,
        index=False,
    )

    print("\nDataset generated successfully")
    print(f"Records: {len(df)}")
    print(f"Saved to: {SYNTHETIC_TRAINING_DATA_PATH}")

    return df


def main() -> None:
    ensure_data_directory()
    generate_dataset()


if __name__ == "__main__":
    main()