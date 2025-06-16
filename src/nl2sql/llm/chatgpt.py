from openai import OpenAI
import time

def ask_deepseek(api_key, prompt, temperature):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    trial = 5
    system_prompt = "-- You are an expert SQL developer specializing in SQLite. Your task is to convert natural language questions into valid SQLite SQL queries. Always wrap your SQL queries in ```sql ``` code blocks."
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
