from tqdm import tqdm
import json

from server import *

def rephrase(files, version="_new"):
    print("Rephrasing")
    for filename in tqdm(files):
        while True:
            new_filename = filename.replace('.txt', version+'.txt')
            with open(filename, 'r') as file:
                variables, prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")
            request = get_prompt('prompt_template/rephrase.txt', [prompt.strip()])
            variables = variables.replace(filename, new_filename)
            inputs = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request}
            ]
            try:
                response = chat('gpt-4', inputs).strip()
                parsered_responses = json.loads(response)
                parsered_responses = parsered_responses["sentences"]
                break
            except:
                pass
        
        with open(new_filename, 'w') as file:
            file.write(f"{variables.strip()}")
            file.write("\n\n<commentblockmarker>###</commentblockmarker>\n\n")
            file.write(f"{parsered_responses}\n")
    return
