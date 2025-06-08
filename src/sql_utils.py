import re
from typing import Optional, Tuple

import pandas as pd
import sqlparse
import streamlit as st
from sqlalchemy import text

from src.db_utils import get_target_connection


def execute_select_query(query: str) -> Optional[pd.DataFrame]:
	"""
	Execute a SQL SELECT query and return results as a Pandas DataFrame.

	Args:
	    query (str): SQL SELECT query to execute

	Returns:
	    Optional[pd.DataFrame]: DataFrame containing query results, or None if an error occurs
	"""
	conn = get_target_connection()
	if conn is None:
		return None
	try:
		return conn.query(query, ttl=0)  # ttl=0 ensures fresh data
	except Exception as e:
		st.error(f"Error executing query: {e}")
		return None


def export_schema_to_string() -> str:
	"""
	Export the database schema as a multiline string.

	Returns:
	    str: Multiline string containing schema information
	"""
	conn = get_target_connection()
	if conn is None:
		return "No target database connection configured."

	schema_lines = ["Database Schema:"]
	try:
		with conn.session as session:
			result = session.execute(
				text("SELECT name, type, sql FROM sqlite_master WHERE type='table';")
			)
			tables = result.fetchall()

			if not tables:
				return "No tables found in the database."

			for table_name, table_type, create_sql in tables:
				schema_lines.append(f"\nTable: {table_name}")
				schema_lines.append(f"Create Statement: {create_sql}")

				result = session.execute(text(f"PRAGMA table_info({table_name});"))
				columns = result.fetchall()
				schema_lines.append("Columns:")
				for column in columns:
					col_id, col_name, col_type, not_null, default_val, pk = column
					schema_lines.append(
						f"  - {col_name} ({col_type}), Not Null: {bool(not_null)}, "
						f"Default: {default_val}, Primary Key: {bool(pk)}"
					)

		return "\n".join(schema_lines)
	except Exception as e:
		return f"Error accessing database: {e}"


def validate_sql_query(query: str, user_permissions: Optional[set] = None) -> Tuple[bool, str]:
	"""
	Validate SQL query for syntax, table/column existence, query type, advanced injection risks,
	schema compatibility, permissions, subqueries, table/column aliases, and foreign keys.

	Args:
	    query (str): SQL query to validate
	    user_permissions (Optional[set]): Set of table names the user can access (None means all tables allowed)

	Returns:
	    Tuple[bool, str]: (is_valid, message) where is_valid indicates if query is valid,
	                      and message provides details on validation result or errors
	"""
	conn = get_target_connection()
	if conn is None:
		return False, "No target database connection configured."

	try:
		parsed = sqlparse.parse(query)
		if len(parsed) > 1:
			return False, "Invalid SQL: Multiple statements detected (potential SQL injection)."

		if not parsed or parsed[0].get_type() != "SELECT":
			return False, "Invalid SQL: Only SELECT queries are allowed."

		suspicious_patterns = [
			r"\b(1=1|OR\s+1=1|UNION\s+(ALL|SELECT)|--|/\*.*?\*/|;|\bEXEC\b|\bxp_cmdshell\b|\bsp_\b)",
			r"\b(DECLARE|CAST|CONVERT|WAITFOR|DELAY)\b",
			r"\b(DROP\s+TABLE|ALTER\s+TABLE|TRUNCATE|CREATE\s+DATABASE)\b",
		]

		query_upper = query.upper()
		for pattern in suspicious_patterns:
			if re.search(pattern, query_upper, re.IGNORECASE):
				return False, f"Invalid SQL: Suspicious pattern detected (potential SQL injection)."

		with conn.session as session:
			session.execute(text("EXPLAIN QUERY PLAN " + query))

			table_names = set()
			table_aliases = {}
			column_references = []
			column_aliases = set()

			def extract_identifiers(statement, in_select_clause=False):
				for token in statement.tokens:
					if isinstance(token, sqlparse.sql.Identifier) and token.is_group:
						real_name = token.get_real_name()
						alias = token.get_alias()
						if real_name and alias:
							table_aliases[alias] = real_name
							table_names.add(real_name)
						elif real_name:
							table_names.add(real_name)
					elif isinstance(token, sqlparse.sql.Identifier) and in_select_clause:
						if token.get_alias():
							column_aliases.add(token.get_alias())
						elif "." in str(token):
							table_ref, col_name = str(token).split(".", 1)
							column_references.append((table_ref.strip("`"), col_name.strip("`")))
						else:
							column_references.append((None, str(token).strip("`")))
					elif isinstance(token, sqlparse.sql.IdentifierList) and in_select_clause:
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
						subquery = sqlparse.parse(str(token))[0]
						extract_identifiers(subquery, in_select_clause=False)
					elif isinstance(token, sqlparse.sql.TokenList):
						is_select = any(t for t in token.tokens if str(t).upper() == "SELECT")
						extract_identifiers(token, in_select_clause=is_select)

			for statement in parsed:
				extract_identifiers(statement, in_select_clause=True)

			result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table';)"))
			existing_tables = {row[0] for row in result.fetchall()}

			non_existent_tables = table_names - existing_tables
			if non_existent_tables:
				return (
					False,
					f"Invalid SQL: Table(s) {', '.join(non_existent_tables)} do not exist.",
				)

			if user_permissions is not None:
				unauthorized_tables = table_names - user_permissions
				if unauthorized_tables:
					return (
						False,
						f"Invalid SQL: No permission for table(s) {', '.join(unauthorized_tables)}.",
					)

			table_columns = {}
			for table in existing_tables:
				result = session.execute(text(f"PRAGMA table_info({table});"))
				table_columns[table] = {row[1]: row[2] for row in result.fetchall()}

			for table_ref, column in column_references:
				if column in column_aliases:
					continue
				actual_table = table_aliases.get(table_ref, table_ref) if table_ref else None
				if actual_table and actual_table in table_columns:
					if column not in table_columns[actual_table]:
						return (
							False,
							f"Invalid SQL: Column '{column}' does not exist in table '{actual_table}'.",
						)
				elif actual_table and actual_table not in table_columns:
					return False, f"Invalid SQL: Table reference '{actual_table}' not found."

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

			for table in table_names:
				result = session.execute(text(f"PRAGMA foreign_key_list({table});"))
				fk_list = result.fetchall()
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

	except Exception as e:
		return False, f"Invalid SQL: Unexpected error - {str(e)}"


