import json.decoder
import os
from dotenv import load_dotenv

from openai import OpenAI
from src.nl2sql.dail_sql.utils.enums import LLM
import time

# Load environment variables from .env file
load_dotenv()

def ask_deepseek(prompt, api_key=None, temperature=0.0):
    if api_key is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    trial = 3

    while trial > 0:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            trial -= 1
            print(f"Repeat for the {trial} times for exception: {e}", end="\n")
            time.sleep(1)
            continue

def ask_deepseek_sql(prompt, db_name, api_key=None, temperature=0.0):
    if api_key is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    trial = 3
    system_prompt = """You are an expert SQL developer specializing in Athena. Your task is to convert natural language questions into valid Athena SQL queries.
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

    prompt = system_prompt + "\n\n" + prompt + "\n\n" + f"Catalog of the database: {db_name}"

    print(f"Prompt for ask_deepseek_sql: {prompt}")

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

# Global client instance
client = None

def init_chatgpt(OPENAI_API_KEY, OPENAI_GROUP_ID, model):
    global client
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        organization=OPENAI_GROUP_ID,  # If not used, can be omitted
        base_url="https://api.yescale.io/v1"
    )


def ask_completion(model, batch, temperature):
    response = client.completions.create(
        model=model,
        prompt=batch,
        temperature=temperature,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=[";"]
    )
    response_clean = [choice.text for choice in response.choices]
    return dict(
        response=response_clean,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens
    )


def ask_chat(model, messages: list, temperature, n):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=200,
        n=n
    )
    response_clean = [choice.message.content for choice in response.choices]
    if n == 1:
        response_clean = response_clean[0]
    return dict(
        response=response_clean,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens
    )


def ask_llm(model: str, batch: list, temperature: float, n:int):
    max_retries = 3
    n_repeat = 0
    while n_repeat < max_retries:
        try:
            if model in LLM.TASK_COMPLETIONS:
                # TODO: self-consistency in this mode
                assert n == 1
                response = ask_completion(model, batch, temperature)
            elif model in LLM.TASK_CHAT:
                # batch size must be 1
                assert len(batch) == 1, "batch must be 1 in this mode"
                messages = [{"role": "user", "content": batch[0]}]
                response = ask_chat(model, messages, temperature, n)
                response['response'] = [response['response']]
            break
        except json.decoder.JSONDecodeError:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for JSONDecodeError", end="\n")
            time.sleep(1)
            continue
        except Exception as e:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for exception: {e}", end="\n")
            time.sleep(1)
            continue

    return response

