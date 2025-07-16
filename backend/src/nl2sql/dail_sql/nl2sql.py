import sys
print(">>> Import done 1")
from src.nl2sql.dail_sql.utils.linking_utils.application import (
    mask_question_with_schema_linking
)
print(">>> Import done 2")
from src.nl2sql.dail_sql.utils.utils import sql2skeleton, get_sql_for_database
print(">>> Import done 3")
from src.nl2sql.dail_sql.prompt.prompt_builder import prompt_factory
print(">>> Import done 4")
from src.nl2sql.dail_sql.llm.chatgpt import ask_deepseek_sql, ask_deepseek
print(">>> Import done 5")
from src.nl2sql.dail_sql.utils.enums import REPR_TYPE, EXAMPLE_TYPE, SELECTOR_TYPE
print(">>> All imports OK")
from src.nl2sql.dail_sql.prompt.PromptReprTemplate import SQLPrompt
from src.core.settings import PROJECT_ROOT

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

def auto_link_and_mask(question, tables, columns):
    """
    Gọi LLM để masking: <mask> cho entity, <unk> cho số.
    Đồng thời tự build sc_link và cv_link dựa trên vị trí token đã mask.
    """
    # Ghép schema thành string cho prompt
    schema_desc = "Tables:\n- " + "\n- ".join(tables) + "\nColumns:\n- " + "\n- ".join(columns)

    prompt = f"""
        Below is a user question and the database schema.

        {schema_desc}

        Task:
        - Replace any word that matches a table or column name with <mask>.
        - Replace any number or numeric token with <unk>.
        - Keep other words unchanged.
        - Output only the masked question.

        Question: {question}
        Masked:
        """.strip()

    # Gọi LLM
    #response = ask_llm(LLM_MODEL, [prompt], temperature=0.0, n=1)["response"][0].strip()
    response = ask_deepseek(prompt)
    masked_question = response
    print("masked_question", masked_question)

    # Tính toán link
    tokens = question.split()
    masked_tokens = masked_question.split()

    sc_link = {"q_tab_match": {}, "q_col_match": {}}
    cv_link = {"num_date_match": [], "cell_match": {}}

    for idx, (orig, masked) in enumerate(zip(tokens, masked_tokens)):
        if masked == "<mask>":
            # Nếu LLM mask thì check trong tables hay columns
            lower = orig.lower().strip("?.,")
            if any(lower == t.lower() for t in tables):
                sc_link["q_tab_match"][f"{idx},0"] = "TEM"
            elif any(lower == c.lower() for c in columns):
                sc_link["q_col_match"][f"{idx},0"] = "CEM"
            else:
                # fallback: gán table
                sc_link["q_tab_match"][f"{idx},0"] = "TEM"
        elif masked == "<unk>":
            cv_link["num_date_match"].append(f"{idx},0")

    return masked_question, sc_link, cv_link


import json

class BankingDataLoader:
    def __init__(self, json_file="data/banking_data.json"):
        # Construct the full path relative to project root
        from src.core.settings import PROJECT_ROOT
        full_path = PROJECT_ROOT / "dataset" / json_file
        with open(full_path, "r") as f:
            self._train_json = json.load(f)

    def get_train_json(self):
        return self._train_json

    def get_train_questions(self):
        return [item["question"] for item in self._train_json]
data = BankingDataLoader("converted.json")

def get_tables_input(prompt_obj, schema):
    """
    Giúp xác định nên đưa schema dưới dạng DDL (cho SQLPrompt)
    hay list dict (cho TextPrompt/NumberSignPrompt/...)
    """
    if isinstance(prompt_obj, SQLPrompt) or hasattr(prompt_obj, "render_schema"):
        return schema   # cho render_schema() chạy
    else:
        # Convert Spider schema -> list Table objects
        table_names = schema["table_names_original"]
        columns = schema["column_names_original"]

        table_columns = {}
        for tid, col in columns:
            table_columns.setdefault(tid, []).append(col)

        tables_list = []
        for tid, tname in enumerate(table_names):
            tables_list.append(
                type("Table", (), {
                    "name": tname,
                    "schema": table_columns.get(tid, [])
                })()
            )
        return tables_list