def analyze_query_plan(query: str, cost_threshold: float = 1000.0) -> Tuple[bool, str]:
	"""
	Analyze the query plan of a validated SQL SELECT query and estimate its execution cost.
	Returns False if the estimated cost exceeds the threshold (indicating a slow query).

	Args:
	    query (str): Validated SQL SELECT query to analyze
	    cost_threshold (float): Maximum acceptable cost (default: 1000.0, tunable)

	Returns:
	    Tuple[bool, str]: (is_acceptable, message) where is_acceptable indicates if the query's
	                      estimated cost is below the threshold, and message provides details
	"""
	conn = get_target_connection()
	if conn is None:
		return False, "No target database connection configured."

	try:
		with conn.session as session:
			result = session.execute(text("EXPLAIN QUERY PLAN " + query))
			plan = result.fetchall()

			result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
			tables = [row[0] for row in result.fetchall()]
			table_sizes = {}
			for table in tables:
				df = conn.query(f"SELECT COUNT(*) AS count FROM {table};", ttl=0)
				table_sizes[table] = df["count"].iloc[0] if not df.empty else 0

			total_cost = 0.0
			plan_details = []

			for row in plan:
				detail = row[3].lower()
				plan_details.append(detail)

				if "scan" in detail and "using index" not in detail:
					table_name = next((t for t in tables if t.lower() in detail), None)
					if table_name:
						rows = table_sizes.get(table_name, 1000)
						cost = rows * 1.0
						total_cost += cost
						plan_details.append(f"Cost: {cost:.2f} (full table scan on {table_name})")
				elif "search" in detail and "using index" in detail:
					table_name = next((t for t in tables if t.lower() in detail), None)
					if table_name:
						rows = table_sizes.get(table_name, 1000)
						cost = min(rows * 0.1, 100.0)
						total_cost += cost
						plan_details.append(f"Cost: {cost:.2f} (indexed search on {table_name})")
				elif "join" in detail:
					cost = 500.0
					total_cost += cost
					plan_details.append(f"Cost: {cost:.2f} (join operation)")
				else:
					cost = 50.0
					total_cost += cost
					plan_details.append(f"Cost: {cost:.2f} (other operation: {detail})")

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

	except Exception as e:
		return False, f"Query plan analysis failed: {str(e)}"
