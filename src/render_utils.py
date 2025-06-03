import time

import numpy as np
import pandas as pd


# Function to convert DataFrame to markdown table
def df_to_markdown(df: pd.DataFrame) -> str:
	"""Convert a DataFrame to a markdown-formatted table."""
	markdown = "| " + " | ".join(df.columns) + " |\n"
	markdown += "|---" * len(df.columns) + "|\n"
	for index, row in df.iterrows():
		markdown += "| " + " | ".join(map(str, row)) + " |\n"
	return markdown


def generate_text_stream(full_text: str, delay: float = 0.1):
	"""Simulate a text stream by yielding words with a delay.
	Args:
		full_text (str): The complete text to simulate.
		delay (float): Delay in seconds between each word.
	"""
	for word in full_text.split():
		yield word + " "
		time.sleep(delay)  # Simulate a delay for each word


def generate_fake_table():
	return pd.DataFrame({"first column": [1, 2, 3, 4], "second column": [10, 20, 30, 40]})


def generate_fake_chart():
	return pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
