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


def get_overall_kpis(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            COUNT(*) AS total_batches,
            SUM(planned_capacity) AS total_planned_capacity,
            SUM(units_produced) AS total_units_produced,
            SUM(good_units) AS total_good_units,
            SUM(defective_units) AS total_defective_units,
            ROUND(
                SUM(good_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS yield_rate_pct,
            ROUND(
                SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS defect_rate_pct,
            ROUND(
                SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
                2
            ) AS capacity_utilization_pct,
            ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
            ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
            SUM(abnormal_flag) AS abnormal_batches
        FROM production_records;
        """
    )

    return pd.read_sql(query, engine)


def get_daily_kpis(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            production_date,
            COUNT(*) AS total_batches,
            SUM(planned_capacity) AS planned_capacity,
            SUM(units_produced) AS units_produced,
            SUM(good_units) AS good_units,
            SUM(defective_units) AS defective_units,
            ROUND(
                SUM(good_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS yield_rate_pct,
            ROUND(
                SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS defect_rate_pct,
            ROUND(
                SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
                2
            ) AS capacity_utilization_pct,
            ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
            ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
            SUM(abnormal_flag) AS abnormal_batches
        FROM production_records
        GROUP BY production_date
        ORDER BY production_date;
        """
    )

    return pd.read_sql(query, engine)


def get_machine_kpis(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            machine_id,
            COUNT(*) AS total_batches,
            SUM(units_produced) AS units_produced,
            SUM(good_units) AS good_units,
            SUM(defective_units) AS defective_units,
            ROUND(
                SUM(good_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS yield_rate_pct,
            ROUND(
                SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS defect_rate_pct,
            ROUND(
                SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
                2
            ) AS capacity_utilization_pct,
            ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
            ROUND(SUM(downtime_minutes), 2) AS total_downtime_minutes,
            ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
            SUM(abnormal_flag) AS abnormal_batches
        FROM production_records
        GROUP BY machine_id
        ORDER BY defect_rate_pct DESC;
        """
    )

    return pd.read_sql(query, engine)


def get_shift_kpis(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            shift_name,
            COUNT(*) AS total_batches,
            SUM(units_produced) AS units_produced,
            SUM(defective_units) AS defective_units,
            ROUND(
                SUM(good_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS yield_rate_pct,
            ROUND(
                SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS defect_rate_pct,
            ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
            ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
            SUM(abnormal_flag) AS abnormal_batches
        FROM production_records
        GROUP BY shift_name
        ORDER BY defect_rate_pct DESC;
        """
    )

    return pd.read_sql(query, engine)


def get_product_kpis(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            product_type,
            COUNT(*) AS total_batches,
            SUM(units_produced) AS units_produced,
            SUM(defective_units) AS defective_units,
            ROUND(
                SUM(good_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS yield_rate_pct,
            ROUND(
                SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
                2
            ) AS defect_rate_pct,
            ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
            ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
            SUM(abnormal_flag) AS abnormal_batches
        FROM production_records
        GROUP BY product_type
        ORDER BY defect_rate_pct DESC;
        """
    )

    return pd.read_sql(query, engine)


def get_abnormal_records(engine) -> pd.DataFrame:
    query = text(
        """
        SELECT
            batch_id,
            production_date,
            machine_id,
            product_type,
            shift_name,
            units_produced,
            defective_units,
            ROUND(
                defective_units / NULLIF(units_produced, 0) * 100,
                2
            ) AS defect_rate_pct,
            downtime_minutes,
            cycle_time_minutes,
            temperature_c,
            pressure_kpa,
            abnormal_flag
        FROM production_records
        WHERE
            abnormal_flag = 1
            OR defective_units / NULLIF(units_produced, 0) > 0.08
            OR downtime_minutes > 90
            OR cycle_time_minutes > 85
        ORDER BY production_date, machine_id, batch_id;
        """
    )

    return pd.read_sql(query, engine)


def format_excel_report(output_path: Path, dataframes: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, dataframe in dataframes.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook = writer.book

        for sheet_name, dataframe in dataframes.items():
            worksheet = workbook[sheet_name]

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    value = "" if cell.value is None else str(cell.value)
                    max_length = max(max_length, len(value))

                worksheet.column_dimensions[column_letter].width = min(
                    max_length + 2,
                    30,
                )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    reports_directory = project_root / "reports"
    reports_directory.mkdir(parents=True, exist_ok=True)

    output_path = reports_directory / "manufacturing_kpi_report.xlsx"

    try:
        engine = get_database_engine()

        dataframes = {
            "Overall KPI": get_overall_kpis(engine),
            "Daily KPI": get_daily_kpis(engine),
            "Machine KPI": get_machine_kpis(engine),
            "Shift KPI": get_shift_kpis(engine),
            "Product KPI": get_product_kpis(engine),
            "Abnormal Records": get_abnormal_records(engine),
        }

        format_excel_report(output_path, dataframes)

        print("Excel KPI report generated successfully.")
        print(f"Saved report to: {output_path}")

        print("\nOverall KPI summary:")
        print(dataframes["Overall KPI"].to_string(index=False))

        print(
            "\nAbnormal records:",
            len(dataframes["Abnormal Records"]),
        )

    except Exception as error:
        print(f"Report generation failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()