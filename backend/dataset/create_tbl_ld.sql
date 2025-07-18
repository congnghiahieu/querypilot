-- TBL_LD: Customer Loan Debt Summary - Aggregated Table Creation
-- This table aggregates data from t24_customer__s2, t24_ld_loans_and_depo__mnp, and t24_stmt_entry__fa
-- Join conditions: 
--   t24_ld_loans_and_depo__mnp.customer_id = t24_customer__s2.customer_code
--   t24_ld_loans_and_depo__mnp.contract_no_ = t24_stmt_entry__fa.our_reference
-- Filter: t24_stmt_entry__fa records from beginning of year to T-1

DROP TABLE IF EXISTS TBL_LD;

CREATE TABLE TBL_LD AS
WITH stmt_filtered AS (
    SELECT 
        our_reference,
        amt_lcy,
        booking_date,
        year,
        month,
        day
    FROM t24_stmt_entry__fa
    WHERE printf('%04d%02d%02d', year, month, day) 
          BETWEEN printf('%04d0101', CAST(strftime('%Y', date('now', '-1 day')) AS INTEGER))
          AND strftime('%Y%m%d', date('now', '-1 day'))
),
stmt_aggregated AS (
    SELECT 
        our_reference,
        SUM(CAST(amt_lcy AS REAL)) as total_stmt_amt_lcy,
        MIN(booking_date) as value_date
    FROM stmt_filtered
    GROUP BY our_reference
)
SELECT 
    -- Customer and loan contract information
    ld.customer_id,
    c.segment,
    ld.contract_no_,
    ld.currency,
    ld.co_code,
    sa.value_date,

    -- Aggregated statement entry data
    COALESCE(sa.total_stmt_amt_lcy, 0) as total_stmt_amt_lcy,

    -- Metadata
    CAST(strftime('%Y', date('now', '-1 day')) AS INTEGER) as year,
    CAST(strftime('%m', date('now', '-1 day')) AS INTEGER) as month,
    CAST(strftime('%d', date('now', '-1 day')) AS INTEGER) as day

FROM t24_ld_loans_and_depo__mnp ld
INNER JOIN t24_customer__s2 c 
    ON ld.customer_id = c.customer_code
LEFT JOIN stmt_aggregated sa 
    ON ld.contract_no_ = sa.our_reference
ORDER BY ld.contract_no_, year;

-- Note: SQLite doesn't support adding PRIMARY KEY to existing table
-- So we'll create a unique index instead
CREATE UNIQUE INDEX idx_tbl_ld_primary ON TBL_LD(contract_no_, year);

-- Add indexes for better performance
CREATE INDEX idx_tbl_ld_customer_code ON TBL_LD(customer_id);
CREATE INDEX idx_tbl_ld_segment ON TBL_LD(segment);
