def construct_full_prompt(
    system_prompt: str,
    database_schema: str,
    user_prompt: str
):
    return f"""
{system_prompt}

{database_schema}

{user_prompt}
"""
