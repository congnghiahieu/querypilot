from openai import OpenAI
import time

def ask_deepseek(api_key, prompt, temperature):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    trial = 5
    system_prompt = """You are an expert SQL developer specializing in SQLite. Your task is to convert natural language questions into valid SQLite SQL queries.

IMPORTANT RESTRICTIONS:
1. ONLY generate SELECT queries - no other query types allowed
2. DO NOT generate:
   - DDL queries (CREATE, ALTER, DROP)
   - DML queries (INSERT, UPDATE, DELETE)
   - DCL queries (GRANT, REVOKE)
3. Always wrap your SQL queries in ```sql ``` code blocks
4. If the user's request requires modifying data, respond with an error message explaining that only SELECT queries are supported
5. NEVER use SELECT * - always specify columns explicitly, even if the user doesn't ask for specific columns
   - This improves query performance
   - Makes the query more maintainable
   - Reduces network bandwidth usage
"""

    prompt = system_prompt + "\n\n" + prompt

    while trial > 0:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=temperature
            )
            print(response.choices[0].message.content)
            return dict(
                response=response.choices[0].message.content,
                **vars(response.usage)
            )
        except Exception as e:
            trial -= 1
            print(f"Repeat for the {trial} times for exception: {e}", end="\n")
            time.sleep(1)
            continue
