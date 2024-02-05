"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import json

from server import *

def get_variables(text):
    lines = text.split('\n')[1:]
    return '\n'.join(lines)

def replace_first_line(text, replace_str):
    lines = text.split('\n')
    lines[0] = replace_str
    return '\n'.join(lines)

def rephrase(files, replace_suffix="_v1", suffix="_new"):
    print("Rephrasing")
    for filename in tqdm(files):
        while True:
            new_filename = filename.replace(f'{replace_suffix}.txt', f'{suffix}.txt')
            with open(filename, 'r') as file:
                variables, prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")
            
            variables_str = replace_first_line(variables, new_filename)
            variables = get_variables(variables)
            
            request = get_rephrase_prompt('prompt_template/rephrase.txt', [variables.strip(), prompt.strip()])

            inputs = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request}
            ]

            try:
                response = chat('gpt-4', inputs)
                response = response.strip()
                response = response.replace("\n", "\\n")
                parsered_responses = json.loads(response)
                parsered_responses = parsered_responses["sentences"]
                break
            except:
                print("Cannot extract the rephrase sentences, now request again.")

        with open(new_filename, 'w') as file:
            file.write(f"{variables_str.strip()}")
            file.write("\n\n<commentblockmarker>###</commentblockmarker>\n\n")
            file.write(f"{parsered_responses}\n")
    return
