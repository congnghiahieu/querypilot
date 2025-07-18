-- Auto-generated CREATE TABLE statements
-- Generated from parquet files in table directories
-- Total tables: 7

-- Table: banca_aia_agent_info__mnp
DROP TABLE IF EXISTS banca_aia_agent_info__mnp;
CREATE TABLE banca_aia_agent_info__mnp (
    id VARCHAR(100) PRIMARY KEY,
    producer_code VARCHAR(100),
    producer_name VARCHAR(100),
    dao_code VARCHAR(100),
    birthday VARCHAR(100),
    idno VARCHAR(100),
    mobile VARCHAR(100),
    email VARCHAR(100),
    email_bancas VARCHAR(100),
    bank_agent_type VARCHAR(100),
    bank_role VARCHAR(100),
    allow_sale VARCHAR(100),
    bank_name VARCHAR(100),
    sub_channel VARCHAR(100),
    region VARCHAR(100),
    branch_id VARCHAR(100),
    branch_codevn VARCHAR(100),
    branch_name VARCHAR(100),
    status VARCHAR(100),
    first_contract_date VARCHAR(100),
    terminate_date VARCHAR(100),
    reinstate_date VARCHAR(100),
    recruit_code VARCHAR(100),
    recruit_name VARCHAR(100),
    sm_code VARCHAR(100),
    sm_name VARCHAR(100),
    rh_name VARCHAR(100),
    sd_name VARCHAR(100),
    reason_leave VARCHAR(100),
    on_leave_from VARCHAR(100),
    on_leave_to VARCHAR(100),
    gender VARCHAR(100),
    atc1_class VARCHAR(100),
    last_executed_time VARCHAR(100),
    tf_sourcing_at DATETIME,
    tf_etl_at DATETIME,
    tf_partition_date DATETIME
);

-- Table: edoc_alf_new_data_loan__mnp
DROP TABLE IF EXISTS edoc_alf_new_data_loan__mnp;
CREATE TABLE edoc_alf_new_data_loan__mnp (
    app_id VARCHAR(100) PRIMARY KEY,
    ld_code VARCHAR(100),
    current_outstanding_balance VARCHAR(100),
    out_of_date VARCHAR(100),
    ld_confirm VARCHAR(100),
    debt_collection_account VARCHAR(100),
    debt_payment_method VARCHAR(100),
    repayment_period VARCHAR(100),
    current_interest VARCHAR(100),
    early_repayment_fee VARCHAR(100),
    preferential_rebate VARCHAR(100),
    total_amount_due_coll VARCHAR(100),
    pd_confirm VARCHAR(100),
    pdld_number VARCHAR(100),
    debt_collection_account_pd VARCHAR(100),
    total_amount_overdue VARCHAR(100),
    reasons_for_debt_collect VARCHAR(100),
    data_datetime VARCHAR(100),
    amount_proposed_to_repay VARCHAR(100),
    mien_giam_confirm VARCHAR(100),
    early_repayment_fee_qd VARCHAR(100),
    loan_product VARCHAR(100)
);

-- Table: t24_account_debit_int_details__mnp
DROP TABLE IF EXISTS t24_account_debit_int_details__mnp;
CREATE TABLE t24_account_debit_int_details__mnp (
    account_no_date VARCHAR(100) PRIMARY KEY,
    m VARCHAR(100),
    s VARCHAR(100),
    dr_int_rate VARCHAR(100),
    inputter VARCHAR(100),
    date_time VARCHAR(100),
    co_code VARCHAR(100),
    dr_limit_amt VARCHAR(100),
    tf_sourcing_at DATETIME,
    tf_etl_at DATETIME,
    tf_partition_date DATETIME
);

-- Table: t24_customer__s2
DROP TABLE IF EXISTS t24_customer__s2;
CREATE TABLE t24_customer__s2 (
    customer_code VARCHAR(100) PRIMARY KEY,
    segment VARCHAR(100)
);

-- Table: t24_ld_loans_and_depo__mnp
DROP TABLE IF EXISTS t24_ld_loans_and_depo__mnp;
CREATE TABLE t24_ld_loans_and_depo__mnp (
    contract_no_ VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100),
    currency VARCHAR(100),
    co_code VARCHAR(100),
    value_date DATETIME,
    category VARCHAR(100),
    FOREIGN KEY (customer_id) REFERENCES t24_customer__s2(customer_code)
);

-- Table: t24_ld_loans_and_depo_details__mnp
DROP TABLE IF EXISTS t24_ld_loans_and_depo_details__mnp;
CREATE TABLE t24_ld_loans_and_depo_details__mnp (
    contract_no_ VARCHAR(100) PRIMARY KEY,
    amount INTEGER,
    m INTEGER,
    s INTEGER,
    FOREIGN KEY (contract_no_) REFERENCES t24_ld_loans_and_depo__mnp(contract_no_)
);

-- Table: t24_stmt_entry__fa
DROP TABLE IF EXISTS t24_stmt_entry__fa;
CREATE TABLE t24_stmt_entry__fa (
    stmt_entry_id VARCHAR(100) PRIMARY KEY,
    transaction_code INTEGER,
    our_reference VARCHAR(100),
    amt_lcy INTEGER,
    booking_date DATETIME,
    year VARCHAR(100),
    month VARCHAR(100),
    day VARCHAR(100),
    FOREIGN KEY (our_reference) REFERENCES t24_ld_loans_and_depo__mnp(contract_no_)
);