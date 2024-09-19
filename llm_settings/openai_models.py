from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
from openai import OpenAI

from utils import *
from global_functions import *

openai = OpenAI(api_key=openai_api_key)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def chat(
    model,                      # gpt-4, gpt-4-0314, gpt-4-32k, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-0301
    messages,                   # [{"role": "system"/"user"/"assistant", "content": "Hello!", "name": "example"}]
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Chat completion choices to generate for each input message.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )
    
    return response.choices[0].message.content

