from pathlib import Path
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def get_database_engine():
    """
    Create a SQLAlchemy engine using credentials from the .env file.
    """
    load_dotenv()

    required_variables = [
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE",
    ]

    missing_variables = [
        variable for variable in required_variables if not os.getenv(variable)
    ]

    if missing_variables:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing_variables)}"
        )

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE"),
    )

    return create_engine(database_url, pool_pre_ping=True)


def prepare_dataframe(csv_path: Path) -> pd.DataFrame:
    """
    Read and validate the manufacturing CSV file.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_path}\n"
            "Run python src/generate_data.py first."
        )

    dataframe = pd.read_csv(csv_path)

    required_columns = [
        "batch_id",
        "production_date",
        "machine_id",
        "product_type",
        "shift",
        "planned_capacity",
        "units_produced",
        "good_units",
        "defective_units",
        "downtime_minutes",
        "cycle_time_minutes",
        "temperature_c",
        "pressure_kpa",
        "abnormal_flag",
    ]

    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {', '.join(missing_columns)}"
        )

    dataframe = dataframe[required_columns].copy()
    dataframe = dataframe.rename(columns={"shift": "shift_name"})
    dataframe["production_date"] = pd.to_datetime(
        dataframe["production_date"]
    ).dt.date

    return dataframe


def load_data(dataframe: pd.DataFrame, engine) -> None:
    """
    Replace the existing production records with the CSV data.
    """
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE production_records"))

    dataframe.to_sql(
        name="production_records",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
        method="multi",
    )


def verify_upload(engine) -> None:
    """
    Display database row counts and a small data sample.
    """
    verification_query = text(
        """
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT machine_id) AS total_machines,
            MIN(production_date) AS first_date,
            MAX(production_date) AS last_date,
            SUM(abnormal_flag) AS abnormal_records
        FROM production_records;
        """
    )

    sample_query = text(
        """
        SELECT
            batch_id,
            production_date,
            machine_id,
            product_type,
            shift_name,
            units_produced,
            defective_units,
            abnormal_flag
        FROM production_records
        ORDER BY production_date, batch_id
        LIMIT 5;
        """
    )

    summary = pd.read_sql(verification_query, engine)
    sample = pd.read_sql(sample_query, engine)

    print("\nUpload summary:")
    print(summary.to_string(index=False))

    print("\nFirst five database records:")
    print(sample.to_string(index=False))


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "data" / "raw" / "manufacturing_data.csv"

    try:
        dataframe = prepare_dataframe(csv_path)
        engine = get_database_engine()

        print(f"Preparing to upload {len(dataframe):,} records...")
        load_data(dataframe, engine)
        verify_upload(engine)

        print("\nData upload completed successfully.")

    except Exception as error:
        print(f"\nData upload failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()