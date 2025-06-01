from typing import Any
import pandas as pd
import numpy as np
import random
import time

def execute_sql(sql: str) -> tuple:
    return generate_fake_text_stream(), generate_fake_table(), generate_fake_chart()


def generate_fake_text_stream():
	response = random.choice(
		[
			"Hello there! How can I assist you today?",
			"Hi, human! Is there anything I can help you with?",
			"Do you need help?",
		]
	)
	for word in response.split():
		yield word + " "
		time.sleep(0.1)  # Simulate a delay for each word


def generate_fake_table():
	return pd.DataFrame({"first column": [1, 2, 3, 4], "second column": [10, 20, 30, 40]})


def generate_fake_chart():
	return pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
