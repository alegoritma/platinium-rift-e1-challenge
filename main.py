import sys
import math
import numpy as np
import random
from functools import lru_cache


plat_sources = {}
zone_source = []

"""
Weights for calculating attraction points. 
See variables 'Calculating Attraction Points' topic in README.md """
RANGE_WEIGHTS = np.array([25e-2, 1e-2, 1e-5, 1e-5, 1e-5, 1e-5, 1e-5])/2
DEPLOY_RANGE_WEIGHTS = np.array([5e-1, 1e-1, 1e-3])*1e-1
WEIGHTS = np.array([
    0.2, 0.8, 0,
    1, 0.75, 0,
    0.01,
    1
])
DEPLOY_WEIGHTS = np.array([
    0.5, 0.5, 0,
    1.2, 1.0, 1.2,
    0.1,
    0.7
])
NEW_STEP_WEIGHT = -0.1
RANGE_OF_VISION = len(RANGE_WEIGHTS)


class zone_state:
    """
    Enumeration class that keeps 
    possible 3 state of a zone"""
    NEUTRAL = 0
    ENEMY = -1
    OWNED = 1


player_count, my_id, zone_count, link_count = [int(i) for i in input().split()]

A = np.zeros((RANGE_OF_VISION, zone_count, zone_count), np.int16)
_attract = np.zeros((zone_count,), np.float16)
_deploy_attract = np.zeros((zone_count,), np.float16)
zone_states = np.zeros((zone_count,), np.int8)
zone_enemy_count = np.zeros((zone_count,), np.uint8)
zone_ally_count = np.zeros((zone_count,), np.uint8)
attract = np.zeros((zone_count, ))
deploy_attract = np.zeros((zone_count, ))


"Takes an id and returns if this id belongs to me or not."
def is_my_zone(uid): return uid == my_id


def normalize(np_arr, size):
    """
    Takes a numpy array and 
    stretches its values between [0, size]."""
    return ((np_arr-np.min(np_arr))/(np.max(np_arr)-np.min(np_arr))*size).astype(np.uint8)


occupied_zones = set()
continents = []
continents_stack = []


def calc_occupation_percentage(continent_enum):
    """
    Takes list of ids of zones and returns what 
    percentages of these zones are owned by allies."""
    i, zone_ids_set = continent_enum
    zone_ids = list(zone_ids_set)
    n_occupied_zones = sum(zone_states[zone_ids] == zone_state.OWNED)
    return n_occupied_zones/len(zone_ids)


def update_occupied_zones():
    """Updates the information of 'occupied_zones' set. 
    See "Variables" topic in README.md for further information."""

    if len(continents) == 0 and len(continents_stack) != 0:
        continents.extend(continents_stack)
        for cont in continents_stack:
            occupied_zones.difference_update(cont)

    for i, continent in enumerate(continents):
        occupied_ally = sum(
            zone_states[list(continent)] == zone_state.OWNED) == len(continent)
        occupied_enemy = sum(
            zone_states[list(continent)] == zone_state.ENEMY) == len(continent)
        if occupied_ally or occupied_enemy:
            occupied_zones.update(continent)
            del continents[i]


@lru_cache(maxsize=None)
def get_adjZones(z_id, step=0):
    """
    Takes a zone id (z_id) and a step, 
    and returns list of zone ids which 
    can be reachable in 'step+1' step from 'z_id'
    """
    adjZones = np.nonzero(A[step, z_id])[0]
    return adjZones


def deploy_if_possible(z_id, amount=1, accept_less=False):
    """
    Deploys `amount` number of ally pods to zone with id='z_id'. 
    If there is not enough platinium to deploy then 
    if `accept_less` is True then deploys 
    number of pods as much as it can."""

    global deployable_count
    if (not accept_less and amount > deployable_count):
        return
    req_ally = min(amount, deployable_count)
    deploy_commands.append((req_ally, z_id))
    deployable_count -= req_ally


def been_there(z_id):
    "Returns if there was an ally in zone with id='z_id' one step before."
    return (zone_ally_count_last[z_id] != 0)


