from src.nl2sql.dail_sql.utils.post_process import process_duplication
from src.nl2sql.llm import ask_deepseek

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


def convert_nl2sql(question: str, data, prompt, task_tracker=None) -> str:
    """
    Convert natural language to SQL query with optional task tracking.

    Args:
        question (str): Natural language query
        data: Data object for processing
        prompt: Prompt template
        task_tracker: Optional TaskTracker instance for performance monitoring

    Returns:
        str: Generated SQL query
    """
    data_item = dict()
    data_item["db_id"] = db_id
    data_item["question"] = question
    data_item["question_toks"] = ""

    max_sequence_len = 65000
    max_ans_len = 4000

    tests = [{"db_id": db_id, "question": question, "question_toks": "", "query": ""}]
    pre_processes_question = data.get_question_json(tests)
    question_format = prompt.format(
        target=pre_processes_question[0],
        max_seq_len=max_sequence_len,
        max_ans_len=max_ans_len,
        scope_factor=100,
        cross_domain=False,
    )

    res = ask_deepseek(question_format["prompt"], 0.0)
    sql = res["response"]
    sql = " ".join(sql.replace("\n", " ").split())
    sql = process_duplication(sql)
    sql = clean_sql_query(sql)

    # Record SQL generation completion if task tracker is provided
    if task_tracker:
        task_tracker.record_sql_generation(sql)

    print(sql)
    return sql
