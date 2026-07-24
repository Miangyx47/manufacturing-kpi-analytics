USE manufacturing_analytics;

DROP TABLE IF EXISTS production_records;

CREATE TABLE production_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(20) NOT NULL UNIQUE,
    production_date DATE NOT NULL,
    machine_id VARCHAR(20) NOT NULL,
    product_type VARCHAR(50) NOT NULL,
    shift_name VARCHAR(20) NOT NULL,
    planned_capacity INT NOT NULL,
    units_produced INT NOT NULL,
    good_units INT NOT NULL,
    defective_units INT NOT NULL,
    downtime_minutes DECIMAL(10, 2) NOT NULL,
    cycle_time_minutes DECIMAL(10, 2) NOT NULL,
    temperature_c DECIMAL(6, 2) NOT NULL,
    pressure_kpa DECIMAL(7, 2) NOT NULL,
    abnormal_flag TINYINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_production_date (production_date),
    INDEX idx_machine_id (machine_id),
    INDEX idx_product_type (product_type),
    INDEX idx_shift_name (shift_name)
);