def calc_attracts(isDeploy=False):
    """
    Calculates attraction scores for zones to be 
    attracted by pods around or to be deployed.
    See "Calculating Attraction Points" topic in README.md.
    """
    __attract = deploy_attract if isDeploy else attract
    __W = DEPLOY_WEIGHTS if isDeploy else WEIGHTS
    __attract[:] = 0.1
    __RANGE_WEIGHTS = DEPLOY_RANGE_WEIGHTS if isDeploy else RANGE_WEIGHTS
    for z_id in range(zone_count):
        if zone_states[z_id] != zone_state.OWNED:
            __attract[z_id] += _attract[z_id]
        calceds = [z_id]
        for j, weight in enumerate(__RANGE_WEIGHTS):
            adjZones = get_adjZones(z_id, j)
            adjZones = adjZones[~np.isin(adjZones, calceds)]

            calceds.extend(adjZones)

            nOfAdjZones = len(adjZones)
            if nOfAdjZones == 0:
                continue

            adjZoneStates = zone_states[adjZones]

            neutralAdjZones = adjZones[adjZoneStates == zone_state.NEUTRAL]
            enemyAdjZones = adjZones[adjZoneStates == zone_state.ENEMY]
            allyAdjZones = adjZones[adjZoneStates == zone_state.OWNED]

            adjNeutralPlatSrc = sum(_attract[neutralAdjZones])  # *__W[3]
            adjEnemyPlatSrc = sum(_attract[enemyAdjZones])  # *__W[4]
            adjAllyPlatSrc = sum(_attract[allyAdjZones])*__W[5]

            nOfAdjNeutralZone = neutralAdjZones.shape[0]
            nOfAdjEnemyZone = enemyAdjZones.shape[0]
            nOfAdjAllyZone = allyAdjZones.shape[0]

            __attract[z_id] += weight*(
                __W[0]*(adjNeutralPlatSrc)
                + __W[1]*(adjEnemyPlatSrc)
                + __W[2]*(adjAllyPlatSrc)
            )/nOfAdjZones


def seperate_ally(pods):
    """Takes pods input from the game and returns 
    number of enemy and ally pods in a tuple."""

    count = {
        True: 0,  # Ally pods
        False: 0  # Enemy Pods
    }
    for uid, pod_count in enumerate(pods):
        count[my_id == uid] += pod_count
    # returns (ally_count, enemy_count)
    return count[True], count[False]


def get_zone_state(owner_id, *pods):
    """Takes owner id of the zone and 
    returns a enum result of this state."""

    if owner_id == -1:
        return zone_state.NEUTRAL
    if is_my_zone(owner_id):
        return zone_state.OWNED
    return zone_state.ENEMY


for i in range(zone_count):
    zone_id, platinum_source = [int(j) for j in input().split()]
    plat_sources[zone_id] = platinum_source
    _attract[zone_id] = 1e-6 + platinum_source
    zone_states[zone_id] = zone_state.NEUTRAL


zone_source = sorted(plat_sources.items(), key=lambda x: x[1], reverse=True)

for i in range(link_count):
    zone_1, zone_2 = [int(j) for j in input().split()]
    A[0, zone_1, zone_2] = 1
    A[0, zone_2, zone_1] = 1

for i in range(1, RANGE_OF_VISION):
    A[i] = np.matmul(A[0], A[i-1])


"""Create Adjacency matrices"""
ADJ_MAT = A[0] != 0
all_nodes = set([_ for _ in range(zone_count)])


while len(all_nodes) > 0:
    start_node = all_nodes.pop()
    group = set([start_node])
    queue = set(np.nonzero(ADJ_MAT[start_node])[0])

    group.update(queue)
    all_nodes.difference_update(queue)
    queue = set(queue)
    ADJ_MAT[:, start_node] = False

    while len(queue) > 0:
        node = queue.pop()
        new_neighbours = set(np.nonzero(ADJ_MAT[node])[0])
        all_nodes.difference_update(new_neighbours)
        queue.update(new_neighbours)
        group.update(new_neighbours)
        ADJ_MAT[node, :] = False
    continents.append(group)


