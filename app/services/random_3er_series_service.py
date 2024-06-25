import math
from app.models import Championship_Player_Model, Tische_Model, Series_Model

def create_3er_random_rounds(random_series_amount, current_championship_ID, current_championship_acronym):
    playerIDsArray = get_player_ids_for_championship(current_championship_ID)
    player_ids_groups_with_blinds = split_players_into_groups(playerIDsArray)
    success = True
    
    for i in range(int(random_series_amount)):
        player_ids_groups_with_blinds = rotate_groups(player_ids_groups_with_blinds)
        print(player_ids_groups_with_blinds)
        player_groups_to_rounds = player_ids_groups_with_blinds
        single_4er_serie_tische_array = generate_4er_serie_tische_array(player_groups_to_rounds)
        player_array_no_blinds = flatten_players_array(single_serie_tische_array=single_4er_serie_tische_array)
        print(player_array_no_blinds)
        single_3er_serie_tische_array=create_3er_tische_array(player_array_no_blinds=player_array_no_blinds)

        
        championship_serien = Series_Model.select_series(championship_id=current_championship_ID)
        length_existing_serien = len(championship_serien)
        series_name=current_championship_acronym+'_S#'+str(length_existing_serien+1)
        series = Series_Model().insert_series(current_championship_ID, series_name=series_name, 
                                              is_random=True, seek_4er_tische=False)
        if not bau_randomische_tische(i, single_serie_tische_array=single_3er_serie_tische_array, 
                                      series=series):
            # If creation of tisches fails, handle the error here
            print(f"Error creating randomische tische for series {series_name}")
            success = False
    
    return success

      
def generate_4er_serie_tische_array(groups):
    # The zip function combines elements from each group with the same index
    return [list(group) for group in zip(*groups)]
  

def bau_randomische_tische(series_index, single_serie_tische_array, series):
    remainder = series_index % 4

    for tisch_index, tisch in enumerate(single_serie_tische_array):
        rotated_tisch = tisch[-remainder:] + tisch[:-remainder]

        tisch_name = series.series_name + "_T#" + str(tisch_index + 1)
        if len(rotated_tisch)==3:
              
            # Insert the tisch into the database
            tisch_inserted = Tische_Model().insert_tisch(
                series_id=series.SeriesID, tisch_name=tisch_name,
                pos_a=rotated_tisch[0], pos_b=rotated_tisch[1],
                pos_c=rotated_tisch[2], pos_d=-1
            )
            
            if not tisch_inserted:
                return False  # Return False if insertion fails
        if len(rotated_tisch)==4:
              
            # Insert the tisch into the database
            tisch_inserted = Tische_Model().insert_tisch(
                series_id=series.SeriesID, tisch_name=tisch_name,
                pos_a=rotated_tisch[0], pos_b=rotated_tisch[1],
                pos_c=rotated_tisch[2], pos_d=rotated_tisch[3]
            )
            
            if not tisch_inserted:
                return False  # Return False if insertion fails

    return True  # Return True if all insertions are successful


def get_player_ids_for_championship(championship_id):

    # Query players registered for the given championship
    registered_players_from_selection = Championship_Player_Model.select_championship_players_by_championship_id(championship_id=championship_id)

    # Extract PlayerIDs of registered players for the championship
    registered_player_ids = [player.PlayerID for player in registered_players_from_selection]
    return registered_player_ids

def rotate_groups(groups):
      # Apply the rotation logic to each group with its index
    return [rotate_group_with_fixed_blind(group, index) for index, group in enumerate(groups)]
  
def rotate_group_with_fixed_blind( group, index):
    # """Rotates the group while keeping the position of a player with playerID == -1 fixed."""
    # Find the index of the player with playerID == -1
    blind_player_index = next((i for i in enumerate(group) if i == -1), None)


    if blind_player_index is not None:
        # Temporarily remove the player with playerID == -1
        blind_player = group.pop(blind_player_index)
    else:
        blind_player = None

    # Rotate the group to the right by 'index' positions
    group = group[-index:] + group[:-index]

    # Reinsert the player with playerID == -1 at its original position if it was removed
    if blind_player is not None:
        group.insert(blind_player_index, blind_player)
        # for player.playerID in 

    return group


def split_players_into_groups(players_ids_arr):
    num_players = len(players_ids_arr)
    num_groups = 4
    group_size = math.ceil(num_players / num_groups)
    remainder = num_players % num_groups
    if remainder>0:
      num_blind_players = num_groups - remainder
    else:
      num_blind_players=0
    # Initialize groups
    player_groups = [[] for _ in range(num_groups)]

    # Current index in the players list
    current_index = 0

    # Fill the first group with 'group_size' players
    player_groups[0] = players_ids_arr[current_index:current_index + group_size]
    current_index += group_size

    # For the remaining groups
    for i in range(1, num_groups):
        size = group_size - 1 if i >= num_groups - num_blind_players else group_size
        player_groups[i] = players_ids_arr[current_index:current_index + size]
        current_index += size
    

    # Print group sizes and compositions for verification
    for i in range(1, num_blind_players + 1):
      if i == 1:  # Special case for the last group
        insert_position = len(player_groups[-i])  # Append to the end
      else:
        insert_position = len(player_groups[-i]) - i+1  # Calculate the correct insert position
      blind_player = -1
      player_groups[-i].insert(insert_position, blind_player)
    return player_groups



def flatten_players_array(single_serie_tische_array):
    flattened_array = []

    for subarray in single_serie_tische_array:
        for value in subarray:
            if value != -1:
                flattened_array.append(value)

    return flattened_array

def create_3er_tische_array(player_array_no_blinds):
    remainder = len(player_array_no_blinds) % 3
    tische_3er_array = []

    if remainder == 1:
        # Get the first 4 elements and put them together in an array
        first_four = player_array_no_blinds[:4]
        tische_3er_array.append(first_four)

        # Get the remaining elements and split them into arrays of three elements each
        remaining_elements = player_array_no_blinds[4:]
        for i in range(0, len(remaining_elements), 3):
            tische_3er_array.append(remaining_elements[i:i+3])

    elif remainder == 2:
        # Get the first 4 elements and put them together in an array
        first_four = player_array_no_blinds[:4]
        tische_3er_array.append(first_four)

        # Get the next 4 elements and put them together in a second array
        next_four = player_array_no_blinds[4:8]
        tische_3er_array.append(next_four)

        # Get the remaining elements and split them into arrays of three elements each
        remaining_elements = player_array_no_blinds[8:]
        for i in range(0, len(remaining_elements), 3):
            tische_3er_array.append(remaining_elements[i:i+3])

    elif remainder == 0:
        # Get all elements and split them into arrays of three elements each
        for i in range(0, len(player_array_no_blinds), 3):
            tische_3er_array.append(player_array_no_blinds[i:i+3])

    return tische_3er_array
