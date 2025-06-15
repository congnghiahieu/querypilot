import json
import multiprocessing as mp
import sqlite3
import sys
from typing import Any

import backoff
import requests
from func_timeout import FunctionTimedOut, func_timeout
from tqdm import tqdm

from src.settings import LLM_CLIENT, SETTINGS


def nice_look_table(column_names: list[str], values: list[Any]):
	rows = []
	# Determine the maximum width of each column
	widths = [
		max(len(str(value[i])) for value in values + [column_names])
		for i in range(len(column_names))
	]

	# Print the column names
	header = "".join(f"{column.rjust(width)} " for column, width in zip(column_names, widths))
	# Print the values
	for value in values:
		row = "".join(f"{str(v).rjust(width)} " for v, width in zip(value, widths))
		rows.append(row)
	rows = "\n".join(rows)
	final_output = header + "\n" + rows
	return final_output


def generate_schema_prompt(db_path: str, num_rows=None):
	full_schema_prompt_list = []
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
	tables = cursor.fetchall()
	schemas = {}
	for table in tables:
		if table == "sqlite_sequence":
			continue
		cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table[0]}';")
		create_prompt = cursor.fetchone()[0]
		schemas[table[0]] = create_prompt
		if num_rows:
			cur_table = table[0]
			if cur_table in ["order", "by", "group"]:
				cur_table = "`{}`".format(cur_table)

			cursor.execute("SELECT * FROM {} LIMIT {}".format(cur_table, num_rows))
			column_names = [description[0] for description in cursor.description]
			values = cursor.fetchall()
			rows_prompt = nice_look_table(column_names=column_names, values=values)
			verbose_prompt = (
				"/* \n {} example rows: \n SELECT * FROM {} LIMIT {}; \n {} \n */".format(
					num_rows, cur_table, num_rows, rows_prompt
				)
			)
			schemas[table[0]] = "{} \n {}".format(create_prompt, verbose_prompt)

	for k, v in schemas.items():
		full_schema_prompt_list.append(v)

	schema_prompt = "\n\n".join(full_schema_prompt_list)
	return schema_prompt


def generate_question_prompt(question: str):
	system_prompt = "-- You are an expert SQL developer specializing in SQLite. Your task is to convert natural language questions into valid SQLite SQL queries."
	question_prompt = f"-- The question is: {question}"

	result_prompt = system_prompt + "\n" + question_prompt

	return result_prompt


def cot_wizard():
	return "\nGenerate the SQL after thinking step by step: "


def generate_full_prompt(db_path: str, question: str):
	schema_prompt = generate_schema_prompt(db_path, num_rows=None)
	comment_prompt = generate_question_prompt(question)
	# combined_prompts = schema_prompt + '\n\n' + comment_prompt + cot_wizard() + '\nSELECT '
	combined_prompts = schema_prompt + "\n\n" + comment_prompt
	return combined_prompts


@backoff.on_exception(
	backoff.constant,
	requests.exceptions.RequestException,
	giveup=lambda e: isinstance(e, requests.exceptions.RequestException) and "quota" in str(e),
	raise_on_giveup=True,
	interval=20,
)
def call_llm(prompt: str):
	try:
		response = LLM_CLIENT.chat.completions.create(
			model=SETTINGS.LLM_MODEL_NAME,
			messages=[{"role": "user", "content": prompt}],
			max_tokens=256,
			temperature=0,
			stream=False,
		)
		return response.choices[0].message.content
	except Exception as e:
		return f"Error: {str(e)}"


def collect_response_from_llm(db_path_list: list[str], question_list: list[str]):
	response_result = {}

	for i, question in tqdm(enumerate(question_list)):
		print(f"--------------------- processing {i}th question ---------------------")
		print(f"the question is: {question}")

		full_prompt = generate_full_prompt(db_path=db_path_list[i], question=question)
		result = call_llm(prompt=full_prompt)

		if type(result) == str:
			sql = result
		else:
			sql = "SELECT" + result

		db_id = db_path_list[i].split("/")[-1].split(".sqlite")[0]
		sql = sql + "\t----- bird -----\t" + db_id
		response_result[i] = sql

	return response_result


def decouple_question_dbpath(testcases: list[dict], db_root_path: str):
	question_list: list[str] = []
	db_path_list: list[str] = []

	for i, data in enumerate(testcases):
		question_list.append(data["question"])
		cur_db_path = db_root_path + data["db_name"] + "/" + data["db_name"] + ".sqlite"
		db_path_list.append(cur_db_path)

	return question_list, db_path_list


def execute_sql(predicted_sql: str, ground_truth_sql: str, db_path: str):
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	cursor.execute(predicted_sql)
	predicted_res = cursor.fetchall()
	cursor.execute(ground_truth_sql)
	ground_truth_res = cursor.fetchall()

	res = 0
	if set(predicted_res) == set(ground_truth_res):
		res = 1
	return res


