import time


def generate_text_stream(full_text: str, delay: float = 0.1):
    """Simulate a text stream by yielding words with a delay.
    Args:
            full_text (str): The complete text to simulate.
            delay (float): Delay in seconds between each word.
    """
    for word in full_text.split():
        yield word + " "
        time.sleep(delay)  # Simulate a delay for each word
