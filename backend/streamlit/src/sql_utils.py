import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import sqlparse


@contextmanager
def get_sqlite_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Create a SQLite connection using a context manager for automatic closure.

    Args:
        db_path (str): Path to the SQLite database file

    Yields:
        sqlite3.Connection: SQLite connection object

    Raises:
        sqlite3.Error: If connection fails
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        yield conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


def execute_sql_select(conn: sqlite3.Connection, query: str, task_tracker=None) -> pd.DataFrame:
    """
    Execute a SQL SELECT query and return results as a Pandas DataFrame with optional task tracking.

    Args:
        conn (sqlite3.Connection): Active SQLite connection
        query (str): SQL SELECT query to execute
        task_tracker: Optional TaskTracker instance for performance monitoring

    Returns:
        pd.DataFrame: DataFrame containing query results
    """
    # Record execution start if task tracker is provided
    if task_tracker:
        task_tracker.record_sql_execution_start()

    start_time = datetime.now()
    try:
        start_time = datetime.now()
        # Execute query and load results into DataFrame
        result = pd.read_sql_query(query, conn)
        execution_duration_s = (datetime.now() - start_time).total_seconds()
        print(f"execution_duration_s: {execution_duration_s}")

        # Record execution completion if task tracker is provided
        if task_tracker:
            task_tracker.record_sql_execution_complete(len(result), execution_duration_s)

        return result

    except Exception as e:
        # Record error if task tracker is provided
        if task_tracker:
            task_tracker.record_error(str(e))
        raise e