def execute_model(
	predicted_sql: str, ground_truth_sql: str, db_path: str, idx: int, meta_time_out: float
):
	try:
		res = func_timeout(
			meta_time_out, execute_sql, args=(predicted_sql, ground_truth_sql, db_path)
		)
	except KeyboardInterrupt:
		sys.exit(0)
	except FunctionTimedOut:
		result = [(f"timeout",)]
		res = 0
	except Exception as e:
		result = [(f"error",)]  # possibly len(query) > 512 or not executable
		res = 0

	result = {"sql_idx": idx, "res": res}
	return result


def clean_sql_query(text_contain_sql: str):
	"""
	Clean SQL query by extracting only the SQL statement from markdown formatted text.

	Args:
	    sql_str (str): Raw SQL string that may contain markdown formatting and explanations

	Returns:
	    str: Clean SQL query
	"""
	# If the query contains markdown code block
	if "```sql" in text_contain_sql:
		# Extract content between ```sql and ```
		start = text_contain_sql.find("```sql") + 6
		end = text_contain_sql.find("```", start)
		if end != -1:
			text_contain_sql = text_contain_sql[start:end]

	text_contain_sql = text_contain_sql.strip()

	return text_contain_sql


def package_sqls(sql_data: dict, db_root_path: str):
	"""
	Package SQL queries and their corresponding database paths for evaluation.

	Args:
	    sql_file_path (str): Path to the file containing SQL queries
	    db_root_path (str): Root path to the database files

	Returns:
	    tuple: (clean_sqls, db_path_list) containing:
	        - clean_sqls: List of SQL queries
	        - db_path_list: List of corresponding database paths
	"""

	clean_sqls = []
	db_path_list = []

	# Predict mode: Load predicted SQL queries from a JSON file
	for idx, sql_str in sql_data.items():
		if type(sql_str) == str:
			# Split the string to get SQL query and database name
			# Format: "SQL_QUERY\t----- bird -----\tDATABASE_NAME"
			parts = sql_str.split("\t----- bird -----\t")
			if len(parts) == 2:
				sql, db_name = parts
				# Clean the SQL query
				sql = clean_sql_query(sql)
			else:
				# Handle invalid format
				sql, db_name = " ", "financial"
		else:
			# Handle invalid predictions with default values
			sql, db_name = " ", "financial"
		clean_sqls.append(sql)
		db_path_list.append(db_root_path + db_name + "/" + db_name + ".sqlite")

	return clean_sqls, db_path_list


def get_gt_sqls(question_path: str, db_root_path: str):
	sql_gt_list = []
	db_path_list = []

	# Load questions from JSON file
	with open(question_path, "r") as f:
		questions = json.load(f)
	for question in questions:
		sql_gt_list.append(question["sql_query"])
		db_path_list.append(
			db_root_path + question["db_name"] + "/" + question["db_name"] + ".sqlite"
		)

	return sql_gt_list, db_path_list


def run_sqls_parallel(
	sqls: list[tuple[str, str]],
	db_paths: list[str],
	num_cpus=1,
	meta_time_out=30.0,
):
	exec_result = []

	pool = mp.Pool(processes=num_cpus)
	for i, sql_pair in enumerate(sqls):
		predicted_sql, ground_truth_sql = sql_pair
		pool.apply_async(
			execute_model,
			args=(predicted_sql, ground_truth_sql, db_paths[i], i, meta_time_out),
			callback=lambda result: exec_result.append(result),
		)
	pool.close()
	pool.join()

	return exec_result


def compute_acc(exec_result: list[dict]):
	num_queries = len(exec_result)
	results = [res["res"] for res in exec_result]

	all_acc = sum(results) / num_queries
	return all_acc * 100, num_queries


if __name__ == "__main__":
	TESTCASE_PATH = "../dataset/BULL-en/dev.json"
	DB_ROOT_PATH = "../dataset/database_en/"
	DATA_MODE = "dev"

	with open(TESTCASE_PATH, "r") as f:
		testcases = json.load(f)

	question_list, db_path_list = decouple_question_dbpath(
		testcases=testcases, db_root_path=DB_ROOT_PATH
	)
	assert len(question_list) == len(db_path_list)

	response_result = collect_response_from_llm(
		db_path_list=db_path_list, question_list=question_list
	)

	print("successfully collect results from Deepseek for {} evaluation.".format(DATA_MODE))

	pred_queries, db_paths = package_sqls(response_result, DB_ROOT_PATH)
	gt_queries, db_paths_gt = get_gt_sqls(TESTCASE_PATH, DB_ROOT_PATH)
	query_pairs = list(zip(pred_queries, gt_queries))

	exec_result = run_sqls_parallel(query_pairs, db_paths=db_paths, num_cpus=16, meta_time_out=30.0)
	exec_result = sorted(exec_result, key=lambda x: x["sql_idx"])
	acc, num_queries = compute_acc(exec_result)

	print(
		"======================================    ACCURACY    ====================================="
	)
	print("Total Accuracy: {:.2f}%; Number of queries: {}".format(acc, num_queries))
	print(
		"==========================================================================================="
	)
	print(
		"==========================================================================================="
	)
	print("Finished evaluation")
