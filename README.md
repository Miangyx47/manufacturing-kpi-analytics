# Manufacturing KPI Analytics

An end-to-end manufacturing analytics project using MySQL, Python, Pandas, and Power BI to automate production reporting and identify abnormal manufacturing conditions.

## Project Objectives

- Generate realistic manufacturing production data
- Store and manage production data in MySQL
- Calculate daily manufacturing KPIs using SQL
- Automate data processing and reporting with Python
- Build an interactive production dashboard
- Detect abnormal production and equipment conditions

## Key Performance Indicators

- Production Output
- Yield Rate
- Defect Rate
- Equipment Downtime
- Cycle Time
- Capacity Utilization

## Technology Stack

- Python
- Pandas
- MySQL
- SQLAlchemy
- Excel / Power BI
- Git and GitHub

## Project Structure

```text
data/        Raw and processed manufacturing data
sql/         MySQL database and KPI queries
src/         Python automation scripts
notebooks/   Exploratory data analysis
dashboard/   Dashboard files and screenshots
reports/     Generated KPI reports 
```

## Dashboard

The project includes an automated Excel dashboard that connects to the MySQL manufacturing database and visualizes key operational metrics.

![Manufacturing KPI Dashboard](dashboard/screenshots/manufacturing_dashboard.png)

## Dashboard Metrics

- Total production output
- Yield rate
- Defect rate
- Capacity utilization
- Abnormal production batches
- Daily production trends
- Daily defect-rate trends
- Equipment defect-rate comparison
- Equipment downtime comparison
- Shift production performance

## Data Pipeline

```text
Simulated Manufacturing Data
        ↓
CSV Data Source
        ↓
Python Data Validation
        ↓
MySQL Production Database
        ↓
SQL KPI Analysis
        ↓
Excel KPI Reports and Dashboard
        ↓
Automated Warning and Critical Alerts