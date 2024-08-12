from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
from openai import OpenAI

from utils import *
from global_functions import *

openai = OpenAI(
    api_key=infradeep_api_key,
    base_url="https://api.deepinfra.com/v1/openai",
)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def deepinfra_chat(
    model,                      # meta-llama/Meta-Llama-3.1-70B-Instruct, mistralai/Mixtral-8x7B-Instruct-v0.1, Qwen/Qwen2-72B-Instruct
    prompt,                     # The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Completions to generate for each prompt.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    
    response = openai.chat.completions.create(
        model=model,
        messages=prompt,
        temperature=temperature,
        stream=False,
    )
    
    return extract_json_from_string(response.choices[0].message.content)