def export_database_schema(conn: sqlite3.Connection) -> str:
    """
    Export the database schema as a multiline string.

    Args:
        conn (sqlite3.Connection): Active SQLite connection

    Returns:
        str: Multiline string containing schema information
    """
    schema_lines = ["Database Schema:"]
    try:
        cursor = conn.cursor()

        # Query sqlite_master for tables
        cursor.execute("SELECT name, type, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            return "No tables found in the database."

        # Build schema string
        for table_name, table_type, create_sql in tables:
            schema_lines.append(f"\nTable: {table_name}")
            schema_lines.append(f"Create Statement: {create_sql}")

            # Get column details
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema_lines.append("Columns:")
            for column in columns:
                col_id, col_name, col_type, not_null, default_val, pk = column
                schema_lines.append(
                    f"  - {col_name} ({col_type}), Not Null: {bool(not_null)}, "
                    f"Default: {default_val}, Primary Key: {bool(pk)}"
                )

        return "\n".join(schema_lines)
    except sqlite3.Error as e:
        return f"Error accessing database: {e}"


def validate_sql_query(
    conn: sqlite3.Connection, query: str, user_permissions: set | None = None
) -> tuple[bool, str]:
    """Hàm này dùng Grok gen ra, đang lỗi, để làm placeholder nếu có sử dụng"""

    """
	Validate SQL query for syntax, table/column existence, query type, advanced injection risks,
	schema compatibility, permissions, subqueries, table/column aliases, and foreign keys.

	Args:
	    conn (sqlite3.Connection): Active SQLite connection
	    query (str): SQL query to validate
	    user_permissions (Optional[set]): Set of table names the user can access (None means all tables allowed)

	Returns:
	    Tuple[bool, str]: (is_valid, message) where is_valid indicates if query is valid,
	                      and message provides details on validation result or errors
	"""
    try:
        # Step 1: Check for multiple statements (basic SQL injection detection)
        parsed = sqlparse.parse(query)
        if len(parsed) > 1:
            return False, "Invalid SQL: Multiple statements detected (potential SQL injection)."

        # Step 2: Restrict to SELECT queries
        if not parsed or parsed[0].get_type() != "SELECT":
            return False, "Invalid SQL: Only SELECT queries are allowed."

        # Step 3: Advanced SQL injection detection
        suspicious_patterns = [
            r"\b(1=1|OR\s+1=1|UNION\s+(ALL|SELECT)|--|/\*.*?\*/|;|\bEXEC\b|\bxp_cmdshell\b|\bsp_\b)",
            r"\b(DECLARE|CAST|CONVERT|WAITFOR|DELAY)\b",
            r"\b(DROP\s+TABLE|ALTER\s+TABLE|TRUNCATE|CREATE\s+DATABASE)\b",
        ]
        import re

        query_upper = query.upper()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, "Invalid SQL: Suspicious pattern detected (potential SQL injection)."

        # Step 4: Validate syntax with EXPLAIN QUERY PLAN
        cursor = conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN " + query)

        # Step 5: Extract table names, table aliases, column references, and column aliases
        table_names = set()
        table_aliases = {}  # Maps alias to actual table name
        column_references = []  # List of (table_or_alias, column) tuples
        column_aliases = set()  # Track column aliases in SELECT clause

        def extract_identifiers(statement, in_select_clause=False):
            for token in statement.tokens:
                if isinstance(token, sqlparse.sql.Identifier) and token.is_group:
                    # Handle table names and aliases
                    real_name = token.get_real_name()
                    alias = token.get_alias()
                    if real_name and alias:
                        table_aliases[alias] = real_name
                        table_names.add(real_name)
                    elif real_name:
                        table_names.add(real_name)
                elif isinstance(token, sqlparse.sql.Identifier) and in_select_clause:
                    # Handle column aliases in SELECT clause
                    if token.get_alias():
                        column_aliases.add(token.get_alias())
                    elif "." in str(token):
                        table_ref, col_name = str(token).split(".", 1)
                        column_references.append((table_ref.strip("`"), col_name.strip("`")))
                    else:
                        column_references.append((None, str(token).strip("`")))
                elif isinstance(token, sqlparse.sql.IdentifierList) and in_select_clause:
                    # Handle multiple columns in SELECT
                    for ident in token.get_identifiers():
                        if isinstance(ident, sqlparse.sql.Identifier):
                            if ident.get_alias():
                                column_aliases.add(ident.get_alias())
                            elif "." in str(ident):
                                table_ref, col_name = str(ident).split(".", 1)
                                column_references.append(
                                    (table_ref.strip("`"), col_name.strip("`"))
                                )
                            else:
                                column_references.append((None, str(ident).strip("`")))
                elif isinstance(token, sqlparse.sql.Parenthesis) and token.is_group:
                    # Recursively process subqueries
                    subquery = sqlparse.parse(str(token))[0]
                    extract_identifiers(subquery, in_select_clause=False)
                elif isinstance(token, sqlparse.sql.TokenList):
                    # Detect SELECT clause for column alias handling
                    is_select = any(t for t in token.tokens if str(t).upper() == "SELECT")
                    extract_identifiers(token, in_select_clause=is_select)

        # Process main query and subqueries
        for statement in parsed:
            extract_identifiers(statement, in_select_clause=True)

        # Step 6: Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = {row[0] for row in cursor.fetchall()}

        # Step 7: Validate table existence
        non_existent_tables = table_names - existing_tables
        if non_existent_tables:
            return False, f"Invalid SQL: Table(s) {', '.join(non_existent_tables)} do not exist."

        # Step 8: Validate permissions (simulated)
        if user_permissions is not None:
            unauthorized_tables = table_names - user_permissions
            if unauthorized_tables:
                return (
                    False,
                    f"Invalid SQL: No permission for table(s) {', '.join(unauthorized_tables)}.",
                )

        # Step 9: Validate column existence, excluding aliases
        table_columns = {}
        for table in existing_tables:
            cursor.execute(f"PRAGMA table_info({table});")
            table_columns[table] = {
                row[1]: row[2] for row in cursor.fetchall()
            }  # Map column name to type

        for table_ref, column in column_references:
            if column in column_aliases:
                continue  # Skip if column is an alias
            actual_table = table_aliases.get(table_ref, table_ref) if table_ref else None
            if actual_table and actual_table in table_columns:
                if column not in table_columns[actual_table]:
                    return (
                        False,
                        f"Invalid SQL: Column '{column}' does not exist in table '{actual_table}'.",
                    )
            elif actual_table and actual_table not in table_columns:
                return False, f"Invalid SQL: Table reference '{actual_table}' not found."
            # If table_ref is None, skip column validation (ambiguous without context)

        # Step 10: Schema compatibility (check WHERE clause types)
        for statement in parsed:
            for token in statement.tokens:
                if isinstance(token, sqlparse.sql.Where):
                    for comp in token.get_sublists():
                        if isinstance(comp, sqlparse.sql.Comparison):
                            left = comp.left
                            if isinstance(left, sqlparse.sql.Identifier) and "." in str(left):
                                table_ref, col_name = str(left).split(".", 1)
                                actual_table = table_aliases.get(
                                    table_ref.strip("`"), table_ref.strip("`")
                                )
                                if (
                                    actual_table in table_columns
                                    and col_name.strip("`") in table_columns[actual_table]
                                ):
                                    col_type = table_columns[actual_table][
                                        col_name.strip("`")
                                    ].lower()
                                    right = comp.right
                                    if (
                                        col_type in ("integer", "real")
                                        and right.ttype is sqlparse.tokens.String
                                    ):
                                        return (
                                            False,
                                            f"Invalid SQL: Type mismatch for column '{col_name}' in table '{actual_table}' (expected {col_type}, got string).",
                                        )

        # Step 11: Validate foreign keys
        for table in table_names:
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fk_list = cursor.fetchall()
            for fk in fk_list:
                _, _, ref_table, from_col, to_col, _, _, _ = fk
                if ref_table not in existing_tables:
                    return (
                        False,
                        f"Invalid SQL: Foreign key references non-existent table '{ref_table}'.",
                    )
                if to_col not in table_columns.get(ref_table, {}):
                    return (
                        False,
                        f"Invalid SQL: Foreign key references non-existent column '{to_col}' in table '{ref_table}'.",
                    )

        return (
            True,
            "SQL query is valid: Syntax correct, tables/columns exist, SELECT only, no injection risks, schema compatible, permissions valid, subqueries valid, aliases resolved, foreign keys valid.",
        )

    except sqlite3.Error as e:
        return False, f"Invalid SQL: Syntax error - {str(e)}"
    except Exception as e:
        return False, f"Invalid SQL: Unexpected error - {str(e)}"


def analyze_query_plan(
    conn: sqlite3.Connection, query: str, cost_threshold: float = 1000.0
) -> tuple[bool, str]:
    """Hàm này dùng Grok gen ra, đang lỗi, để làm placeholder nếu có sử dụng"""

    """
	Analyze the query plan of a validated SQL SELECT query and estimate its execution cost.
	Returns False if the estimated cost exceeds the threshold (indicating a slow query).

	Args:
	    conn (sqlite3.Connection): Active SQLite connection
	    query (str): Validated SQL SELECT query to analyze
	    cost_threshold (float): Maximum acceptable cost (default: 1000.0, tunable)

	Returns:
	    Tuple[bool, str]: (is_acceptable, message) where is_acceptable indicates if the query's
	                      estimated cost is below the threshold, and message provides details
	"""
    try:
        cursor = conn.cursor()

        # Step 1: Get the query plan
        cursor.execute("EXPLAIN QUERY PLAN " + query)
        plan = cursor.fetchall()

        # Step 2: Estimate table sizes for cost calculation
        table_sizes = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            table_sizes[table] = cursor.fetchone()[0]

        # Step 3: Analyze query plan and estimate cost
        total_cost = 0.0
        plan_details = []

        for row in plan:
            # SQLite EXPLAIN QUERY PLAN format: (id, parent, notused, detail)
            detail = row[3].lower()
            plan_details.append(detail)

            # Heuristic costs (tunable based on your database characteristics)
            if "scan" in detail and "using index" not in detail:
                # Full table scan: high cost proportional to table size
                table_name = next((t for t in tables if t.lower() in detail), None)
                if table_name:
                    rows = table_sizes.get(table_name, 1000)  # Default to 1000 if unknown
                    cost = rows * 1.0  # 1.0 cost per row for full scan
                    total_cost += cost
                    plan_details.append(f"Cost: {cost:.2f} (full table scan on {table_name})")
            elif "search" in detail and "using index" in detail:
                # Indexed search: low cost, assume logarithmic scaling
                table_name = next((t for t in tables if t.lower() in detail), None)
                if table_name:
                    rows = table_sizes.get(table_name, 1000)
                    cost = min(rows * 0.1, 100.0)  # 0.1 cost per row, capped for indexed search
                    total_cost += cost
                    plan_details.append(f"Cost: {cost:.2f} (indexed search on {table_name})")
            elif "join" in detail:
                # Join operation: moderate cost, depends on join type and table sizes
                cost = 500.0  # Base cost for join (tunable)
                total_cost += cost
                plan_details.append(f"Cost: {cost:.2f} (join operation)")
            else:
                # Other operations (e.g., sorting, grouping): small fixed cost
                cost = 50.0
                total_cost += cost
                plan_details.append(f"Cost: {cost:.2f} (other operation: {detail})")

        # Step 4: Compare total cost to threshold
        message = (
            f"Query plan analysis:\n- Estimated cost: {total_cost:.2f}\n- Threshold: {cost_threshold:.2f}\n- Plan details:\n  "
            + "\n  ".join(plan_details)
        )
        if total_cost > cost_threshold:
            return (
                False,
                message
                + f"\nQuery is too slow: Estimated cost {total_cost:.2f} exceeds threshold {cost_threshold:.2f}.",
            )

        return True, message + "\nQuery is acceptable: Estimated cost is within threshold."

    except sqlite3.Error as e:
        return False, f"Query plan analysis failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during query plan analysis: {str(e)}"