def nl2sql(question, context, db_id):
    try:
        # Construct database path relative to project root
        path_db = PROJECT_ROOT / "dataset" / f"{db_id}.sqlite"
        
        print(f"question = {question}\ndb_id = {db_id}")
        print(f"Database path: {path_db}")
        schema = get_sql_for_database(path_db)
        # Sau khi có schema
        table_names = schema["table_names_original"]
        columns = schema["column_names_original"]

        # Group columns theo table_id
        table_columns = {}
        for tid, col in columns:
            table_columns.setdefault(tid, []).append(col)


        print("Schema:", schema)
        print("after get id question")
        tables = [t.lower() for t in table_names]
        columns = [col_name.lower() for _, col_name in columns]

        # === DSL ===
        masked_question, sc_link, cv_link = auto_link_and_mask(question, tables, columns)

        print("before mask question")
        masked_question_final = mask_question_with_schema_linking([
            {
                "question_for_copying": question.split(),
                "sc_link": sc_link,
                "cv_link": cv_link
            }
        ], "<mask>", "<unk>")[0]

        print(f"✅ Masked question: {masked_question_final}")
  
        QMS_PromptClass = prompt_factory(
            repr_type=REPR_TYPE.CODE_REPRESENTATION,
            k_shot=2,
            example_format=EXAMPLE_TYPE.QA,
            selector_type=SELECTOR_TYPE.EUC_DISTANCE_QUESTION_MASK
        )
        qms_prompt = QMS_PromptClass(data)
        print("prompt_factory done")

        target_json = {
            "question": masked_question_final,
            "question_for_copying": masked_question_final.split(),
            "sc_link": sc_link,
            "cv_link": cv_link
        }
        print("✅ target_json:", target_json)
        print("✅ question_for_copying:", target_json["question_for_copying"])
        qms_examples = qms_prompt.get_examples(target_json, num_example=2)
        print("QMS examples:", qms_examples)
        tables_input = get_tables_input(qms_prompt, schema)
        prompt1 = qms_prompt.format_question({
            "question": masked_question_final,
            "tables": schema,
            "db_id": db_id,
            "path_db": path_db
        })
        for ex in qms_examples:
            prompt1 += "\n\n" + qms_prompt.format_example_only(ex) + "\nSELECT " + ex["query"]

        prompt1 += "\n\n-- Chỉ trả về duy nhất câu SQL."

        print("Prompt 1:", prompt1)

        #pre_sql = ask_llm(LLM_MODEL, [prompt1], temperature=0.0, n=1)["response"][0]
        pre_sql = ask_deepseek_sql(prompt1)['response']
        clean_sql = [l.strip() for l in pre_sql.splitlines() if l.strip().upper().startswith("SELECT")][0]

        # === Skeleton ===
        skeleton_value = sql2skeleton(clean_sql, schema)
        print("Skeleton:", skeleton_value)

        # === QSS ===
        QSS_PromptClass = prompt_factory(
            repr_type=REPR_TYPE.CODE_REPRESENTATION,
            k_shot=1,
            example_format=EXAMPLE_TYPE.QA,
            selector_type=SELECTOR_TYPE.EUC_DISTANCE_MASK_PRE_SKELETON_SIMILARITY_THRESHOLD
        )
        qss_prompt = QSS_PromptClass(data)
        qss_target = target_json.copy()
        qss_target.update({"pre_skeleton": skeleton_value})
        qss_examples = qss_prompt.get_examples(qss_target, num_example=1)

        print ("Question gốc: ", question)
        prompt2 = qss_prompt.format_question({
            "question": question,
            "tables": schema,
            "db_id": db_id,
            "path_db": path_db
        })
        for ex in qms_examples + qss_examples:
            prompt2 += "\n\n" + qss_prompt.format_example_only(ex) + "\nSELECT " + ex["query"]
        prompt2 += "\n\n-- Chỉ trả về duy nhất câu SQL."

        print("Prompt 2:", prompt2)

        if context:
            prompt2 += "\n\n-- Dựa trên các thông tin trong context, hãy tạo câu SQL phù hợp."
            prompt2 += "\n\n-- Context: " + context

        #final_sql = ask_llm(LLM_MODEL, [prompt2], temperature=0.0, n=1)["response"][0]
        final_sql = ask_deepseek_sql(prompt2)['response']
        print("✅ Final SQL:", final_sql)
        
        # Clean and return the SQL query
        clean_final_sql = clean_sql_query(final_sql)
        return clean_final_sql
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return None
