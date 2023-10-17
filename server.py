from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import openai
import time
import os
import json
import random
from utils import *
openai.api_key = openai_api_key

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
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )
    
    if n == 1:
        return response['choices'][0]['message']['content']
    else:
        return [i['message']['content'] for i in response['choices']]


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion(
    model,                      # text-davinci-003, text-davinci-002, text-curie-001, text-babbage-001, text-ada-001
    prompt,                     # The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Completions to generate for each prompt.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )
    
    if n == 1:
        return response['choices'][0]['text']
    else:
        response = response['choices']
        response.sort(key=lambda x: x['index'])
        return [i['text'] for i in response['choices']]


class Player:
    def __init__(self, model, id, default_prompt, records=None, utility=None):
        self.model = model
        self.id = id
        self.prompt = default_prompt
        self.records = records if records else []
        self.utility = utility if utility else []
    
    
    def gpt_request(self, inputs):
        start_time = time.time()
        while time.time() - start_time < 10:
            if self.model == 'text-davinci-003':
                response = completion(self.model, inputs).strip()
                self.print_prompt(inputs, response)
                return response
            elif self.model in ['gpt-3.5-turbo', 'gpt-4']:
                response = chat(self.model, inputs).strip()
                # response = '{"option": "yes"}' if random.randint(0,2) < 1 else '{"option": "no"}'
                # response = '{"option": "expensive"}' if random.randint(0,2) < 1 else '{"option": "cheap"}'
                # response = f'''{{"option": "{random.randint(0,100)}"}}'''
                self.print_prompt(self.id, inputs, response)
                return response
            else:
                raise ValueError("The model is not supported or does not exist.")
    
    
    def print_prompt(self, id, inputs, response):
        os.makedirs("records", exist_ok=True)
        with open(f"records/{id}.txt", 'a') as f:
            f.write(f"{inputs}\n----\n")
            f.write(f"{response}\n====\n")
        return


class GameServer:
    def __init__(self, player_num, rounds, description_file, description_list):
        self.n = player_num
        self.rounds = rounds
        description_prompt = self.get_prompt(description_file, description_list)
        default_prompt = [
            {"role": "system", "content": description_prompt}
        ]
        self.players = [Player('gpt-3.5-turbo', f"player_{i}", default_prompt) for i in range(player_num)]
        self.round_records = []


    def get_prompt(self, filename, inputs):
        with open(filename, 'r') as file:
            generated_prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")[1].strip()
        for index, item in enumerate(inputs):
            key = f"!<INPUT {index}>!"
            generated_prompt = generated_prompt.replace(key, str(item))
        return generated_prompt
    
    
    def save(self, savename, game_info={}):
        savefile = f'save/{savename}'
        save_data = {
            "round_records": self.round_records,
            "player_data": [],
            "n": self.n,
            "rounds": self.rounds
        }
        save_data = {**save_data, **game_info}
        
        for player in self.players:
            player_info = {
                "model": player.model,
                "id": player.id,
                "prompt": player.prompt,
                "records": player.records,
                "utility": player.utility
            }
            save_data["player_data"].append(player_info)
        os.makedirs("save", exist_ok=True)
        with open(savefile, 'w') as json_file:
            json.dump(save_data, json_file, indent=2)
        return savefile
    
    
    def load(self, filename):
        with open(filename, 'r') as json_file:
            loaded = json.load(json_file)
            
        # Load game setting
        self.round_records = loaded["round_records"]
        for index, loaded_player in enumerate(loaded["player_data"]):
            self.players[index] = Player(loaded_player["model"], loaded_player["id"],
                            loaded_player["prompt"], loaded_player["records"], loaded_player["utility"])
            
        return loaded
    
    