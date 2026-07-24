from pathlib import Path
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def get_database_engine():
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


def load_production_data(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            batch_id,
            production_date,
            machine_id,
            product_type,
            shift_name,
            planned_capacity,
            units_produced,
            good_units,
            defective_units,
            downtime_minutes,
            cycle_time_minutes,
            temperature_c,
            pressure_kpa,
            abnormal_flag
        FROM production_records
        ORDER BY production_date, machine_id, batch_id;
        """
    )

    return pd.read_sql(query, engine)


def calculate_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()

    dataframe["defect_rate_pct"] = (
        dataframe["defective_units"]
        / dataframe["units_produced"].replace(0, pd.NA)
        * 100
    )

    dataframe["yield_rate_pct"] = (
        dataframe["good_units"]
        / dataframe["units_produced"].replace(0, pd.NA)
        * 100
    )

    dataframe["capacity_utilization_pct"] = (
        dataframe["units_produced"]
        / dataframe["planned_capacity"].replace(0, pd.NA)
        * 100
    )

    return dataframe


def assign_alert_level(row: pd.Series) -> str:
    """
    Assign an alert level based on manufacturing thresholds.
    """

    critical_conditions = [
        row["defect_rate_pct"] >= 12,
        row["downtime_minutes"] >= 180,
        row["cycle_time_minutes"] >= 110,
        row["capacity_utilization_pct"] < 60,
    ]

    warning_conditions = [
        row["defect_rate_pct"] >= 8,
        row["downtime_minutes"] >= 90,
        row["cycle_time_minutes"] >= 85,
        row["capacity_utilization_pct"] < 70,
    ]

    if any(critical_conditions):
        return "CRITICAL"

    if any(warning_conditions) or row["abnormal_flag"] == 1:
        return "WARNING"

    return "NORMAL"


def build_alert_reason(row: pd.Series) -> str:
    reasons = []

    if row["defect_rate_pct"] >= 12:
        reasons.append("Critical defect rate")
    elif row["defect_rate_pct"] >= 8:
        reasons.append("High defect rate")

    if row["downtime_minutes"] >= 180:
        reasons.append("Critical equipment downtime")
    elif row["downtime_minutes"] >= 90:
        reasons.append("High equipment downtime")

    if row["cycle_time_minutes"] >= 110:
        reasons.append("Critical cycle time")
    elif row["cycle_time_minutes"] >= 85:
        reasons.append("High cycle time")

    if row["capacity_utilization_pct"] < 60:
        reasons.append("Critical low capacity utilization")
    elif row["capacity_utilization_pct"] < 70:
        reasons.append("Low capacity utilization")

    if row["abnormal_flag"] == 1 and not reasons:
        reasons.append("Source data abnormal flag")

    return "; ".join(reasons) if reasons else "No alert"


def detect_anomalies(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = calculate_metrics(dataframe)

    dataframe["alert_level"] = dataframe.apply(
        assign_alert_level,
        axis=1,
    )

    dataframe["alert_reason"] = dataframe.apply(
        build_alert_reason,
        axis=1,
    )

    alerts = dataframe[dataframe["alert_level"] != "NORMAL"].copy()

    alert_order = {
        "CRITICAL": 1,
        "WARNING": 2,
    }

    alerts["alert_priority"] = alerts["alert_level"].map(alert_order)

    alerts = alerts.sort_values(
        by=[
            "alert_priority",
            "production_date",
            "machine_id",
            "batch_id",
        ]
    )

    return alerts.drop(columns=["alert_priority"])


def create_machine_alert_summary(alerts: pd.DataFrame) -> pd.DataFrame:
    if alerts.empty:
        return pd.DataFrame()

    summary = (
        alerts.groupby("machine_id")
        .agg(
            total_alerts=("batch_id", "count"),
            critical_alerts=(
                "alert_level",
                lambda values: (values == "CRITICAL").sum(),
            ),
            warning_alerts=(
                "alert_level",
                lambda values: (values == "WARNING").sum(),
            ),
            avg_defect_rate_pct=("defect_rate_pct", "mean"),
            avg_downtime_minutes=("downtime_minutes", "mean"),
            avg_cycle_time_minutes=("cycle_time_minutes", "mean"),
        )
        .reset_index()
    )

    summary[
        [
            "avg_defect_rate_pct",
            "avg_downtime_minutes",
            "avg_cycle_time_minutes",
        ]
    ] = summary[
        [
            "avg_defect_rate_pct",
            "avg_downtime_minutes",
            "avg_cycle_time_minutes",
        ]
    ].round(2)

    return summary.sort_values(
        by=["critical_alerts", "total_alerts"],
        ascending=[False, False],
    )


def save_alert_reports(
    alerts: pd.DataFrame,
    machine_summary: pd.DataFrame,
    reports_directory: Path,
) -> None:
    reports_directory.mkdir(parents=True, exist_ok=True)

    alerts_csv_path = reports_directory / "manufacturing_alerts.csv"
    summary_csv_path = reports_directory / "machine_alert_summary.csv"
    excel_path = reports_directory / "manufacturing_alert_report.xlsx"

    alerts.to_csv(alerts_csv_path, index=False)
    machine_summary.to_csv(summary_csv_path, index=False)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        alerts.to_excel(
            writer,
            sheet_name="Batch Alerts",
            index=False,
        )

        machine_summary.to_excel(
            writer,
            sheet_name="Machine Summary",
            index=False,
        )

        workbook = writer.book

        for worksheet in workbook.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)

            for column_cells in worksheet.columns:
                max_length = max(
                    len(str(cell.value)) if cell.value is not None else 0
                    for cell in column_cells
                )

                column_letter = column_cells[0].column_letter
                worksheet.column_dimensions[column_letter].width = min(
                    max_length + 2,
                    35,
                )

    print(f"Saved batch alerts to: {alerts_csv_path}")
    print(f"Saved machine summary to: {summary_csv_path}")
    print(f"Saved Excel alert report to: {excel_path}")


def print_alert_summary(
    alerts: pd.DataFrame,
    machine_summary: pd.DataFrame,
) -> None:
    critical_count = (alerts["alert_level"] == "CRITICAL").sum()
    warning_count = (alerts["alert_level"] == "WARNING").sum()

    print("\nAlert summary:")
    print(f"Total alerts: {len(alerts):,}")
    print(f"Critical alerts: {critical_count:,}")
    print(f"Warning alerts: {warning_count:,}")

    if not machine_summary.empty:
        print("\nMachines with the most alerts:")
        print(machine_summary.head(5).to_string(index=False))

    if not alerts.empty:
        print("\nFirst ten alerts:")
        display_columns = [
            "batch_id",
            "production_date",
            "machine_id",
            "defect_rate_pct",
            "downtime_minutes",
            "cycle_time_minutes",
            "capacity_utilization_pct",
            "alert_level",
            "alert_reason",
        ]

        print(
            alerts[display_columns]
            .head(10)
            .round(2)
            .to_string(index=False)
        )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reports_directory = project_root / "reports"

    try:
        engine = get_database_engine()
        production_data = load_production_data(engine)

        alerts = detect_anomalies(production_data)
        machine_summary = create_machine_alert_summary(alerts)

        save_alert_reports(
            alerts,
            machine_summary,
            reports_directory,
        )

        print_alert_summary(alerts, machine_summary)

        print("\nAnomaly detection completed successfully.")

    except Exception as error:
        print(f"Anomaly detection failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()