from src.nl2sql.data_preprocess import schema_linking_producer
from src.nl2sql.utils.enums import REPR_TYPE, EXAMPLE_TYPE, SELECTOR_TYPE, LLM
import json
import os
import sqlite3
from src.nl2sql.utils.utils import get_tables_from_db
from src.nl2sql.prompt.prompt_builder import prompt_factory
from src.nl2sql.utils.data_builder import load_data
from src.nl2sql.llm.chatgpt import ask_deepseek
from src.nl2sql.utils.post_process import process_duplication



bull_dir = "./dataset/bull"
bull_table = "BULL-en/tables.json"
bull_db = "database_en"
PATH_DATA = "dataset/"

db_id = "ccks_fund"

def clean_sql_query(sql_str):
    """
    Clean SQL query by extracting only the SQL statement from markdown formatted text.
    
    Args:
        sql_str (str): Raw SQL string that may contain markdown formatting and explanations
        
    Returns:
        str: Clean SQL query
    """
    # If the query contains markdown code block
    if "```sql" in sql_str:
        # Extract content between ```sql and ```
        start = sql_str.find("```sql") + 6
        end = sql_str.find("```", start)
        if end != -1:
            sql_str = sql_str[start:end]
    
    # Remove any leading/trailing whitespace and newlines
    sql_str = sql_str.strip()
    
    return sql_str

def get_tables(db_id):
    path_db = os.path.join(bull_dir, bull_db, db_id, db_id + ".sqlite")
    tables = get_tables_from_db(path_db)
    return tables

def get_databases(table_json):
    databases = dict()
    with open(table_json) as f:
        tables = json.load(f)
        for tj in tables:
            db_id = tj["db_id"]
            databases[db_id] = get_tables(db_id)
    return databases

def convert_nl2sql(question: str) -> str:
    data_item = dict()
    data_item["db_id"] = db_id
    data_item["question"] = question
    data_item["question_toks"] = ""
    print("Start schema linking")
    #preprocessed = schema_linking_producer(data_item, bull_table, bull_db, bull_dir)
    
    k_shot = 9
    max_sequence_len = 65000
    max_ans_len = 4000
    prompt_repr = REPR_TYPE.CODE_REPRESENTATION
    example_type = EXAMPLE_TYPE.QA
    selector_type = SELECTOR_TYPE.EUC_DISTANCE_QUESTION_MASK

    data = load_data("bull", PATH_DATA, None)
    databases = data.get_databases()
    prompt = prompt_factory(prompt_repr, k_shot, example_type, selector_type)(data=data, tokenizer="None")
    print("End prompt factory")

    tests = [
        {
            "db_id": db_id,
            "question": question,
            "question_toks": "",
            "query": ""
        }
    ]
    print("Start pre-processing question")
    pre_processes_question = data.get_question_json(tests)
    print("Start formatting question")
    question_format = prompt.format(
        target=pre_processes_question[0],
        max_seq_len=max_sequence_len,
        max_ans_len=max_ans_len,
        scope_factor=100,
        cross_domain=False
    )

    api_key = os.getenv("DEEPSEEK_API_KEY")
    res = ask_deepseek(api_key, question_format['prompt'], 0.0)
    sql = res["response"]
    sql = " ".join(sql.replace("\n", " ").split())
    sql = process_duplication(sql)
    sql = clean_sql_query(sql)
    print(sql)
    return sql