ally_factor = (player_count//2+1)-1

zone_ally_count_last = zone_ally_count.copy()


# game loop
while True:
    platinum = int(input())
    deployable_count = platinum//20

    "Re-initialize step-based variables."
    zone_ally_count_last[:] = zone_ally_count
    zone_enemy_count[:] = 0
    zone_ally_count[:] = 0

    for i in range(zone_count):
        """
        Update number of ally and enemy counts in each zone (zone_ally_count, zone_enemy_count).
        Update zone_states for each zone. (Enemy, Neutral or Owned)
        """
        z_id, owner_id, *pods = [int(j) for j in input().split()]
        zone_states[z_id] = get_zone_state(owner_id, *pods)

        ally_pods, enemy_pods = seperate_ally(pods)
        zone_ally_count[z_id] = ally_pods
        zone_enemy_count[z_id] = enemy_pods

    "Initilize variables for what to print end of step."
    deploy_commands = []
    move_commands = {}

    """
    Update occupied zones to eleminate unnecessary deployments and calculations 
    with continents that completely occupied by one player already
    """
    update_occupied_zones()

    """
    Calculate attraction points for 
    """
    calc_attracts()  # TODO: filter occupied zones
    calc_attracts(isDeploy=True)

    """
    Sort zone_ids by attraction points for deployment and 
    add instructions to deploy_commands list. 
    """
    _zone_source = sorted(
        zone_source, key=lambda x: deploy_attract[x[0]], reverse=True)
    for z_id, source_amount in _zone_source:
        if z_id in occupied_zones:
            continue
        if zone_states[z_id] == zone_state.ENEMY:
            continue
        if deployable_count <= 0:
            break

        n = min(ally_factor, deployable_count)
        deploy_commands.append((n, z_id))
        deployable_count -= n

    """
    Iterate all allies (with zone id) and decide where to move.
    """
    ally_zones = np.nonzero(zone_ally_count)[0]
    for z_id in ally_zones:

        "Continue if continent is allready occupied completely."
        if z_id in occupied_zones:
            continue

        move_commands[z_id] = {}
        ally_count = zone_ally_count[z_id]
        adjZones = get_adjZones(z_id)

        """
        Prioritize zones taken by enemy for the allies. 
        If ally has no opportinity to win then treat back"""
        enemy_zones_sorted = adjZones[np.argsort(
            zone_enemy_count[adjZones])][::-1]

        for z_enemy in enemy_zones_sorted:
            enemy_count = zone_enemy_count[z_enemy]
            if enemy_count != 0 and enemy_count < ally_count:
                if plat_sources[z_enemy] > plat_sources[z_id]:
                    move_commands[z_id][z_enemy] = ally_count
                ally_count -= enemy_count
                continue
            elif enemy_count == ally_count:
                deploy_if_possible(z_id, enemy_count, accept_less=True)
                if plat_sources[z_enemy] > plat_sources[z_id]:
                    move_commands[z_id][z_enemy] = ally_count
                ally_count -= enemy_count

        while ally_count > 0:
            z_best_attr = adjZones[np.argmax(attract[adjZones])]
            if z_best_attr not in move_commands[z_id]:
                move_commands[z_id][z_best_attr] = 0

            move_commands[z_id][z_best_attr] += 1
            ally_count -= 1
            attract[z_best_attr] += NEW_STEP_WEIGHT

    "Build commands for movement and deployment. And then print."
    deploy_commands = [f"{n} {z_id}" for n, z_id in deploy_commands if n > 0]
    move_cmd_str = ""
    for src_zone, dest_zones in move_commands.items():
        for dest_zone, count in dest_zones.items():
            move_cmd_str += f"{count} {src_zone} {dest_zone} "

    move_cmd_str = move_cmd_str if move_cmd_str else 'WAIT'
    deploy_commands = 'WAIT' if len(
        deploy_commands) == 0 else ' '.join(deploy_commands)

    print(move_cmd_str)
    print(deploy_commands)
