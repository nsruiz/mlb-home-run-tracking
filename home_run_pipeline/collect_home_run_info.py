## The purpose of this script is collect home run information in a format to then be used to update a Blender file

from home_run_pipeline.json_io import load_json

# A dictionary matching MLB teams to the names of colors used within the 3-D world
color_dict = {
    "Arizona Diamondbacks": ["Arizona Diamondbacks Red", "Arizona Diamondbacks Teal"],
    "Atlanta Braves": ["Atlanta Braves Blue", "Atlanta Braves Red"],
    "Baltimore Orioles": ["Baltimore Orioles Orange", "Baltimore Orioles Black"],
    "Boston Red Sox": ["Boston Red Sox Red", "Boston Red Sox Blue"],
    "Chicago Cubs": ["Chicago Cubs Blue", "Chicago Cubs Red"],
    "Chicago White Sox": ["Chicago White Sox Grey", "Chicago White Sox Black"],
    "Cincinnati Reds": ["Cincinnati Reds Red", "Cincinnati Reds Black"],
    "Cleveland Guardians": ["Cleveland Guardians Red", "Cleveland Guardians Blue"],
    "Colorado Rockies": ["Colorado Rockies Purple", "Colorado Rockies Silver"],
    "Detroit Tigers": ["Detroit Tigers Blue", "Detroit Tigers Orange"],
    "Houston Astros": ["Houston Astros Blue", "Houston Astros Orange"],
    "Kansas City Royals": ["Kansas City Royals Blue", "Kansas City Royals Gold"],
    "Los Angeles Angels": ["Los Angeles Angels Red", "Los Angeles Angels Dark Red"],
    "Los Angeles Dodgers": ["Los Angeles Dodger Blue", "Los Angeles Dodgers White"],
    "Miami Marlins": ["Miami Marlins Blue", "Miami Marlins Black"],
    "Milwaukee Brewers": ["Milwaukee Brewers Dark Blue", "Milwaukee Brewers Gold"],
    "Minnesota Twins": ["Minnesota Twins Blue", "Minnesota Twins Red"],
    "New York Mets": ["New York Mets Blue", "New York Mets Orange"],
    "New York Yankees": ["New York Yankees Navy", "New York Yankees Grey"],
    "Athletics": ["Oakland A's Green", "Oakland A's Yellow"],
    "Philadelphia Phillies": ["Philadelphia Phillies Red", "Philadelphia Phillies Blue"],
    "Pittsburgh Pirates": ["Pittsburgh Pirates Yellow", "Pittsburgh Pirates Black"],
    "San Diego Padres": ["San Diego Padres Brown", "San Diego Padres Yellow"],
    "San Francisco Giants": ["San Francisco Giants Orange", "San Francisco Giants Black"],
    "Seattle Mariners": ["Seattle Mariners Blue", "Seattle Mariners Green"],
    "St. Louis Cardinals": ["St Louis Cardinals Red", "St Louis Cardinals Blue"],
    "Tampa Bay Rays": ["Tampa Bay Rays Blue", "Tampa Bay Rays Light Blue"],
    "Texas Rangers": ["Texas Rangers Blue", "Texas Rangers Red"],
    "Toronto Blue Jays": ["Toronto Blue Jays Blue", "Toronto Blue Jays Red"],
    "Washington Nationals": ["Washington Nationals Red", "Washington Nationals Blue"]
}

# There are sometimes discrepancies in the MLB API between a player's full name and their commonly used one.
# This function derives the player's commonly used first and last name.
def extract_preferred_names(person):
    full = person["fullName"]
    last = person["lastName"]

    # Find the index of the last name in the full name (case-insensitive)
    idx = full.lower().find(last.lower())

    if idx == -1:
        # Last name not found — fallback to fullName split
        raise ValueError(f"Last name '{last}' not found in full name '{full}'")

    # Preferred first name is everything before the last name
    preferred_first = full[:idx].strip()

    # Last name + suffixes is everything from the last name on
    preferred_last = full[idx:].strip()

    return preferred_first, preferred_last

# A helper function used to determine whether the hitter in a given play is on the home team
def metric_team_is_home(metric_log) -> bool:
    metric_team_id = metric_log['team']['id']
    home_team_id = metric_log['game']['teams']['home']['team']['id']
    return metric_team_id == home_team_id

