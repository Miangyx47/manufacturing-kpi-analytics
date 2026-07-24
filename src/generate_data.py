from pathlib import Path
import random

import numpy as np
import pandas as pd


RANDOM_SEED = 42
NUM_RECORDS = 3000

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def generate_manufacturing_data(num_records: int) -> pd.DataFrame:
    """
    Generate simulated manufacturing production records.

    Each row represents one production batch processed by a machine.
    """

    start_date = pd.Timestamp("2026-01-01")
    end_date = pd.Timestamp("2026-03-31")

    machines = [f"M-{i:02d}" for i in range(1, 11)]
    products = ["Chip-A", "Chip-B", "Chip-C"]
    shifts = ["Day", "Evening", "Night"]

    records = []

    for batch_number in range(1, num_records + 1):
        production_date = pd.Timestamp(
            random.randint(
                int(start_date.timestamp()),
                int(end_date.timestamp()),
            ),
            unit="s",
        ).normalize()

        machine_id = random.choice(machines)
        product_type = random.choice(products)
        shift = random.choice(shifts)

        planned_capacity = random.randint(850, 1200)

        utilization_rate = np.clip(
            np.random.normal(loc=0.86, scale=0.08),
            0.55,
            1.0,
        )

        units_produced = int(planned_capacity * utilization_rate)

        defect_rate = np.clip(
            np.random.normal(loc=0.025, scale=0.012),
            0.003,
            0.12,
        )

        defective_units = int(units_produced * defect_rate)
        good_units = units_produced - defective_units

        downtime_minutes = max(
            0,
            round(np.random.exponential(scale=18), 2),
        )

        cycle_time_minutes = max(
            20,
            round(np.random.normal(loc=55, scale=8), 2),
        )

        temperature_c = round(
            np.random.normal(loc=23, scale=1.5),
            2,
        )

        pressure_kpa = round(
            np.random.normal(loc=101.3, scale=2.0),
            2,
        )

        # Introduce some abnormal records for later anomaly detection.
        abnormal_flag = 0

        if random.random() < 0.05:
            defective_units = int(units_produced * random.uniform(0.08, 0.15))
            good_units = units_produced - defective_units
            abnormal_flag = 1

        if random.random() < 0.04:
            downtime_minutes = round(random.uniform(90, 240), 2)
            abnormal_flag = 1

        if random.random() < 0.03:
            cycle_time_minutes = round(random.uniform(85, 130), 2)
            abnormal_flag = 1

        records.append(
            {
                "batch_id": f"B-{batch_number:05d}",
                "production_date": production_date.date(),
                "machine_id": machine_id,
                "product_type": product_type,
                "shift": shift,
                "planned_capacity": planned_capacity,
                "units_produced": units_produced,
                "good_units": good_units,
                "defective_units": defective_units,
                "downtime_minutes": downtime_minutes,
                "cycle_time_minutes": cycle_time_minutes,
                "temperature_c": temperature_c,
                "pressure_kpa": pressure_kpa,
                "abnormal_flag": abnormal_flag,
            }
        )

    return pd.DataFrame(records)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "data" / "raw" / "manufacturing_data.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    manufacturing_df = generate_manufacturing_data(NUM_RECORDS)
    manufacturing_df = manufacturing_df.sort_values(
        by=["production_date", "machine_id", "batch_id"]
    )

    manufacturing_df.to_csv(output_path, index=False)

    print(f"Generated {len(manufacturing_df):,} manufacturing records.")
    print(f"Saved file to: {output_path}")
    print()
    print(manufacturing_df.head())
    print()
    print("Abnormal records:", manufacturing_df["abnormal_flag"].sum())


if __name__ == "__main__":
    main()