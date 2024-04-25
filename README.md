<div align= "center">
    <h1> 💰GAMA-Bench</h1>
</div>


<div align="center">
<img src="framework.png" width="750px">
</div>


## Leaderboard
<div align="center">
<img src="leaderboard.png" width="750px">
</div>

## Updates

[Apr 25, 2024] Update scoring scheme of Public Goods Game, Diner's Dilemma, and Sealed-Bid Auction to favor rational strategies (being self-interested); Update leaderboard;

## Execution Process

###  Create Utils File
Customize the model api, create a `utils.py` in this dictionary:
```py
openai_api_key = "<key>"    # Keep it empty string if not use
google_api_key = "<key>"    # Keep it empty string if not use
temperature = "<model temperature>"
delay_time = "<time break between each request>"
```

### Specify Test Cases
In `main.py`, specify the server parameters:
1. Import the following files:
    ```py
    from server import *
    from global_functions import *
    ```

2. Import the game:
    ```py
    from games.guessing_game import *
    ```

3. Create a simple game instance:
    ```py
    game = GuessingGame(player_num=10, min=0, max=100, ratio=2/3, ratio_str='2/3', version='v1', models='gpt-3.5-turbo', name_exp='test')
    ```
    - `player_num`: An integer refers to the number of players
    - `min`, `max`, `ratio`, `ratio_str`: Game parameters, different games may have different parameters
    - `version`: A string refers to the prompt version (default: `"v1"`)
    - `models`: A string or a list of models, the instruction of customizing models would be illustrated in the "Models Instruction" section (default: `"gpt-3.5-turbo"`)
    - `name_exp`: A string that specifies the name of all output files belonging to this game instance

4. Run a game instance for 20 rounds:
    ```py
    game.run(20)
    ```
    After a round is completed, a `JSON` saving file will be stored in the "save" directory sharing the same name with `name_exp`, all model requests and responses records will be stored in the "records" directory , and the visualized game results will be store in the "figures" directory 

5. Load a game:
    ```py
    game = load(filepath='save/test.json', object=GuessingGame)  # load the saved data 
    game = load(filepath='save/test.json', object=GuessingGame, newfile='test2')  # load and save as new file
    game.run(20)
    ```
    - `filepath`: A string refers to the path of the loading data
    - `object`: The game object that going to load
    - `namefile`: If it is `None`, the server will continue to update the current file, otherwise, the server will copy the file to a new file and update there

6. Show the visualized and statistical analysis of game instance:
    ```py
    game.show()
    ```



## Additional Operations

### Models Instruction
User can specify the models by passing a string or a list of models name when creating the game instance
- If the parameter is a `string`, which implies all players within the game instance are all referring to that model
    ```py
    game = GuessingGame(player_num=10, ..., models='gpt-3.5-turbo') # 10 players are all gpt-3.5-turbo
    ```

- If the parameter is a list, which implies that players are agented by the models based on their position in the list, but the number of players must match the length of the list
    ```py
    # player_0 to player_4 are gpt-3.5-turbo, player_5 to player_9 are gpt-4
    models = ["gpt-3.5-turbo" for _ in range(5)] + ["gpt-4" for _ in range(5)]
    game = GuessingGame(player_num=10, ..., models=models)
    ```
    ```py
    models = ['gpt-3.5-turbo' if i%2==0 else 'gpt-4' for i in range(10)]
    ```



#### Supported models
- OpenAI models family: models name start with `gpt-3.5-turbo` and `gpt-4`, user can specify the model version, such as `gpt-3.5-turbo-0125`
- Gemini models family: models name start with `gemini`, such as `gemini-pro-1.0`



#### Special players
We also support user to specify some special players with fixed strategies
1. `specified=<response_1>/<response_2>/.../<response_n>`: The player will response the specified answers repeatly
    ```py
    models = ["specified=0"] + ["gpt-3.5-turbo" for _ in range(9)]  # first player always responses 0 in every round
    ```
    ```py
    models = ["specified=0/100"] + ["gpt-3.5-turbo" for _ in range(9)]  # first player alternatively responses 0 and 100
    ```
    
2. `user`: User can participant the game with models by inserting `user` to the list by giving the responses in the terminal
    ```py
    models = ["user"] + ["gpt-3.5-turbo" for _ in range(9)]
    ```



### Rephrase prompts
Games usually consist of 3 prompts "description", "report" and "request" (bar game consists of "explicit" and "implicit" versions of report), user can rephrase the prompts using GPT-4 and the provided implementation
```py
from prompt_template.prompt_rephrase import *
game_file = 'guessing_game'
rephrase_files = ['description', 'report', 'request']
rephrase([f"prompt_template/{game_file}/{filename}_v1.txt" for filename in rephrase_files], replace_suffix="v1", suffix="v2")
```



## Result Analysis
For GuessingGame, BarGame, DivideDollar, and DinerDilemma, we developed a tool to visualize and integrate multiple runs into a figure, as shown in our paper. `analysis_main.ipynb` demonstrated the sample usage of our tool.

### Analyze Multiple Runs
In `analysis_main.ipynb`, specify the server and analysis parameters:
1. Import the following files:
    ```py
    from server import *
    from global_functions import *
    from analysis import *
    ```

2. Import the game:
    ```py
    from games.guessing_game import *
    ```

3. Create an Analysis instance:
    ```py
    plane = Analysis(GuessingGame)
    ```

4. Add the saved run with label:
    ```py
    plane.add('raw_results/guessing_game/guessing_game_v1_1.json', "T1")
    ```

5. Plot the graph:
    ```py
    plane.plot()
    ```
    - `index`: Figure index, for some games, we provided more than one figure for the analysis. For example, in DinerDilemma, we provide a graph demonstrating the percentage of players who choose "cheap" in each round; we also provide a graph demonstrating the averaged accumulated percentage of players who chose "cheap"; default `0`.
    - `title`: Title of the graph; default `None`
    - `xlabel`: Label of the x axis, default `"Round"`
    - `ylabel`: Label of the y axis, default `None`
    - `ylim`: Range of y axis, default `None`
    - `loc`: Location of the legend, default `"upper right"`
    - `format`: Figure format, default `"png"`
    - `savename`: Name of the figure, default `"merge"`



## 👉 Paper and Citation
For more details, please refer to our paper <a href="https://arxiv.org/abs/2403.11807">here</a>.

If you find our paper&tool interesting and useful, please feel free to give us a star and cite us through:
```
@article{huang2024how,
  author    = {Jen{-}tse Huang and
               Eric John Li and
               Man Ho Lam and
               Tian Liang and
               Wenxuan Wang and
               Youliang Yuan and
               Wenxiang Jiao and
               Xing Wang and
               Zhaopeng Tu and
               Michael R. Lyu},
  title     = {How Far Are We on the Decision-Making of LLMs? Evaluating LLMs' Gaming Ability in Multi-Agent Environments},
  journal   = {arXiv preprint arXiv:2403.11807},
  year      = {2024}
}