# This function loops through the previous day's home runs to get the relevant info for the Blender script.
def process_home_run_data(home_run_data):
    home_run_details = {}
    for idx, home_run in enumerate(home_run_data):
        play_id = home_run['stat']['play']['playId']
        player_id = home_run['batter']['id']
        game_id = home_run['game']['gamePk']

        event_date = home_run.get('date')
        hitter_first_name, hitter_last_name = extract_preferred_names(home_run['player'])

        hitter_team = home_run['team']['name']
        team_color_primary = color_dict[hitter_team][0]
        team_color_secondary = color_dict[hitter_team][1]

        # Collect team info and colors
        hitter_team_id = home_run['team']['id']

        # Typically, team info is collected with an internal async function that makes an API call
        # A static file replaces it here
        team_info = load_json("data/input/team_info.json")
        hitter_team_location = team_info.get(str(hitter_team_id)).get('franchiseName')
        hitter_team_name = team_info.get(str(hitter_team_id)).get('clubName')

        if hitter_team_location == hitter_team_name:  # Handles unique case of Athletics
            hitter_team_location = ""

        # Collect relevant stats
        distance = home_run['stats']['hitting']['tracking'].get('hitDistance', {}).get('value')
        exit_velo = home_run['stats']['hitting']['tracking'].get('exitVelocity', {}).get('value', "NA")
        launch_angle = home_run['stats']['hitting']['tracking'].get('launchAngle', {}).get('value')
        attack_angle = home_run['stats']['hitting']['tracking'].get('attackAngle', {}).get('value', "NA")
        hang_time = home_run['stats']['hitting']['tracking'].get('hangTime', {}).get('value')
        max_height = int(home_run['stats']['hitting']['tracking'].get('maxHeight', {}).get('value', "NA"))
        bat_speed = home_run['stats']['hitting']['tracking'].get('batSpeed', {}).get('value', "NA")

        # Collect needed images and video
        hitter_headshot_url = f'https://img.mlbstatic.com/mlb/images/players/head_shot/{player_id}.jpg'

        # Home run play data is collected with an internal async function that makes an API call
        # Here, it's replaced with a static file.
        play_data_list = load_json("data/input/play_data.json")
        play_data = play_data_list[idx]

        bat_side = home_run['stat']['play']['details']['batSide']['code']

        # This loop determines whether to use the home, away, or national broadcast of the home run
        for idex, feed in enumerate(play_data['video']['playbackGroups']):
            if (metric_team_is_home(home_run) and feed.get('mediaSourceType') == 'BROADCAST'):
                broadcast_idx = idex
                break
            elif not metric_team_is_home(home_run) and 'isAwayFeed' in feed.keys():
                broadcast_idx = idex
                break
            elif feed.get('mediaSourceType') == 'BROADCAST':
                broadcast_idx = idex
                break
        broadcast_url = play_data['video']['playbackGroups'][broadcast_idx]['playbackRenditions'][0]['playbackUrl']

        # This selects the side view from the first-base dugout for a right-handed batter or third-base dugout for a left-handed batter
        for idex, feed in enumerate(play_data['video']['playbackGroups']):
            if feed.get('mediaSourceType') == '1B_BATTER_SIDEVIEW' and bat_side == 'R':
                base_idx = idex
                break
            elif feed.get('mediaSourceType') == '3B_BATTER_SIDEVIEW' and bat_side == 'L':
                base_idx = idex
                break

        sideview_url = play_data['video']['playbackGroups'][base_idx]['playbackRenditions'][0]['playbackUrl']

        # Collects bat tracking info for use in the 3-D world
        bat_head_coordinates = play_data.get('bat', {}).get('batPositions', [{}, {}])[0].get('positions', [])
        contact_time = play_data.get('bat', {}).get('impact', {}).get('timeStamp')
        bat_handle_coordinates = play_data.get('bat', {}).get('batPositions', [{}, {}])[1].get('positions', [])

        # Pull data together to create JSON for Blender
        home_run_details[play_id] = {"Date": event_date,
                                     "Hitter first name": hitter_first_name,
                                     "Hitter last name": hitter_last_name,
                                     "Hitter bat side": bat_side,
                                     "Team": hitter_team,
                                     "Team location": hitter_team_location,
                                     "Team name": hitter_team_name,
                                     "Team primary color": team_color_primary,
                                     "Team secondary color": team_color_secondary,
                                     "Distance": distance,
                                     "Exit velo": exit_velo,
                                     "Launch angle": launch_angle,
                                     "Attack angle": attack_angle,
                                     "Hang time": hang_time,
                                     "Max height": max_height,
                                     "Bat speed": bat_speed,
                                     "Contact time": contact_time,
                                     "Bat head coordinates": bat_head_coordinates,
                                     "Bat handle coordinates": bat_handle_coordinates,
                                     "Hitter headshot": hitter_headshot_url,
                                     "Highlight URL": broadcast_url,
                                     "Sideview URL": sideview_url
                                     }

    # After looping, the file is then traditionally uploaded to AWS S3 cloud infrastructure.
    # For the purposes of the demo, it just creates a local JSON.
    return home_run_details



