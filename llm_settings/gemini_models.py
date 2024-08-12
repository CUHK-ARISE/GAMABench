from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
import google.generativeai as genai

from utils import *
from global_functions import *

genai.configure(api_key=google_api_key)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def gemini_chat(
    model,                      # gemini-1.0-pro, gemini-1.0-pro-001, gemini-1.0-pro-latest, gemini-1.0-pro-vision-latest, gemini-pro, gemini-pro-vision
    messages,                   # [{'role': 'user', 'parts': "In one sentence, explain how a computer works to a young child."}, {'role': "model', 'parts': "A computer is like a very smart machine that can understand and follow our instructions, help us with our work, and even play games with us!"}
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Chat response choices to generate for each input message.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    model = genai.GenerativeModel(model)
    response = model.generate_content(
        messages,
        generation_config=genai.types.GenerationConfig(
            # Only one candidate for now.
            candidate_count=n,
            # stop_sequences=['x'],
            max_output_tokens=max_tokens,
            temperature=temperature)
    )   
    
    if n == 1:
        return response.text