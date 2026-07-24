USE manufacturing_analytics;

-- =========================================================
-- 1. Overall production KPI summary
-- =========================================================

SELECT
    COUNT(*) AS total_batches,
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
    ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    ROUND(
        SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
        2
    ) AS capacity_utilization_pct
FROM production_records;


-- =========================================================
-- 2. Daily KPI summary
-- =========================================================

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
    ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    ROUND(
        SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
        2
    ) AS capacity_utilization_pct
FROM production_records
GROUP BY production_date
ORDER BY production_date;


-- =========================================================
-- 3. Machine performance analysis
-- =========================================================

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
    ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
    ROUND(SUM(downtime_minutes), 2) AS total_downtime_minutes,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    ROUND(
        SUM(units_produced) / NULLIF(SUM(planned_capacity), 0) * 100,
        2
    ) AS capacity_utilization_pct
FROM production_records
GROUP BY machine_id
ORDER BY defect_rate_pct DESC;


-- =========================================================
-- 4. Shift performance analysis
-- =========================================================

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
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes
FROM production_records
GROUP BY shift_name
ORDER BY defect_rate_pct DESC;


-- =========================================================
-- 5. Product performance analysis
-- =========================================================

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
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes
FROM production_records
GROUP BY product_type
ORDER BY defect_rate_pct DESC;


-- =========================================================
-- 6. Abnormal production records
-- =========================================================

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
    abnormal_flag
FROM production_records
WHERE
    abnormal_flag = 1
    OR defective_units / NULLIF(units_produced, 0) > 0.08
    OR downtime_minutes > 90
    OR cycle_time_minutes > 85
ORDER BY production_date, machine_id;


-- =========================================================
-- 7. Daily abnormal alert summary
-- =========================================================

SELECT
    production_date,
    COUNT(*) AS abnormal_batches,
    COUNT(DISTINCT machine_id) AS affected_machines,
    ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    ROUND(
        AVG(defective_units / NULLIF(units_produced, 0)) * 100,
        2
    ) AS avg_defect_rate_pct
FROM production_records
WHERE
    abnormal_flag = 1
    OR defective_units / NULLIF(units_produced, 0) > 0.08
    OR downtime_minutes > 90
    OR cycle_time_minutes > 85
GROUP BY production_date
ORDER BY production_date;


-- =========================================================
-- 8. Worst-performing machines
-- =========================================================

SELECT
    machine_id,
    COUNT(*) AS total_batches,
    ROUND(
        SUM(defective_units) / NULLIF(SUM(units_produced), 0) * 100,
        2
    ) AS defect_rate_pct,
    ROUND(AVG(downtime_minutes), 2) AS avg_downtime_minutes,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    SUM(abnormal_flag) AS abnormal_batches
FROM production_records
GROUP BY machine_id
HAVING COUNT(*) >= 10
ORDER BY
    defect_rate_pct DESC,
    avg_downtime_minutes DESC
LIMIT 5;