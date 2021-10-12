# CSE334 Programming Languages - Homework

## Coding Game Project

- **Coding Game Project:** Platinum Rift - Episode 1
- **Coding Game Profile:** [VolkanKALIN](https://www.codingame.com/profile/212472b01398703ee3e5296d4940f1a57238424)

When I started to inspect the logic of the game, the first thing I struggle with was the interface of codingame system where you communicate with games via I/O tasks. Therefore, I took to set the ground for more manageable code right ahead, where I wrote a couple of functions and defined variables to keep the game state and other information about the gameboard.

### Helper Class and Functions

```py
class zone_state:
"Enumeration class that keeps possible 3 states of a zone: NEUTRAL, ENEMY, OWNED"

def is_my_zone(uid: int) -> bool:
"Takes an id and returns if this id belongs to me or not." 

def seperate_ally(pods: list[int]) -> (int, int):
"Takes pods input from the game and returns the number of enemy and ally pods in a tuple."

def get_zone_state(owner_id: int) -> zone_state:
"Takes owner id of the zone and returns an enum result of this state." 

def normalize(np_arr: ndarray, size: int) -> ndarray:
"Takes a numpy array and stretches its values between [0, size]."

def calc_occupation_percentage(continent_enum: (int, list[int])) -> float:
"Takes list of ids of zones and returns what percentages of these zones are owned by allies."

def update_occupied_zones():
"Updates the information of 'occupied_zones' set. See Variables topic for further information."

def get_adjZones(z_id: int, step: int) -> list[int]:
"Takes a zone id and a step and returns list of zone ids which can be reachable in 'step+1' step from 'z_id'"

def deploy_if_possible(z_id, amount=1, accept_less=False):
"Deploys `amount` number of ally pods to zone with id='z_id'. If there is not enough platinum to deploy then if `accept_less` is True then deploys pods as much number of as it can."

def been_there(z_id: int) -> bool:
"Returns if there was an ally in the zone with id='z_id' one step before."

def calc_attracts(isDeploy=False):
"Calculates attraction scores for zones to be attracted by pods around or to be deployed. See 'Calculating Attraction Points' topic."
```

### Variables

- **`plat_sources`**: Dict object that keeps platinum sources of each zone.
- **`zone_states`**: Dict object that keeps the state of each zone (Neutral, Enemy or Owned).
- **`zone_source`**: List object that keeps the information of `plat_sources` in a sorted manner.
- **`A`**: ndarray object keeps adjacency matrices of the gameboard that holds the information of reachable zones in `n` state. For example, `A[2][0][5]` gives the information if it can be reached from link `0` to link `5` in `2` steps.
- **`occupied_zones`**: Keeps the list of continents (sets of zone ids), which are completely occupied by any player.
- **`attract`, `deploy_attract`**: Attraction scores for zones to be attracted by pods around or to be deployed.
- **`zone_ally_count_last`**: Dict object that keeps the number of allies on every zone one step before.
- **`ally_factor`**: Fixed number of pods to be deployed at once.

#### Calculating Attraction Points

My early trials of the game logic were hardcoded and let it more complicated and hard to manage my code which was frustrating to maintain. Thus, after that moment, I felt ready to take some advice from experienced players, so, I read the external resources part on "WHAT WILL I LEARN?" topic of the game details. And there was an idea put forward by `grmel`, which is a zone evaluating a function, where each pod will decide where to go or be deployed in the next move is determined by the attraction points of possible zones to move, so I implemented the function `calc_attracts`. And according to his evaluation function attractiveness point is calculated with parameters such as `# of platinum sources`, `# of adjacent enemy platinum sources`, `number of platinum sources can be taken in 2 steps` etc.

First I calculated the attraction point as to how it is being recommended by `grmel`, but my pods started to stuck in local zones because I was only calculating these attraction points and I had hard times finding out the specific reason because there was no simple way to debug attraction points (for example showing each attraction point on each zone on each step). So searched for the source code of the game to create my environment for easier debugging but couldn't find anything. So I accepted the debugging method where you can print values each step, and after hours I found out 2 problems: platinum sources were overflooding the points and calculating points with only 2 steps further was not enough. Thus, I included 2 variables to arrange the effect of parameters on attraction points, which are WEIGHTS and RANGE_WEIGHTS. WEIGHT is keeping each parameter's coefficient of effect on attraction point. And RANGE_WEIGHTS are keeping coefficient of parameters according to how far the zone is. And then, I started to tweak those WEIGHT parameters slowly. But the problem is it was a very long process to change something little and waiting how affects the result. And I also needed to know the results for more than one game condition and opponents. I planned to provide parameters and save results automatically but my research ended up empty-handed. So I kept tuning parameters manually. I thought about using the API of the website and requesting games via script to the endpoint `codingame.com/services/TestSession/play` rather than using the interface, but unfortunately, I didn't have time for reverse-engineering the UI `¯\_(ツ)_/¯`.

##### What could I do?

If I had automated access to providing my code and getting results, I would start by using the easiest approaches: *genetic algorithm* or *bayesian optimization*.

### Struggles

Since the game expects you to answer in a determined time, I started to encounter related errors. So I tried to optimize my code as much as possible while also not trying to turn into more *spaghetti*. I realized there I was calling `get_adjZones` more than once with the same parameters so I just used memoization with `@lru_cache` decorator. Then I have started to take this error once in a blue moon.
