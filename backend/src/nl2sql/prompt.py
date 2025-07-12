def construct_full_prompt(system_prompt: str, database_schema: str, user_prompt: str):
    return f"""
{system_prompt}

{database_schema}

{user_prompt}
"""


def get_sql_generation_prompt_template():
    """Template for generating SQL queries for AWS Athena"""

    return """
Given the conversation context, create a syntactically correct SQL query for AWS Athena to help find the answer to the user's question.
If the user specifies a number of results, adjust the query accordingly.
Limit the results to a maximum of 10 if not specified.

<<MUST CRUCIAL INSTRUCTIONS>>
- By Default Always use LIMIT 10 if the user does not specify the number of records for every question, unless the user mentions.
- Only provide the SQL query inside the 'query' JSON key. Do not include any additional text or explanation.
- Validate how many records the user is asking, and use `LIMIT` and `OFFSET` to approximate results, especially for cases like percentiles.

**Important Notes for AWS Athena**:
- Always limit your answer to only Top 10 records if the user does not specify the number of records.
- Use Athena/Presto SQL syntax (supports window functions, CTEs, advanced aggregations).
- All table and column names should be properly quoted if they contain special characters.
- Use appropriate data types for comparisons and calculations.
- Be mindful of case sensitivity in string comparisons.

**Database Schema**:
{table_info}

**Available Tables and Columns**:
{schema_info}

**Example Scenarios**:
{example_scenarios}

**Question**: {user_question}

##Output Format:
Your response should be a JSON with only the SQL query in the 'query' key, as shown below:

    "query": "YOUR_SQL_QUERY_HERE"

Do not include any additional text, explanation, or commentary. Just the query in the correct format.

{format_instructions}
"""


def get_text_generation_prompt_template() -> str:
    """Placeholder template, change later"""

    return """
You are an expert data analyst. Given the following table and user question, generate a concise summary in markdown format.
Summary should describe the insights of the tabular data and answer the user question. Also explain the records to the user.
- The summary only explains the answers, not the questions. It will just explain the answer in form of answering the question.
Table:
{query_result}

User Question:
{user_question}

Summary:
"""
