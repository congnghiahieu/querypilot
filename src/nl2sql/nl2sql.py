import os
from src.nl2sql.llm.chatgpt import ask_deepseek
from src.nl2sql.utils.post_process import process_duplication

db_id = "financial"

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

def convert_nl2sql(question: str, data, prompt) -> str:
    data_item = dict()
    data_item["db_id"] = db_id
    data_item["question"] = question
    data_item["question_toks"] = ""
    
    max_sequence_len = 65000
    max_ans_len = 4000

    tests = [
        {
            "db_id": db_id,
            "question": question,
            "question_toks": "",
            "query": ""
        }
    ]
    pre_processes_question = data.get_question_json(tests)
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
